import type {CloudSnapshot,CloudOperation} from '../features/cloud/types';
import contract from '../../../src/clydex/desktop/hud_contract.json';

export type Json = null | boolean | number | string | Json[] | {[key: string]: Json};
export type Values = Record<string, Json>;
export type VoiceState = 'standby' | 'wake_detected' | 'listening' | 'transcribing' | 'thinking' | 'waiting_for_approval' | 'speaking' | 'interrupted' | 'sleeping' | 'error';
export type DisplayMode = 'window' | 'fullscreen' | 'widget' | 'floating' | 'mini' | 'tray';
export type Page = 'overview' | 'conversation' | 'intelligence' | 'memory' | 'voice' | 'personality' | 'notifications' | 'settings' | 'cloud' | 'knowledge' | 'devices' | 'synchronization';
export interface Preferences {
  theme: 'cyber' | 'midnight' | 'graphite'; accent: string; animations: boolean; reduced_motion: boolean;
  resource_saving: boolean; fps: 15 | 30 | 60; particles: number; detail: 'low' | 'balanced' | 'high';
  startup_animation: boolean; startup_sound: boolean; startup_greeting: boolean; sounds_muted: boolean;
  sound_volume: number; dnd: boolean; native_notifications: boolean;
}
export interface VoiceStatus {
  state: VoiceState; muted: boolean; locked: boolean; visible: boolean; background_armed: boolean;
  wake_capture_active: boolean; wake_status: string; half_duplex: boolean; microphone_enabled: boolean;
}
export interface Review {id: string; description: string; script: string; digest: string; expires_in: number}
export interface Message {id: string; role: 'user' | 'bot' | 'error' | 'mic_info'; text: string}
export interface Notice {id: string; code: string; message: string; timestamp: number}
export interface VoiceEvent {kind: string; state: VoiceState; timestamp: number; details: Values}
export interface Telemetry {kind: 'audio'; timestamp: number; direction: string; amplitude: number; frequency_spectrum: number[]}
export interface Display {mode: DisplayMode; visible: boolean; monitor: number; modes: DisplayMode[]; monitors: {index: number; x: number; y: number; width: number; height: number}[]}
export interface WidgetData {
  status: string; alerts: [string, string][]; timer_remaining?: number; timer_duration?: number; timer_running?: boolean;
  alarm_at?: string | null; stopwatch_elapsed?: number; stopwatch_running?: boolean; lap_count?: number;
  lap?: string; city?: string; weather?: string; temperature?: string; weather_status?: string; weather_metrics?: string;
}
export interface Frame {
  version: 1; locked: boolean; state?: string; busy?: boolean; recording?: boolean;
  voice: VoiceStatus; review: Review | null; level?: number; bands?: number[]; wave?: number[];
  voice_events?: [string, VoiceEvent | Telemetry][]; messages: Message[]; notifications: Notice[];
  revision?: number; preferences: Preferences; display: Display; personality?: string; language?: string;
  provider?: {provider?: string; model?: string; status?: string; memory_used?: number};
  session?: {title: string; temporary: boolean}; uptime_seconds?: number; widget?: WidgetData;
  playback?: {frames_played: number; sample_rate: number | null; completed: boolean | null};
  system?: {os: string; release: string; cpu_percent: number | null; memory_percent: number | null; memory_total_bytes: number | null; process_memory_bytes: number | null};
}
export interface Bootstrap {version: number; initialization: {component: string; status: string; detail: string}[]; preferences: Preferences; display: Display}
export interface Provider extends Values {id: string; enabled: boolean; model: string; endpoint: string; status: string; requires_key: boolean; allow_paid: boolean}
export interface Intelligence {providers: Provider[]; routing: Values; memory_policy: Values; current: {title: string; temporary: boolean}; privacy_ceiling: boolean; cloud_allowed: boolean}
export interface VoiceSettings {configuration: Values; voice: VoiceStatus; model_status: string; warnings: string[];
  devices: {id: number; name: string; host: string; input_channels: number; output_channels: number}[];
  sapi_voices: {id: string; name: string; gender: string; languages: string[]}[];
  personality: {presentation: Values; address: string; profiles: string[]}; activations: Values}
export interface MemoryRecord {id: string; category: string; value: string; local_only: boolean; revision: number; origin: string; source_kind: string; created_at: string}
export interface Memories {records: MemoryRecord[]; proposals: MemoryRecord[]; policy: {enabled: boolean; automatic: boolean; categories: string[]}}
export interface Conversation {id: string; title: string; status: string; updated_at: string}
export interface Permissions {scopes: {scope: string; disabled: boolean; startup_disabled: boolean}[]; cloud_allowed: boolean; privacy_ceiling: boolean}
export type Command = keyof typeof contract.command;
type FieldType<T> = T extends 'string' | 'string?' ? string : T extends 'boolean' | 'boolean?' ? boolean : T extends 'integer' | 'integer?' ? number : T extends 'array' ? Json[] : Values;
type Fields<T> = {[K in keyof T as T[K] extends `${string}?` ? never : K]: FieldType<T[K]>} & {[K in keyof T as T[K] extends `${string}?` ? K : never]?: FieldType<T[K]>};
// JSON module values widen to strings; explicit command payload contracts keep call sites strict.
export interface CommandPayloads {
  'cloud.configure': {values:Values}; 'cloud.action': {operation:CloudOperation;values:Values}; 'knowledge.select': {folder?:boolean};
  'chat.send': {message: string}; 'chat.clear': {}; 'voice.capture': {check?: boolean}; 'voice.mute': {muted: boolean};
  'voice.stop': {}; 'voice.test': {}; 'voice.arm': {}; 'voice.configure': {values: Values}; 'voice.download': {model: string};
  'personality.configure': {values: Values; address?: string}; 'provider.configure': {name: string; values: Values; secret?: string; remove_key?: boolean};
  'provider.check': {name: string}; 'routing.configure': {values: Values}; 'conversation.manage': {values: Values};
  'conversation.resume': {id: string}; 'memory.manage': {values: Values}; 'memory.configure': {values: Values};
  'approval.decide': {id: string; approve: boolean}; 'display.mode': {mode: DisplayMode}; 'display.monitor': {index: number};
  'preferences.configure': {values: Values}; 'permissions.configure': {disabled_scopes: string[]};
  'widget.action': {operation: string; seconds?: number; hour?: number; minute?: number; city?: string};
  'notifications.clear': {}; 'notifications.native_test': {}; 'startup.greet': {};
}
export interface ReadResults {cloud: CloudSnapshot; bootstrap: Bootstrap; intelligence: Intelligence; voice: VoiceSettings; memories: Memories; conversations: Conversation[]; export: string; preferences: Preferences; permissions: Permissions; widget: WidgetData}
export interface Reply {ok: boolean; error?: string; data?: unknown}
export interface PythonBridge {hud_snapshot(): Promise<unknown>; hud_read(section: string, params: Values): Promise<Reply>; hud_command(action: string, payload: unknown): Promise<Reply>}
declare global {interface Window {pywebview?: {api: PythonBridge}}}
export {contract};
export type ContractFields<T extends keyof typeof contract.command> = Fields<(typeof contract.command)[T]>;
