import {useEffect, useRef, useState, type CSSProperties} from 'react';
import type {AvatarRenderer, AvatarSignal} from './renderer';
import reference from '../../../../assets/avatars/clydex_avatar_reference.png';
import type {Frame} from '../../types/bridge';

export function Avatar({frame, compact = false}: {frame: Frame; compact?: boolean}) {
  const host = useRef<HTMLDivElement>(null), renderer = useRef<AvatarRenderer | null>(null);
  const [fallback, setFallback] = useState(false), [visible, setVisible] = useState(!document.hidden);
  const signal: AvatarSignal = {state: frame.voice.state, amplitude: visible ? Math.min(1, Math.sqrt(frame.level || 0) * 2) : 0,
    spectrum: frame.bands || [], playbackFrames: frame.playback?.frames_played, sampleRate: frame.playback?.sample_rate,
    active: visible && frame.display.visible && frame.display.mode !== 'tray' && !frame.locked,
    preferences: frame.preferences, constrained: ['focus','gaming'].includes(frame.personality || '') || ['standby','sleeping'].includes(frame.voice.state)};
  const current = useRef(signal); current.current = signal;
  useEffect(() => {
    const change = () => setVisible(!document.hidden); document.addEventListener('visibilitychange', change);
    let alive = true;
    void import('./renderer').then(({HologramField}) => {if (!alive) return; try {renderer.current = new HologramField(host.current!, current.current, () => setFallback(true));} catch (_) {setFallback(true);}}).catch(() => {if (alive) setFallback(true);});
    return () => {alive = false; document.removeEventListener('visibilitychange', change); renderer.current?.dispose(); renderer.current = null;};
  }, []);
  useEffect(() => {renderer.current?.update(signal);}, [frame.level, frame.voice.state, frame.preferences, frame.display.visible, frame.personality, visible]);
  const energy = signal.amplitude;
  return <section className={`avatar-stage ${compact ? 'compact-avatar' : ''} state-${frame.voice.state}`} aria-label="Digital Wireframe reference presentation"
    style={{'--energy': energy, '--envelope': `${Math.max(2, energy * 65)}px`} as CSSProperties}>
    <div className="avatar-field" ref={host}/><div className="orbital orbital-one"/><div className="orbital orbital-two"/>
    <div className="avatar-ruler left-ruler" aria-hidden="true"/><div className="avatar-ruler right-ruler" aria-hidden="true"/>
    <div className="avatar-reference"><img src={reference} alt="Owner-approved masculine cyan Digital Wireframe reference"/><div className="hologram-scan"/></div>
    <span className="avatar-coordinate left-coordinate">DIGITAL<br/>WIREFRAME / 01</span><span className="avatar-coordinate right-coordinate">LOCAL<br/>PRESENTATION</span>
    <div className="avatar-floor"/>
    <div className="avatar-caption"><div className="state-label"><span className="status-dot"/>{frame.voice.state.replaceAll('_', ' ')}</div>
      <div className="speech-envelope" aria-label="Measured audio envelope, not phoneme lip synchronization"><i/><i/><i/><i/><i/></div>
      <p>Approved reference · production rig pending</p><small>{fallback ? 'WebGL unavailable · reference fallback' : 'Audio-reactive field · no viseme timing'}{frame.playback?.frames_played ? ` · last playback ${frame.playback.frames_played} frames` : ''}</small></div>
  </section>;
}
