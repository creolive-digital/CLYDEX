import {Field, Toggle} from './ui';
import type {Json, Values} from '../types/bridge';

const labels: Record<string, string> = {
  enabled: 'Enable provider', model: 'Model identifier', endpoint: 'Provider endpoint', allow_paid: 'Permit billed requests, subject to review',
  stream: 'Receive supported streaming responses', local_only_confirmed: 'I run local-only Ollama with OLLAMA_NO_CLOUD=1',
  upstream: 'Approved OpenRouter upstream', selected: 'Selected provider', automatic: 'Automatic routing', privacy: 'Block cloud transmission', offline: 'Offline routing only',
  fast: 'Fast provider order', balanced: 'Balanced provider order', advanced: 'Advanced provider order', offline_order: 'Offline provider order', fallbacks: 'Explicit fallback providers',
  max_request_cost: 'Estimated cost ceiling (blank disables)', input_price_per_million: 'Input price per million tokens', output_price_per_million: 'Output price per million tokens',
  microphone_enabled: 'Permit microphone use · also requires unmute this session', background_listening: 'Permit background capture/output with native indicator',
  continuous: 'Follow-up conversation', wake_enabled: 'Configure custom local Hey CLYDEX detection', hotkey_enabled: 'Enable global shortcut', tray_enabled: 'Enable native tray controls',
  tts_language: 'Speech synthesis language', recognition_language: 'Recognition language', response_language: 'Response language',
  piper_manifest: 'Licensed local Piper manifest', wake_manifest: 'Validated local wake manifest', spoken_characters: 'Spoken response character limit',
  speak_in_focus: 'Allow spoken replies in focus/gaming mode', max_no_speech: 'Maximum no-speech probability', min_avg_logprob: 'Minimum recognition log probability',
  min_language_probability: 'Minimum automatic language confidence', privacy_ceiling: 'Startup privacy ceiling',
};
export const labelFor = (key: string) => labels[key] || key.replaceAll('_', ' ').replace(/^./, c => c.toUpperCase());
export function ConfigFields({values, keys, onChange, choices = {}, readonly = []}: {values: Values; keys: string[]; onChange: (key: string, value: Json) => void; choices?: Record<string, string[]>; readonly?: string[]}) {
  return <div className="form-grid">{keys.filter(key => key in values).map(key => {
    const value = values[key], label = labelFor(key), disabled = readonly.includes(key);
    if (typeof value === 'boolean') return <Toggle key={key} label={label} checked={value} disabled={disabled} onChange={v => onChange(key, v)}/>;
    if (choices[key]) return <Field key={key} label={label}><select value={String(value)} disabled={disabled} onChange={e => onChange(key, typeof value === 'number' ? Number(e.target.value) : e.target.value)}>{choices[key].map(option => <option key={option} value={option}>{option.replaceAll('_', ' ')}</option>)}</select></Field>;
    if (Array.isArray(value)) return <Field key={key} label={label} hint="Comma-separated identifiers, in priority order"><input disabled={disabled} value={value.join(', ')} onChange={e => onChange(key, e.target.value.split(',').map(x => x.trim()).filter(Boolean))}/></Field>;
    if (value !== null && typeof value === 'object') return null;
    const numeric = typeof value === 'number' || value === null;
    return <Field key={key} label={label}><input type={numeric ? 'number' : 'text'} step={numeric ? 'any' : undefined} disabled={disabled} value={value === null ? '' : String(value)} maxLength={2000}
      onChange={e => onChange(key, numeric ? (e.target.value === '' && (value === null || ['max_request_cost','input_price_per_million','output_price_per_million'].includes(key)) ? null : Number(e.target.value)) : e.target.value)}/></Field>;
  })}</div>;
}
