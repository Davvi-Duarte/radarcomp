from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.domain.models import Opportunity, OpportunityStatus, Priority, ScanEvent
from app.llm.base import LLMProvider
from app.parsers.html_parser import parse_plone_detail
from app.parsers.pdf_parser import extract_pdf_text
from app.repositories.json_repository import JsonRepository
from app.scoring.engine import ScoringEngine
from app.services.classifier import COMPUTING_TERMS, classify
from app.services.dedup import find_duplicate
from app.sources.base import BaseSource
from app.utils.http import HttpClient
from app.utils.text import extract_edital_number, normalize_text, sha256_text, stable_id

logger = logging.getLogger(__name__)


class Scanner:
    def __init__(
        self,
        source: BaseSource,
        repository: JsonRepository,
        scoring: ScoringEngine,
        http: HttpClient | None = None,
        llm: LLMProvider | None = None,
        notifier=None,
        dedup_threshold: float = 0.88,
    ) -> None:
        self.source = source
        self.repository = repository
        self.scoring = scoring
        self.http = http or HttpClient()
        self.llm = llm
        self.notifier = notifier
        self.dedup_threshold = dedup_threshold

    def scan(self) -> dict[str, int]:
        now = datetime.now(timezone.utc)
        opportunities = self.repository.load_opportunities()
        state = self.repository.load_state()
        stats = {"entries": 0, "new": 0, "updated": 0, "skipped": 0, "errors": 0, "gemini_calls": 0}

        for entry in self.source.list_entries():
            stats["entries"] += 1
            try:
                response = self.http.get(entry.url)
                title, description, docs = parse_plone_detail(response.text, entry.url)
                fingerprint_parts = [entry.title, entry.description, title, description]
                fingerprint_parts.extend(
                    f"{d.title}|{d.description}|{d.published_at.isoformat() if d.published_at else ''}|{d.url}"
                    for d in docs
                )
                detail_hash = sha256_text("\n".join(fingerprint_parts))
                previous_hash = state.get("pages", {}).get(entry.url, {}).get("hash")
                if previous_hash == detail_hash:
                    stats["skipped"] += 1
                    continue

                combined = "\n".join(filter(None, [entry.title, entry.description, title, description] + [f"{d.title} {d.description}" for d in docs]))
                classification = classify(combined, "IFPB", entry.source_kind)

                pdf_text = ""
                chosen_pdf = self._choose_primary_pdf(docs)
                # For generic EBTT/TAE pages, inspect the edital PDF to discover the actual area/cargo.
                if (not classification.relevant or classification.confidence < 0.8) and chosen_pdf:
                    try:
                        pdf_resp = self.http.get(chosen_pdf.url)
                        pdf_text = extract_pdf_text(pdf_resp.content)
                        classification = classify(combined + "\n" + pdf_text, "IFPB", entry.source_kind)
                    except Exception as exc:
                        logger.warning("Could not extract PDF %s: %s", chosen_pdf.url, exc)

                if not classification.relevant:
                    state.setdefault("pages", {})[entry.url] = {"hash": detail_hash, "last_checked": now.isoformat()}
                    stats["skipped"] += 1
                    continue

                edital_number = extract_edital_number(title or entry.title)
                oid = stable_id("IFPB", edital_number or title or entry.title, entry.source_kind)
                existing = opportunities.get(oid)
                is_update = existing is not None
                opportunity = existing.model_copy(deep=True) if existing else Opportunity(
                    id=oid,
                    title=title or entry.title,
                    institution="IFPB",
                    source_url=entry.url,
                    official_url=entry.url,
                    edital_url=chosen_pdf.url if chosen_pdf else None,
                    edital_number=edital_number,
                    description=description or entry.description,
                    first_seen_at=now,
                    last_seen_at=now,
                )
                opportunity.title = title or entry.title
                opportunity.description = description or entry.description
                opportunity.plan = classification.plan
                opportunity.priority = classification.priority
                opportunity.opportunity_type = classification.opportunity_type
                opportunity.job_area = classification.job_area
                opportunity.last_seen_at = now
                opportunity.source_hash = detail_hash
                opportunity.edital_url = chosen_pdf.url if chosen_pdf else opportunity.edital_url
                opportunity.edital_number = edital_number or opportunity.edital_number
                opportunity.metadata["source_kind"] = entry.source_kind
                opportunity.metadata["documents"] = [d.model_dump(mode="json") for d in docs]

                llm_text = (pdf_text or combined).strip()
                if self.llm and llm_text and (not existing or previous_hash != detail_hash):
                    try:
                        extracted = self.llm.extract_opportunity(llm_text, {
                            "institution": "IFPB",
                            "source_kind": entry.source_kind,
                            "title": opportunity.title,
                            "edital_number": opportunity.edital_number,
                        })
                        stats["gemini_calls"] += 1
                        self._merge_extraction(opportunity, extracted)
                    except Exception as exc:
                        logger.exception("Gemini failed for %s: %s", entry.url, exc)

                self._set_status(opportunity)
                opportunity = self.scoring.score(opportunity)

                if not existing:
                    dup = find_duplicate(opportunity, list(opportunities.values()), self.dedup_threshold)
                    if dup:
                        opportunity.id = dup.id
                        opportunity.first_seen_at = dup.first_seen_at
                        existing = dup
                        is_update = True

                should_notify = self.notifier and opportunity.priority in {Priority.P0, Priority.P1} and opportunity.last_notified_hash != detail_hash
                if should_notify:
                    try:
                        self.notifier.send_opportunity(opportunity, is_update=bool(existing))
                        opportunity.last_notified_hash = detail_hash
                        self.repository.append_event(ScanEvent(timestamp=now, event="NOTIFIED", opportunity_id=opportunity.id, source=entry.source_name))
                    except Exception as exc:
                        logger.exception("Notification failed for %s: %s", opportunity.id, exc)

                opportunities[opportunity.id] = opportunity
                state.setdefault("pages", {})[entry.url] = {"hash": detail_hash, "last_checked": now.isoformat()}
                self.repository.append_event(ScanEvent(
                    timestamp=now,
                    event="UPDATED" if is_update else "NEW",
                    opportunity_id=opportunity.id,
                    source=entry.source_name,
                    details={"url": entry.url, "priority": str(opportunity.priority), "score": opportunity.total_score},
                ))
                stats["updated" if is_update else "new"] += 1
            except Exception as exc:
                stats["errors"] += 1
                logger.exception("Failed processing %s: %s", entry.url, exc)

        self.repository.save_opportunities(opportunities)
        self.repository.save_state(state)
        return stats

    @staticmethod
    def _choose_primary_pdf(docs):
        pdfs = [d for d in docs if d.is_pdf]
        if not pdfs:
            return None
        preferred = [d for d in pdfs if "retific" in normalize_text(d.title) and "resultado" not in normalize_text(d.title)]
        if preferred:
            return sorted(preferred, key=lambda d: d.published_at or datetime.min)[-1]
        edital_docs = [d for d in pdfs if "edital" in normalize_text(d.title) and "resultado" not in normalize_text(d.title)]
        if edital_docs:
            return edital_docs[0]
        return pdfs[0]

    @staticmethod
    def _merge_extraction(o: Opportunity, e) -> None:
        for field in [
            "job_area", "campus", "city", "state", "number_of_positions", "salary", "workload",
            "registration_start", "registration_end", "minimum_degree",
        ]:
            value = getattr(e, field)
            if value is not None:
                setattr(o, field, value)
        if e.accepted_degrees:
            o.accepted_degrees = e.accepted_degrees
        if e.requirements:
            o.requirements = e.requirements
        if e.technologies:
            o.technologies = e.technologies
        if e.summary:
            o.description = e.summary
        o.metadata["llm_confidence"] = e.confidence

    @staticmethod
    def _set_status(o: Opportunity) -> None:
        from datetime import date
        if o.registration_end:
            o.status = OpportunityStatus.CLOSED if o.registration_end < date.today() else OpportunityStatus.OPEN
        elif o.status == OpportunityStatus.NEW:
            o.status = OpportunityStatus.WATCHING
