import {Mic, MicOff, Square, AudioLines, ShieldCheck} from 'lucide-react';
import {command} from '../../services/bridge';
import type {Frame} from '../../types/bridge';

export function Spectrum({bands = [], wave = []}: {bands?: number[]; wave?: number[]}) {
  return <div className="spectrum" role="img" aria-label="Actual audio frequency energy"><svg viewBox="0 0 360 48" preserveAspectRatio="none">
    <path d="M0 24H360" className="signal-baseline"/>{bands.map((value, i) => <rect key={i} x={i * 360 / bands.length + 1} y={24 - Math.min(1, value) * 21} width={Math.max(1, 360 / bands.length - 4)} height={Math.max(1, Math.min(1, value) * 42)} rx="1"/>) }
    {wave.length > 1 && <polyline points={wave.map((v, i) => `${i * 360 / (wave.length - 1)},${24 - Math.tanh(v * 4) * 20}`).join(' ')} />}
  </svg></div>;
}
export function VoiceControls({frame, onError, small = false}: {frame: Frame; onError: (e: string) => void; small?: boolean}) {
  const run = (work: Promise<void>) => {void work.catch(e => onError(e.message));};
  const live = frame.recording || frame.voice.wake_capture_active;
  return <section className={`voice-bar ${small ? 'small-voice-bar' : ''}`} aria-label="Voice and emergency controls">
    <div className="voice-signal-label"><AudioLines size={17}/><div><b>{live ? 'Microphone live' : frame.voice.muted ? 'Microphone muted' : 'Microphone permitted'}</b><small>{frame.voice.half_duplex ? 'HALF DUPLEX' : 'VOICE'} · {frame.voice.state.replaceAll('_', ' ').toUpperCase()}</small></div></div>
    <Spectrum bands={frame.bands} wave={frame.wave}/>
    <div className="voice-actions">
      <button className={`button ${frame.recording ? 'live' : 'primary'}`} disabled={!frame.recording && (frame.busy || frame.voice.muted)} onClick={() => run(command('voice.capture', {}))}><Mic size={16}/>{frame.recording ? 'Finish recording' : 'Talk'}</button>
      {frame.voice.muted ? <button className="button" onClick={() => run(command('voice.mute', {muted: false}))}><Mic size={16}/>Unmute</button> : <button className="button" onClick={() => run(command('voice.mute', {muted: true}))}><MicOff size={16}/>Mute</button>}
      <button className="button stop-button" onClick={() => run(command('voice.stop', {}))}><Square size={13}/>Stop</button>
    </div><span className="privacy-inline"><ShieldCheck size={12}/>Local speech · supervised actions</span>
  </section>;
}
