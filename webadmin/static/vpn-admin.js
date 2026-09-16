(() => {
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const fmtBytes = value => {
    const n = Number(value || 0);
    if (!n) return '0 B';
    const units = ['B','KB','MB','GB','TB'];
    const i = Math.min(units.length - 1, Math.floor(Math.log(n) / Math.log(1024)));
    return `${(n / (1024 ** i)).toFixed(i > 1 ? 1 : 0)} ${units[i]}`;
  };
  const badge = (ok, text) => `<span class="badge ${ok ? '' : 'vpnBad'}">● ${esc(text)}</span>`;

  const css = document.createElement('style');
  css.textContent = `
    .vpnBad{color:#ff8d95!important;border-color:#8b3341!important;background:#40161d!important}
    .vpnGrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:16px}
    .vpnCard{padding:14px;border:1px solid rgba(232,207,105,.25);border-radius:10px;background:rgba(13,30,21,.95);min-width:0}
    .vpnCard span{display:block;color:var(--muted);font-size:10px;text-transform:uppercase}.vpnCard b{display:block;margin-top:5px;font-size:15px;overflow-wrap:anywhere}
    .vpnForm{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.vpnField{min-width:0}.vpnField.full{grid-column:1/-1}
    .vpnField label{display:block;color:#e6cf68;font-size:11px;margin-bottom:5px}.vpnField input,.vpnField select,.vpnField textarea{width:100%;border:1px solid rgba(229,198,74,.3);border-radius:8px;background:rgba(13,30,21,.95);color:var(--text);padding:10px;font:inherit}.vpnField textarea{min-height:120px;font:11px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace;resize:vertical}
    .vpnSecretState{color:var(--muted);font-size:10px;margin-top:4px}.vpnActions{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.vpnInfo{padding:12px;border:1px solid rgba(232,207,105,.2);border-radius:9px;background:rgba(15,24,18,.92);color:var(--muted);font-size:12px;margin:10px 0}.vpnResult{white-space:pre-wrap;font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace}.vpnLogs{min-height:240px;max-height:420px;overflow:auto;padding:14px;border:1px solid #827632;border-radius:9px;background:rgba(2,8,5,.96);color:#cdd4d8;font:11px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
    @media(max-width:900px){.vpnGrid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:650px){.vpnGrid,.vpnForm{grid-template-columns:1fr}.vpnField.full{grid-column:auto}}
  `;
  document.head.appendChild(css);

  const nav = document.querySelector('.tabs');
  if (!nav || $('vpn')) return;
  const logsTab = [...nav.querySelectorAll('.tab')].find(btn => btn.dataset.page === 'logs');
  const tab = document.createElement('button');
  tab.className = 'tab';
  tab.dataset.page = 'vpn';
  tab.textContent = 'VPN';
  nav.insertBefore(tab, logsTab || null);

  const section = document.createElement('section');
  section.className = 'page hidden';
  section.id = 'vpn';
  section.innerHTML = `
    <article class="panel"><div class="title row"><span>VPN · CYBERGHOST / GLUETUN</span><button class="copy" id="vpnRefresh">↻ Refresh</button></div><div class="inner">
      <div class="vpnGrid">
        <div class="vpnCard"><span>Deployment</span><b id="vpnMode">—</b></div>
        <div class="vpnCard"><span>Tunnel</span><b id="vpnTunnel">—</b></div>
        <div class="vpnCard"><span>VPN public IP</span><b id="vpnPublicIp">—</b></div>
        <div class="vpnCard"><span>Kill switch</span><b id="vpnKill">—</b></div>
        <div class="vpnCard"><span>Provider</span><b id="vpnProvider">—</b></div>
        <div class="vpnCard"><span>Protocol</span><b id="vpnProtocolStatus">—</b></div>
        <div class="vpnCard"><span>Received</span><b id="vpnRx">—</b></div>
        <div class="vpnCard"><span>Sent</span><b id="vpnTx">—</b></div>
      </div>
      <div id="vpnModeHint" class="vpnInfo"></div>
      <div class="vpnActions">
        <button class="btn" id="vpnConnect">Connect</button>
        <button class="btn danger" id="vpnDisconnect">Disconnect (block traffic)</button>
        <button class="btn ghost" id="vpnReconnect">Reconnect</button>
        <button class="btn ghost" id="vpnTest">Test protection</button>
      </div>
      <div id="vpnActionState" class="saveState"></div>
      <div id="vpnTestResult" class="vpnInfo vpnResult">Protection test has not been run yet.</div>
    </div><div class="foot">Only the Stremio runtime is routed through the VPN. WebAdmin and Pi-hole remain directly reachable on the LAN.</div></article>

    <article class="panel"><div class="title">CYBERGHOST OPENVPN CONFIGURATION</div><div class="inner">
      <div class="vpnInfo"><b>Use the generated CyberGhost OpenVPN credentials and certificate files, not your normal account password.</b> Saved secrets are stored in the private <code>vpn-data</code> Docker volume and are never returned to this page.</div>
      <div class="vpnForm">
        <div class="vpnField"><label>Provider</label><input id="vpnProviderCfg" value="cyberghost" disabled></div>
        <div class="vpnField"><label>Protocol</label><select id="vpnProtocol"><option value="udp">OpenVPN UDP (recommended)</option><option value="tcp">OpenVPN TCP</option></select></div>
        <div class="vpnField"><label>Country (optional)</label><input id="vpnCountry" placeholder="e.g. Netherlands"></div>
        <div class="vpnField"><label>Server hostname (optional; leave blank for provider selection)</label><input id="vpnHostname" placeholder="Optional CyberGhost hostname"></div>
        <div class="vpnField full"><label>LAN CIDRs allowed outside the VPN</label><input id="vpnCidrs" value="192.168.0.0/16,10.0.0.0/8,172.30.0.0/24"></div>
        <div class="vpnField"><label>Generated OpenVPN username</label><input id="vpnUser" autocomplete="off" placeholder="Leave blank to keep saved value"><div class="vpnSecretState" id="vpnUserState"></div></div>
        <div class="vpnField"><label>Generated OpenVPN password</label><input id="vpnPass" type="password" autocomplete="new-password" placeholder="Leave blank to keep saved value"><div class="vpnSecretState" id="vpnPassState"></div></div>
        <div class="vpnField full"><label>client.crt (PEM)</label><textarea id="vpnCert" placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----"></textarea><div class="vpnSecretState" id="vpnCertState"></div></div>
        <div class="vpnField full"><label>client.key (PEM)</label><textarea id="vpnKey" placeholder="-----BEGIN PRIVATE KEY-----&#10;...&#10;-----END PRIVATE KEY-----"></textarea><div class="vpnSecretState" id="vpnKeyState"></div></div>
      </div>
      <div class="vpnActions"><button class="btn" id="vpnSave">Save</button><button class="btn" id="vpnSaveApply">Save & Apply</button><button class="btn danger" id="vpnClearSecrets">Clear saved secrets</button></div>
      <div id="vpnSaveState" class="saveState"></div>
      <div class="vpnInfo">CyberGhost does not provide VPN-side port forwarding. Outbound P2P remains available, but inbound peers cannot reach the Stremio BitTorrent port through the CyberGhost address.</div>
    </div><div class="foot">Configuration changes take effect after applying/restarting Gluetun. Stremio remains fail-closed behind the VPN namespace.</div></article>

    <article class="panel"><div class="title row"><span>VPN LOGS</span><button class="copy" id="vpnLogsRefresh">↻ Refresh</button></div><div class="inner"><pre class="vpnLogs" id="vpnLogs">VPN logs not loaded.</pre></div><div class="foot">Recent Gluetun output. Stored username/password values are redacted before being returned by WebAdmin.</div></article>
  `;
  document.querySelector('main.shell').appendChild(section);

  let loadedConfig = false;

  function setAction(text, bad = false) {
    $('vpnActionState').textContent = text || '';
    $('vpnActionState').style.color = bad ? 'var(--danger)' : '';
  }
  function setSave(text, bad = false) {
    $('vpnSaveState').textContent = text || '';
    $('vpnSaveState').style.color = bad ? 'var(--danger)' : '';
  }
  async function api(path, opts = {}) {
    const response = await fetch(path, {cache:'no-store', ...opts});
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail || body.message || `HTTP ${response.status}`);
    return body;
  }

  function secretState(id, configured) {
    $(id).textContent = configured ? '✓ Saved (value hidden)' : 'Not configured';
    $(id).style.color = configured ? 'var(--green)' : '';
  }

  function renderStatus(data) {
    const g = data.gluetun || {}, routing = data.routing || {}, runtime = data.runtime || {}, cfg = data.config || {};
    $('vpnMode').innerHTML = data.deploymentMode === 'vpn' ? badge(true, 'VPN') : badge(false, 'Direct');
    const running = g.vpnStatus === 'running';
    $('vpnTunnel').innerHTML = badge(running, g.vpnStatus || (g.present ? 'starting' : 'not deployed'));
    $('vpnPublicIp').textContent = g.publicIp || '—';
    $('vpnKill').innerHTML = badge(!!routing.killSwitchActive, routing.killSwitchActive ? 'Active' : 'Not verified');
    $('vpnProvider').textContent = runtime.provider || cfg.provider || 'CyberGhost';
    $('vpnProtocolStatus').textContent = String(runtime.protocol || cfg.protocol || 'udp').toUpperCase();
    $('vpnRx').textContent = fmtBytes(g.rxBytes);
    $('vpnTx').textContent = fmtBytes(g.txBytes);

    if (data.deploymentMode !== 'vpn') {
      $('vpnModeHint').innerHTML = '<b>Direct mode is active.</b> Save your CyberGhost material here, then run <code>sh start-vpn.sh</code> on the Docker host to move Stremio behind Gluetun.';
    } else if (!g.controlAvailable) {
      $('vpnModeHint').innerHTML = `<b>VPN stack detected, control API not ready.</b> ${esc(g.controlError || 'Gluetun may still be starting or waiting for valid credentials.')}`;
    } else {
      $('vpnModeHint').innerHTML = `<b>VPN mode is active.</b> Stremio shares the Gluetun network namespace; WebAdmin stays on the LAN. ${esc((data.limitations || {}).disconnectBehaviour || '')}`;
    }

    if (!loadedConfig) {
      $('vpnProtocol').value = cfg.protocol || 'udp';
      $('vpnCountry').value = cfg.country || '';
      $('vpnHostname').value = cfg.hostname || '';
      $('vpnCidrs').value = cfg.firewall_outbound_subnets || '192.168.0.0/16,10.0.0.0/8,172.30.0.0/24';
      loadedConfig = true;
    }
    const creds = cfg.credentials || {};
    secretState('vpnUserState', creds.username);
    secretState('vpnPassState', creds.password);
    secretState('vpnCertState', creds.clientCert);
    secretState('vpnKeyState', creds.clientKey);

    const controllable = !!g.controlAvailable && data.deploymentMode === 'vpn';
    $('vpnConnect').disabled = !controllable || running;
    $('vpnDisconnect').disabled = !controllable || !running;
    $('vpnReconnect').disabled = !controllable;
  }

  async function loadStatus() {
    try { renderStatus(await api('/api/vpn/status')); }
    catch (error) { setAction(`Status error: ${error.message}`, true); }
  }

  async function loadLogs() {
    try {
      const data = await api('/api/vpn/logs?lines=250');
      $('vpnLogs').textContent = data.available ? (data.lines || []).join('\n') || 'No VPN log lines yet.' : 'Gluetun container is not running.';
      $('vpnLogs').scrollTop = $('vpnLogs').scrollHeight;
    } catch (error) { $('vpnLogs').textContent = `Could not load VPN logs: ${error.message}`; }
  }

  function configBody(clear = false) {
    return {
      provider: 'cyberghost',
      protocol: $('vpnProtocol').value,
      country: $('vpnCountry').value.trim(),
      hostname: $('vpnHostname').value.trim(),
      firewall_outbound_subnets: $('vpnCidrs').value.trim(),
      username: $('vpnUser').value || null,
      password: $('vpnPass').value || null,
      client_cert: $('vpnCert').value || null,
      client_key: $('vpnKey').value || null,
      clear_credentials: clear,
    };
  }

  function clearSecretInputs() {
    $('vpnUser').value = '';
    $('vpnPass').value = '';
    $('vpnCert').value = '';
    $('vpnKey').value = '';
  }

  async function saveConfig(apply = false, clear = false) {
    setSave(clear ? 'Clearing secrets…' : 'Saving…');
    try {
      await api('/api/vpn/config', {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(configBody(clear))});
      clearSecretInputs();
      loadedConfig = false;
      setSave(clear ? 'Saved secrets cleared.' : 'Configuration saved.');
      await loadStatus();
      if (apply) {
        setSave('Applying configuration…');
        const result = await api('/api/vpn/apply', {method:'POST'});
        setSave(result.message || 'Configuration applied.');
        await loadStatus(); await loadLogs();
      }
    } catch (error) { setSave(error.message, true); }
  }

  async function action(path, label) {
    setAction(`${label}…`);
    try {
      const data = await api(path, {method:'POST'});
      setAction(data.message || `${label} requested.`);
      await loadStatus(); await loadLogs();
    } catch (error) { setAction(error.message, true); }
  }

  async function testProtection() {
    $('vpnTestResult').textContent = 'Running protection test…';
    try {
      const d = await api('/api/vpn/test', {method:'POST'});
      $('vpnTestResult').textContent = [
        `Result: ${d.result}`,
        `Protected: ${d.protected ? 'YES' : 'NO / NOT PROVEN'}`,
        `Host WAN IP: ${d.hostPublicIp || 'unavailable'}`,
        `VPN public IP: ${d.vpnPublicIp || 'unavailable'}`,
        `Stremio public IP: ${d.stremioPublicIp || 'blocked/unavailable'}`,
        `Stremio routed through VPN: ${d.stremioThroughVpn ? 'yes' : 'no'}`,
        `Kill switch active: ${d.killSwitchActive ? 'yes' : 'no'}`,
        `Kill switch verified while stopped: ${d.killSwitchVerified == null ? 'not tested' : d.killSwitchVerified ? 'yes' : 'no'}`,
        '', d.reason || ''
      ].join('\n');
    } catch (error) { $('vpnTestResult').textContent = `Protection test failed: ${error.message}`; }
  }

  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(item => item.classList.toggle('active', item === tab));
    document.querySelectorAll('.page').forEach(page => page.classList.add('hidden'));
    section.classList.remove('hidden');
    loadStatus();
    loadLogs();
  });
  $('vpnRefresh').onclick = loadStatus;
  $('vpnLogsRefresh').onclick = loadLogs;
  $('vpnConnect').onclick = () => action('/api/vpn/connect', 'Connecting');
  $('vpnDisconnect').onclick = () => {
    if (confirm('Disconnect the VPN? Stremio Internet traffic will be BLOCKED by the kill switch until you reconnect.')) action('/api/vpn/disconnect', 'Disconnecting');
  };
  $('vpnReconnect').onclick = () => action('/api/vpn/reconnect', 'Reconnecting');
  $('vpnTest').onclick = testProtection;
  $('vpnSave').onclick = () => saveConfig(false, false);
  $('vpnSaveApply').onclick = () => saveConfig(true, false);
  $('vpnClearSecrets').onclick = () => { if (confirm('Delete the saved CyberGhost username, password, client certificate and private key?')) saveConfig(false, true); };

  loadStatus();
})();
