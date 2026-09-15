(() => {
  const style = document.createElement('style');
  style.textContent = `
    .addonConnect{margin-top:20px;padding-top:18px;border-top:1px solid rgba(232,207,105,.22)}
    .addonSelect{width:100%;margin:6px 0 12px;padding:10px 11px;border:1px solid rgba(229,198,74,.3);border-radius:8px;background:rgba(13,30,21,.95);color:var(--text)}
    .addonMeta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:0 0 10px}
    .addonMeta .badge{padding:3px 8px}
    .addonDescription{color:var(--muted);font-size:11px;margin:0 0 12px}
    .addonResources{color:#f4d35e;font-size:10px;text-transform:uppercase;letter-spacing:.05em;margin:-4px 0 12px}
    .addonActions{display:flex;gap:8px;flex-wrap:wrap;margin-top:-7px}
    .addonActions a{text-decoration:none;display:inline-block}
    .addonUnavailable{padding:11px 12px;border:1px dashed rgba(232,207,105,.28);border-radius:8px;color:var(--muted);font-size:11px}
  `;
  document.head.appendChild(style);

  const host = document.querySelector('#dashboard .connect > div:first-child');
  if (!host || document.getElementById('addonConnect')) return;

  const box = document.createElement('div');
  box.id = 'addonConnect';
  box.className = 'addonConnect';
  box.innerHTML = `
    <div class="eyebrow">Addons available on this server</div>
    <select id="addonSelect" class="addonSelect">
      <option value="">Select an addon…</option>
    </select>
    <div id="addonDetails" class="addonUnavailable">Loading addons…</div>
  `;
  host.appendChild(box);

  const select = document.getElementById('addonSelect');
  const details = document.getElementById('addonDetails');
  let addons = [];

  function escapeHtml(value) {
    const node = document.createElement('div');
    node.textContent = String(value ?? '');
    return node.innerHTML;
  }

  function escapeAttr(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('"', '&quot;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;');
  }

  function render() {
    const addon = addons.find(item => item.id === select.value);
    if (!addon) {
      details.className = 'addonUnavailable';
      details.textContent = addons.length ? 'Select an addon to show its Stremio installation link.' : 'No addons reported by this server.';
      return;
    }

    const state = addon.ready ? 'Ready' : addon.enabled ? 'HTTPS required' : 'Unavailable';
    const resources = Array.isArray(addon.resources) && addon.resources.length
      ? addon.resources.join(' · ')
      : 'No resources reported';

    if (!addon.manifestUrl) {
      details.className = 'addonUnavailable';
      details.innerHTML = `<strong>${escapeHtml(addon.name)}</strong><br>${escapeHtml(addon.status || state)}`;
      return;
    }

    details.className = '';
    details.innerHTML = `
      <div class="addonMeta">
        <strong>${escapeHtml(addon.name)}</strong>
        <span class="badge">${escapeHtml(state)}</span>
        ${addon.version ? `<small>v${escapeHtml(addon.version)}</small>` : ''}
      </div>
      <div class="addonDescription">${escapeHtml(addon.description || '')}</div>
      <div class="addonResources">${escapeHtml(resources)}</div>
      <div class="eyebrow">Stremio addon manifest</div>
      <div class="field">
        <code id="addonManifestUrl">${escapeHtml(addon.manifestUrl)}</code>
        <button class="copy" data-copy="addonManifestUrl" title="Copy addon URL">⧉</button>
      </div>
      <div class="hint">Copy this URL into Stremio → Addons → Add addon.</div>
      <div class="addonActions">
        ${addon.libraryUrl ? `<a class="mini" href="${escapeAttr(addon.libraryUrl)}" target="_blank" rel="noopener">Open Library</a>` : ''}
      </div>
    `;
  }

  async function loadAddons() {
    details.className = 'addonUnavailable';
    details.textContent = 'Loading addons…';
    try {
      const response = await fetch('/api/addons', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const body = await response.json();
      addons = Array.isArray(body.addons) ? body.addons : [];
      select.innerHTML = '<option value="">Select an addon…</option>' + addons.map(addon => {
        const suffix = addon.enabled ? '' : ' (unavailable)';
        return `<option value="${escapeAttr(addon.id)}">${escapeHtml(addon.name)}${suffix}</option>`;
      }).join('');
      render();
    } catch (error) {
      addons = [];
      select.innerHTML = '<option value="">Select an addon…</option>';
      details.textContent = 'Could not load addon information from WebAdmin.';
    }
  }

  select.addEventListener('change', render);
  loadAddons();
})();
