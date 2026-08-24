const state = { items: [], filter: 'all', query: '' };

const esc = (value='') => String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const dateBR = value => value ? new Intl.DateTimeFormat('pt-BR').format(new Date(`${value}T12:00:00`)) : 'não informado';
const dateTimeBR = value => value ? new Intl.DateTimeFormat('pt-BR', {dateStyle:'short', timeStyle:'short'}).format(new Date(value)) : 'nenhuma oportunidade detectada ainda';
const safeUrl = value => { try { const u = new URL(value); return ['http:','https:'].includes(u.protocol) ? u.href : '#'; } catch { return '#'; } };

function matches(item) {
  const f = state.filter;
  const filterOk = f === 'all' || item.plan === f || item.priority === f || item.status === f;
  const haystack = [item.title,item.institution,item.job_area,item.city,item.campus,item.description,item.edital_number].join(' ').toLowerCase();
  return filterOk && haystack.includes(state.query.toLowerCase());
}

function card(item) {
  const reasons = (item.score_explanation || []).slice(0,4).map(r => `<li>${esc(r)}</li>`).join('');
  return `<article class="card" data-priority="${esc(item.priority)}">
    <div class="card-top">
      <div>
        <div class="badges">
          <span class="badge priority-${esc(item.priority)}">${esc(item.priority)}</span>
          <span class="badge">Plano ${esc(item.plan)}</span>
          <span class="badge">${esc(item.status)}</span>
        </div>
        <h2>${esc(item.title)}</h2>
        <div class="institution">${esc(item.institution)}${item.campus ? ` · ${esc(item.campus)}` : ''}</div>
      </div>
      <div class="score"><strong>${Number(item.total_score || 0).toFixed(0)}</strong><span>score</span></div>
    </div>
    <div class="meta">
      <div>🧭 ${esc(item.job_area || 'Área a confirmar')}</div>
      <div>📍 ${esc(item.city || item.state || 'Local a confirmar')}</div>
      <div>📅 Prazo: ${dateBR(item.registration_end)}</div>
      <div>📄 Edital: ${esc(item.edital_number || '—')}</div>
    </div>
    ${item.description ? `<p class="description">${esc(item.description)}</p>` : ''}
    ${reasons ? `<ul class="reasons">${reasons}</ul>` : ''}
    <a class="button" href="${esc(safeUrl(item.official_url))}" rel="noopener noreferrer" target="_blank">Ver fonte oficial ↗</a>
  </article>`;
}

function render() {
  const visible = state.items.filter(matches);
  document.querySelector('#opportunities').innerHTML = visible.map(card).join('');
  document.querySelector('#empty').classList.toggle('hidden', visible.length !== 0);
}

async function init() {
  try {
    const response = await fetch('data/opportunities.json', {cache:'no-store'});
    const data = await response.json();
    state.items = data.opportunities || [];
    document.querySelector('#last-update').textContent = `Última atualização: ${dateTimeBR(data.generated_at)}`;
    document.querySelector('#count-a').textContent = state.items.filter(x => x.plan === 'A').length;
    document.querySelector('#count-b').textContent = state.items.filter(x => x.plan === 'B').length;
    document.querySelector('#count-c').textContent = state.items.filter(x => x.plan === 'C').length;
    document.querySelector('#count-total').textContent = state.items.length;
    render();
  } catch (error) {
    document.querySelector('#last-update').textContent = 'Falha ao carregar dados do RadarComp.';
    console.error(error);
  }
}

document.querySelector('#filters').addEventListener('click', event => {
  const button = event.target.closest('button[data-filter]');
  if (!button) return;
  document.querySelectorAll('.filter').forEach(b => b.classList.remove('active'));
  button.classList.add('active');
  state.filter = button.dataset.filter;
  render();
});

document.querySelector('#search').addEventListener('input', event => {
  state.query = event.target.value;
  render();
});

init();
