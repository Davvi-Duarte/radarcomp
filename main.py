from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from app.config.loader import load_yaml
from app.llm.gemini import GeminiProvider
from app.notifications.telegram import TelegramNotificationProvider
from app.repositories.json_repository import JsonRepository
from app.scoring.engine import ScoringEngine
from app.services.site_builder import build_site_data
from app.services.scanner import Scanner
from app.sources.ifpb import IFPBSource


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def make_components():
    profile = load_yaml("config/profile.yaml")
    scoring_cfg = load_yaml("config/scoring.yaml")
    sources_cfg = load_yaml("config/sources.yaml")
    repo = JsonRepository("data")
    source = IFPBSource(sources_cfg["ifpb"])
    scoring = ScoringEngine(scoring_cfg, profile)

    llm = None
    if os.getenv("GEMINI_API_KEY"):
        try:
            llm = GeminiProvider()
        except Exception as exc:
            logging.getLogger(__name__).warning("Gemini disabled: %s", exc)

    notifier = None
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        try:
            notifier = TelegramNotificationProvider()
        except Exception as exc:
            logging.getLogger(__name__).warning("Telegram disabled: %s", exc)
    return repo, source, scoring, llm, notifier, profile


def cmd_scan(args) -> int:
    repo, source, scoring, llm, notifier, profile = make_components()
    threshold = float(load_yaml("config/scoring.yaml").get("dedup_threshold", 0.88))
    stats = Scanner(source, repo, scoring, llm=llm, notifier=notifier, dedup_threshold=threshold).scan()
    build_site_data(repo.load_opportunities())
    logging.getLogger(__name__).info("Scan stats: %s", stats)
    return 0 if stats["errors"] == 0 else 2


def cmd_list(args) -> int:
    repo = JsonRepository("data")
    items = list(repo.load_opportunities().values())
    if args.plan:
        items = [x for x in items if str(x.plan) == args.plan]
    if args.priority:
        items = [x for x in items if str(x.priority) == args.priority]
    items.sort(key=lambda x: (-x.total_score, x.title))
    for o in items:
        print(f"{o.id}  {o.priority}/{o.plan}  {o.total_score:>6g}  {o.title}")
    return 0


def cmd_show(args) -> int:
    repo = JsonRepository("data")
    item = repo.load_opportunities().get(args.id)
    if not item:
        print("Opportunity not found")
        return 1
    print(item.model_dump_json(indent=2))
    return 0


def cmd_build_site(args) -> int:
    repo = JsonRepository("data")
    build_site_data(repo.load_opportunities())
    return 0


def cmd_test_telegram(args) -> int:
    provider = TelegramNotificationProvider()
    import requests
    response = requests.post(
        f"https://api.telegram.org/bot{provider.token}/sendMessage",
        json={"chat_id": provider.chat_id, "text": "✅ RadarComp: integração com Telegram funcionando."},
        timeout=20,
    )
    response.raise_for_status()
    print("Mensagem de teste enviada.")
    return 0


def cmd_source_status(args) -> int:
    repo = JsonRepository("data")
    import json
    print(json.dumps(repo.load_state(), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="radarcomp")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Scan configured sources")
    p_scan.set_defaults(func=cmd_scan)

    p_list = sub.add_parser("list", help="List opportunities")
    p_list.add_argument("--plan", choices=["A", "B", "C", "OTHER"])
    p_list.add_argument("--priority", choices=["P0", "P1", "P2", "P3"])
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show one opportunity")
    p_show.add_argument("id")
    p_show.set_defaults(func=cmd_show)

    p_site = sub.add_parser("build-site", help="Generate public site data")
    p_site.set_defaults(func=cmd_build_site)

    p_tg = sub.add_parser("test-telegram", help="Send a Telegram test message")
    p_tg.set_defaults(func=cmd_test_telegram)

    p_status = sub.add_parser("source-status", help="Show source state")
    p_status.set_defaults(func=cmd_source_status)
    return parser


def main() -> int:
    load_dotenv()
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
