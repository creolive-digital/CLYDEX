/* Functional voice controls; no private string becomes HTML or an instruction. */
(() => {
  const el = id => document.getElementById(id), api = () => window.pywebview.api;
  const panel = el('voicePanel'), notice = text => {
    el('voiceNotice').textContent = text;
    el('voiceStatusMessage').textContent = text;
  };
  const flags = ['microphone_enabled', 'background_listening', 'continuous', 'wake_enabled', 'hotkey_enabled', 'tray_enabled'];
  const textFields = ['mode', 'recognition_language', 'fast_model', 'accurate_model', 'tts_provider', 'voice_id',
    'tts_language', 'tts_fallback', 'piper_manifest', 'wake_manifest', 'hotkey'];
  const numbers = ['max_recording_seconds', 'initial_silence_seconds', 'silence_ms', 'min_speech_ms', 'followup_seconds',
    'inactivity_seconds', 'playback_cooldown_ms', 'noise_floor', 'noise_ratio', 'min_avg_logprob', 'max_no_speech',
    'min_language_probability', 'speech_rate', 'volume', 'wake_threshold'];
  const option = (target, label, value) => { const o = document.createElement('option'); o.value = value; o.textContent = label; target.append(o); };
  const models = ['tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en', 'medium', 'medium.en', 'large-v1', 'large-v2', 'large-v3', 'large-v3-turbo', 'turbo'];
  for (const id of ['v_fast_model', 'v_accurate_model']) models.forEach(m => option(el(id), m, m));
  async function refresh() {
    const data = await api().voice_settings();
    if (data.busy || data.locked) { notice('Unlock the desktop and wait for the current task to finish.'); return false; }
    const c = data.configuration;
    for (const key of flags) el('v_' + key).checked = c[key];
    for (const key of [...textFields, ...numbers]) el('v_' + key).value = c[key];
    for (const [id, direction] of [['input_device', 'input_channels'], ['output_device', 'output_channels']]) {
      const select = el('v_' + id); select.replaceChildren(); option(select, 'System default', '');
      data.devices.filter(d => d[direction] > 0).forEach(d => option(select, `${d.name} (${d.host})`, d.id));
      select.value = c[id] ?? '';
    }
    el('v_voice_id').replaceChildren(); option(el('v_voice_id'), 'Matching installed voice (prefer male metadata)', '');
    data.sapi_voices.forEach(v => option(el('v_voice_id'), `${v.name} · ${v.gender || 'unspecified'} · ${v.languages.join(', ') || 'unknown languages'}`, v.id));
    el('v_voice_id').value = c.voice_id;
    el('voiceModelStatus').textContent = `Recognition cache: ${data.model_status}`;
    el('voiceCapabilities').textContent = data.sapi_voices.length ? 'Installed local SAPI metadata only; pronunciation and cinematic quality are unverified.' : 'No SAPI voice metadata available. Text replies remain available.';
    el('voiceActivationStatus').textContent = `Shortcut: ${data.activations.hotkey}; tray: ${data.activations.tray}; wake: ${data.voice.wake_status}`;
    const p = data.personality.presentation;
    el('personalityMode').replaceChildren(); data.personality.profiles.forEach(k => option(el('personalityMode'), k.replaceAll('_', ' '), k));
    el('personalityMode').value = p.mode; el('personalityTone').value = p.tone;
    el('personalityLength').value = p.response_length; el('personalityLanguage').value = p.response_language;
    el('personalitySpokenLimit').value = p.spoken_characters; el('personalityFocusSpeech').checked = p.speak_in_focus;
    el('personalityAddress').value = data.personality.address;
    return true;
  }
  const bind = (id, work) => el(id).addEventListener('click', async () => {
    try { await work(); } catch (_) { notice('Could not apply this request. Check values, local model files and permissions.'); }
  });
  async function queued(result) {
    if (await result) { panel.close(); notice('Queued. Review the exact change in the approval dialog.'); }
    else notice('Wait for the current task or unlock the desktop.');
  }
  bind('voiceSettingsOpen', async () => { if (await refresh() && !panel.open) panel.showModal(); });
  bind('voiceRefresh', refresh);
  bind('voiceUnmute', async () => {
    if (!await api().mute_microphone(false)) { if (await refresh() && !panel.open) panel.showModal(); notice('Enable microphone policy, then explicitly unmute this session.'); }
  });
  bind('voiceMute', () => api().mute_microphone(true));
  bind('voiceInterrupt', () => api().stop());
  bind('voiceCheckMic', async () => { panel.close(); if (!await api().microphone(true)) notice('Enable and unmute the microphone first.'); });
  bind('voiceCheckSpeaker', async () => { panel.close(); await api().test_voice(); });
  bind('voiceSave', () => {
    const v = {};
    flags.forEach(k => { v[k] = el('v_' + k).checked; });
    textFields.forEach(k => { v[k] = el('v_' + k).value.trim(); });
    numbers.forEach(k => { v[k] = Number(el('v_' + k).value); });
    for (const k of ['input_device', 'output_device']) v[k] = el('v_' + k).value === '' ? null : Number(el('v_' + k).value);
    return queued(api().configure_voice(v));
  });
  el('v_mode').addEventListener('change', () => { if (el('v_mode').value === 'auto') el('v_recognition_language').value = 'auto'; });
  el('v_recognition_language').addEventListener('change', () => {
    if (el('v_recognition_language').value !== 'auto' && el('v_mode').value === 'auto') el('v_mode').value = 'en';
  });
  bind('voiceDownloadModel', () => {
    let model = el(el('v_mode').value === 'en-accurate' ? 'v_accurate_model' : 'v_fast_model').value;
    if (el('v_mode').value === 'auto' || el('v_recognition_language').value !== 'en') model = model.replace(/\.en$/, '');
    return queued(api().download_speech_model(model));
  });
  bind('voiceArmWake', () => queued(api().arm_voice_wake()));
  bind('personalitySave', () => queued(api().configure_personality({mode: el('personalityMode').value,
    tone: el('personalityTone').value, response_length: el('personalityLength').value,
    response_language: el('personalityLanguage').value.trim(), spoken_characters: Number(el('personalitySpokenLimit').value),
    speak_in_focus: el('personalityFocusSpeech').checked}, el('personalityAddress').value.trim())));
  document.addEventListener('visibilitychange', () => { if (window.pywebview?.api) api().set_voice_visible(!document.hidden); });
  window.addEventListener('clydex-voice', event => {
    const data = event.detail, voice = data.voice;
    if (!voice) return;
    const live = data.recording || voice.wake_capture_active;
    el('voiceLiveState').classList.toggle('mic-live', live);
    el('voiceLiveState').textContent = voice.locked ? 'Locked · microphone muted' :
      `${live ? 'MIC LIVE' : voice.muted ? 'Microphone muted' : 'Microphone permitted'} · ${voice.state.replaceAll('_', ' ')}${voice.background_armed ? ' · local wake armed' : ''}`;
    el('voiceSettingsOpen').disabled = data.busy || voice.locked;
    el('voiceUnmute').disabled = voice.locked;
    for (const [kind, e] of data.voice_events || []) {
      if (kind === 'voice_event' && ['warning', 'error'].includes(e.kind)) {
        notice(e.details.code === 'synthesis_language_or_voice_unavailable'
          ? 'The selected local speech language or voice is unavailable. The full answer is on screen.'
          : `Voice status: ${(e.details.code || 'unavailable').replaceAll('_', ' ')}. Full answers remain on screen.`);
      }
    }
    if (voice.locked) { el('personalityAddress').value = ''; el('conversationExport').value = ''; el('voiceStatusMessage').textContent = ''; }
  });
})();
