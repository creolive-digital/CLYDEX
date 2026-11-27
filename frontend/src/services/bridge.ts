import {contract, type Command, type CommandPayloads, type Frame, type ReadResults, type Values} from '../types/bridge';

export function validateFrame(value: unknown): Frame {
  if (!value || typeof value !== 'object') throw new Error('Invalid desktop response');
  const f = value as Frame;
  if (f.version !== 1 || typeof f.locked !== 'boolean' || !f.voice || !f.display || !f.preferences ||
      !Array.isArray(f.messages) || !Array.isArray(f.notifications)) throw new Error('Incompatible desktop contract');
  const states = ['standby','wake_detected','listening','transcribing','thinking','waiting_for_approval','speaking','interrupted','sleeping','error'];
  if (!states.includes(f.voice.state) || f.messages.some(m => typeof m.text !== 'string' || typeof m.id !== 'string')) throw new Error('Invalid desktop state');
  if (f.level !== undefined && (!Number.isFinite(f.level) || f.level < 0)) throw new Error('Invalid audio level');
  if (f.bands && (!Array.isArray(f.bands) || f.bands.length > 256 || f.bands.some(v => !Number.isFinite(v)))) throw new Error('Invalid spectrum');
  if (f.locked) return {...f, messages: [], notifications: [], review: null, level: 0, bands: [], wave: []};
  return f;
}
export function api() {
  if (!window.pywebview?.api) throw new Error('Open CLYDEX from the Windows desktop launcher.');
  return window.pywebview.api;
}
export async function command<K extends Command>(name: K, payload: CommandPayloads[K]): Promise<void> {
  if (!(name in contract.command)) throw new Error('Unknown desktop action');
  const result = await api().hud_command(name, payload);
  if (!result.ok) throw new Error(result.error || 'Request unavailable. Check microphone permission, pending work and local configuration.');
}
export async function read<K extends keyof ReadResults>(section: K, params: Values = {}): Promise<ReadResults[K]> {
  const result = await api().hud_read(section, params);
  if (!result.ok || result.data === undefined || (typeof result.data === 'object' && result.data &&
      ('busy' in result.data || 'locked' in result.data))) throw new Error(result.error || 'Wait for the current task or unlock the desktop.');
  return result.data as ReadResults[K];
}
