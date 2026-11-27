import type {Frame} from '../../types/bridge';

export type SoundCategory='startup'|'wake'|'completion'|'security'|'notification'|'shutdown';
export const tones:Record<SoundCategory,number[]>={startup:[330,495,660],wake:[540,810],completion:[520,780],security:[260,220],notification:[620],shutdown:[500,375,250]};
/** Original procedural oscillator cues. No missing or third-party sound asset is assumed. */
export class SoundEvents {
  private context:AudioContext|null=null;
  private seen=new Set<string>();
  private oscillators=new Set<OscillatorNode>();
  private frame:Frame|null=null;
  private started=false;
  private lastWake=0;
  unlock=()=>{if(!this.context&&this.frame&&!this.frame.preferences.sounds_muted){this.context=new AudioContext();}void this.context?.resume();};
  update(frame:Frame){
    this.frame=frame;
    if(frame.locked||document.hidden||!frame.display.visible||frame.preferences.dnd||frame.preferences.sounds_muted||['focus','gaming'].includes(frame.personality||'')){this.stop();for(const notice of frame.notifications)this.seen.add(notice.id);if(this.seen.size>200)this.seen=new Set(frame.notifications.map(n=>n.id));return;}
    if(!this.started&&this.context?.state==='running'){this.started=true;if(frame.preferences.startup_sound)this.play('startup');}
    for(const notice of frame.notifications){if(this.seen.has(notice.id))continue;this.seen.add(notice.id);this.play(notice.code.includes('approval')||notice.code.includes('error')?'security':notice.code==='task.complete'?'completion':'notification');}
    if(this.seen.size>200)this.seen=new Set(frame.notifications.map(n=>n.id));
    for(const [kind,event]of frame.voice_events||[]){if(kind==='voice_event'&&event.kind==='wake_detected'&&event.timestamp>this.lastWake){this.lastWake=event.timestamp;this.play('wake');}}
  }
  play(category:SoundCategory){
    const frame=this.frame;if(!this.context||this.context.state!=='running'||!frame||frame.locked||document.hidden||frame.preferences.sounds_muted||frame.preferences.dnd||!frame.display.visible||['focus','gaming'].includes(frame.personality||''))return;
    const now=this.context.currentTime;
    tones[category].forEach((frequency,index)=>{const oscillator=this.context!.createOscillator(),gain=this.context!.createGain();oscillator.type='sine';oscillator.frequency.value=frequency;gain.gain.setValueAtTime(0,now+index*.09);gain.gain.linearRampToValueAtTime(frame.preferences.sound_volume/100*.07,now+index*.09+.01);gain.gain.exponentialRampToValueAtTime(.0001,now+index*.09+.09);oscillator.connect(gain);gain.connect(this.context!.destination);this.oscillators.add(oscillator);oscillator.onended=()=>{oscillator.disconnect();gain.disconnect();this.oscillators.delete(oscillator);};oscillator.start(now+index*.09);oscillator.stop(now+index*.09+.1);});
  }
  stop(){for(const oscillator of this.oscillators){try{oscillator.stop();}catch(_){/* Already stopped. */}}this.oscillators.clear();}
  dispose(){this.stop();void this.context?.close();this.context=null;}
}
