/* Functional Phase 02 controls. All external/private strings are text, never markup. */
(() => {
  const el = id => document.getElementById(id), api = () => window.pywebview.api;
  const panel = el('intelligencePanel');
  let settings, records = [], proposals = [];
  const value = id => el(id).value, checked = id => el(id).checked;
  const notice = text => { el('intelligenceNotice').textContent = text; };
  const option = (select, text, id) => { const o = document.createElement('option'); o.textContent = text; o.value = id; select.append(o); };
  const list = text => text.split(',').map(v => v.trim()).filter(Boolean);
  const number = id => value(id).trim() === '' ? null : Number(value(id));
  function provider() {
    const p = settings.providers.find(p => p.id === value('providerId'));
    for (const field of ['enabled', 'allow_paid', 'stream', 'local_only_confirmed']) el('p_' + field).checked = p[field];
    for (const field of ['model', 'endpoint', 'upstream', 'timeout', 'max_request_bytes', 'max_response_bytes', 'max_output_tokens',
      'retries', 'max_request_cost', 'input_price_per_million', 'output_price_per_million', 'api_version', 'workspace_id', 'token_parameter']) {
      el('p_' + field).value = p[field] ?? '';
    }
    el('p_task_types').value = p.task_types.join(',');
    el('p_stream').disabled = !p.capabilities.streaming;
    el('providerStatus').textContent = p.status;
    el('providerKey').value = '';
    el('removeKey').checked = false;
    el('providerKey').disabled = !p.requires_key;
    el('removeKey').disabled = !p.requires_key;
  }
  async function refresh() {
    const data = await api().intelligence_settings();
    if (data.busy) { notice('Wait for the current task to finish.'); return; }
    settings = data;
    const chosen = value('providerId');
    el('providerId').replaceChildren(); el('routingSelected').replaceChildren();
    data.providers.forEach(p => { option(el('providerId'), p.id, p.id); option(el('routingSelected'), p.id, p.id); });
    if (data.providers.some(p => p.id === chosen)) el('providerId').value = chosen;
    provider();
    el('routingSelected').value = data.routing.selected;
    el('routingProfile').value = data.routing.profile;
    for (const k of ['automatic', 'privacy', 'offline']) el('r_' + k).checked = data.routing[k];
    for (const k of ['fast', 'balanced', 'advanced', 'offline_order', 'fallbacks']) el('r_' + k).value = data.routing[k].join(',');
    el('sessionState').textContent = `${data.current.title} · ${data.current.temporary ? 'Temporary — nothing saved' : data.current.status + ' · encrypted locally'}`;
    el('policyCeiling').textContent = data.privacy_ceiling || !data.cloud_allowed ? 'Application configuration blocks cloud requests.' : 'Cloud requests require provider policy and data review.';
    await histories(); await memories();
  }
  async function histories() {
    const rows = await api().conversations(value('historyQuery'));
    el('historyList').replaceChildren();
    rows.forEach(r => option(el('historyList'), `${r.title} · ${r.status} · ${r.updated_at}`, r.id));
  }
  async function memories() {
    const data = await api().memories();
    if (data.busy) return;
    records = data.records; proposals = data.proposals;
    el('memoryList').replaceChildren(); el('proposalList').replaceChildren();
    records.forEach(r => option(el('memoryList'), `[${r.category}] ${r.value.slice(0, 100)}`, r.id));
    proposals.forEach(r => option(el('proposalList'), `[${r.category}] ${r.value}`, r.id));
    el('memoryEnabled').checked = data.policy.enabled;
    el('memoryAutomatic').checked = data.policy.automatic;
    document.querySelectorAll('[data-memory-category]').forEach(c => { c.checked = data.policy.categories.includes(c.value); });
    memory();
  }
  function memory() {
    const r = records.find(r => r.id === value('memoryList'));
    if (!r) { el('memoryProvenance').textContent = 'No selected memory.'; return; }
    el('memoryValue').value = r.value; el('memoryCategory').value = r.category; el('memoryLocal').checked = r.local_only;
    el('memoryProvenance').textContent = `${r.origin} · user confirmed: ${r.confirmed} · ${r.source_kind} · created ${r.created_at} · updated ${r.updated_at} · revision ${r.revision}`;
  }
  async function queued(result) {
    if (await result) { panel.close(); notice('Action queued. Review the exact change in the approval dialog.'); }
    else notice('Wait for the current task to finish.');
  }
  const bind = (id, fn) => el(id).addEventListener('click', async () => {
    try { await fn(); } catch (_) { notice('Could not apply this request. Check the values and configured permissions.'); }
  });
  bind('intelligenceOpen', async () => { await refresh(); if (!panel.open) panel.showModal(); });
  bind('intelligenceRefresh', refresh);
  el('providerId').addEventListener('change', provider);
  bind('providerSave', async () => {
    const v = {};
    for (const k of ['enabled', 'allow_paid', 'stream', 'local_only_confirmed']) v[k] = checked('p_' + k);
    for (const k of ['model', 'endpoint', 'upstream', 'api_version', 'workspace_id', 'token_parameter']) v[k] = value('p_' + k).trim();
    for (const k of ['timeout', 'max_request_bytes', 'max_response_bytes', 'max_output_tokens', 'retries',
      'max_request_cost', 'input_price_per_million', 'output_price_per_million']) v[k] = number('p_' + k);
    v.task_types = list(value('p_task_types'));
    const secret = value('providerKey') || null;
    el('providerKey').value = '';
    await queued(api().configure_provider(value('providerId'), v, secret, checked('removeKey')));
  });
  bind('providerCheck', () => queued(api().check_provider(value('providerId'))));
  bind('routingSave', () => {
    const v = {selected: value('routingSelected'), profile: value('routingProfile')};
    for (const k of ['automatic', 'privacy', 'offline']) v[k] = checked('r_' + k);
    for (const k of ['fast', 'balanced', 'advanced', 'offline_order', 'fallbacks']) v[k] = list(value('r_' + k));
    return queued(api().configure_routing(v));
  });
  bind('historySearch', histories);
  bind('historyResume', () => queued(api().resume_conversation(value('historyList'))));
  for (const [id, operation] of [['historyRename', 'rename'], ['historyArchive', 'archive'], ['historyUnarchive', 'unarchive'], ['historyDelete', 'delete']]) {
    bind(id, () => queued(api().conversation_action({operation, id: value('historyList'), title: value('conversationTitle')})));
  }
  bind('historyTemporary', () => queued(api().conversation_action({operation: 'new', title: value('conversationTitle') || 'Temporary conversation', persistent: false})));
  bind('historyPersistent', () => queued(api().conversation_action({operation: 'new', title: value('conversationTitle'), persistent: true})));
  bind('historyRetention', () => queued(api().conversation_action({operation: 'retention', days: Number(value('retentionDays'))})));
  bind('historyExport', async () => { el('conversationExport').value = await api().export_conversation(value('historyList') || null); });
  el('memoryList').addEventListener('change', memory);
  bind('memoryAdd', () => queued(api().memory_action({operation: 'add', category: value('memoryCategory'), value: value('memoryValue'), local_only: checked('memoryLocal')})));
  bind('memoryUpdate', () => {
    const r = records.find(r => r.id === value('memoryList'));
    return queued(api().memory_action({operation: 'update', id: r.id, revision: r.revision, value: value('memoryValue'), local_only: checked('memoryLocal')}));
  });
  bind('memoryDelete', () => queued(api().memory_action({operation: 'delete', id: value('memoryList')})));
  bind('memoryPolicy', () => queued(api().configure_memory({enabled: checked('memoryEnabled'), automatic: checked('memoryAutomatic'),
    categories: [...document.querySelectorAll('[data-memory-category]:checked')].map(c => c.value)})));
  bind('proposalAccept', () => queued(api().memory_action({operation: 'accept', id: value('proposalList'), local_only: true})));
  bind('proposalDismiss', () => queued(api().memory_action({operation: 'dismiss', id: value('proposalList')})));
  window.addEventListener('clydex-intelligence', async event => {
    for (const [kind, data] of event.detail) {
      if (kind === 'provider_state') el('intelligenceTelemetry').textContent = `${data.provider} / ${data.model || 'CLI default'} · ${data.status}`;
      if (kind === 'provider_delta') el('intelligenceTelemetry').textContent = `Receiving response · ${data.received_characters} characters (validation pending)`;
      if (kind === 'memory_suggestion') el('intelligenceTelemetry').textContent = 'Memory suggestion awaiting review in AI & Memory.';
      if (kind === 'history_state') el('intelligenceTelemetry').textContent = data.saved ? (data.temporary ? 'Temporary conversation' : 'Saved locally') : 'Sensitive turn omitted from history';
      if (kind === 'intelligence_result') {
        if (data.clear || data.transcript) window.dispatchEvent(new CustomEvent('clydex-transcript', {detail: data.transcript || []}));
        if (data.connection_status) notice(data.connection_status);
        if (panel.open && data.refresh) await refresh();
      }
    }
  });
})();
