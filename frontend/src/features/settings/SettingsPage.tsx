import {useEffect, useState} from 'react';
import {SlidersHorizontal, ShieldCheck, Bell, Keyboard} from 'lucide-react';
import {ConfigFields} from '../../components/ConfigFields';
import {Panel, Field, Toggle, ErrorNotice, ReviewButton, Refresh} from '../../components/ui';
import {useRead} from '../../hooks/useRead';
import {command} from '../../services/bridge';
import type {Frame, Values} from '../../types/bridge';

export function SettingsPage({frame,onError}:{frame:Frame;onError:(e:string)=>void}) {
  const [values,setValues]=useState<Values>({...frame.preferences});
  const {data:permissions,error,refresh}=useRead('permissions',frame.revision),[disabled,setDisabled]=useState<string[]|null>(null);
  useEffect(()=>setValues({...frame.preferences}),[frame.revision]);
  const run=(work:Promise<void>)=>{void work.catch(e=>onError(e.message));};
  return <div className="page-stack"><div className="two-columns"><Panel title="Your control room" eyebrow="LOOK & FEEL"><SlidersHorizontal className="section-icon"/><ConfigFields values={values} keys={['theme','animations','reduced_motion','resource_saving','fps','particles','detail']} onChange={(k,v)=>setValues(p=>({...p,[k]:v}))} choices={{theme:['cyber','midnight','graphite'],fps:['15','30','60'],detail:['low','balanced','high']}}/>
    <Field label="Custom accent color" hint="Foreground accent is adjusted for readable contrast; decorative color follows your selection."><input type="color" value={String(values.accent)} onChange={e=>setValues(p=>({...p,accent:e.target.value}))}/></Field><p className="quiet-note">Hidden rendering is suspended. Focus/gaming and resource saving cap particles and FPS. No CPU/GPU performance target is implied.</p>
    <Field label="Move this window to a display"><select value={frame.display.monitor} onChange={e=>run(command('display.monitor',{index:Number(e.target.value)}))}>{frame.display.monitors.map(m=><option value={m.index} key={m.index}>Display {m.index+1} · {m.width} × {m.height}</option>)}</select></Field>
  </Panel><div className="page-stack"><Panel title="A considered arrival" eyebrow="STARTUP"><ConfigFields values={values} keys={['startup_animation','startup_sound','startup_greeting']} onChange={(k,v)=>setValues(p=>({...p,[k]:v}))}/><p className="quiet-note">Startup reports local initialization, not live provider acceptance. Optional greeting is neutral and local. Silent startup is the default.</p></Panel>
    <Panel title="Signals, not interruptions" eyebrow="SOUND & NOTIFICATIONS"><Bell className="section-icon"/><ConfigFields values={values} keys={['sounds_muted','sound_volume','dnd','native_notifications']} onChange={(k,v)=>setValues(p=>({...p,[k]:v}))}/><p className="quiet-note">Original synthesized cues: startup, wake, task completion, warning, notification and shutdown. No thinking sound. Browser playback needs a user gesture; native notices contain generic status only.</p><button className="button" onClick={()=>run(command('notifications.native_test',{}))}>Test permitted native notification</button></Panel></div></div>
    <ReviewButton disabled={frame.busy} onClick={()=>run(command('preferences.configure',{values}))}>Review presentation preferences</ReviewButton>
    <Panel title="Permission boundaries" eyebrow="SECURITY & PRIVACY" action={<Refresh onClick={()=>void refresh()}/> }><ErrorNotice text={error}/><div className="security-banner"><ShieldCheck size={23}/><p>These are installed trusted capability scopes. Checked restrictions disable a scope. Startup restrictions remain enforced; presentation settings cannot override them.</p></div>
      <div className="scope-grid">{permissions?.scopes.map(scope=><Toggle key={scope.scope} label={`${scope.scope}${scope.startup_disabled?' · startup restriction':''}`} checked={(disabled??permissions.scopes.filter(s=>s.disabled).map(s=>s.scope)).includes(scope.scope)} disabled={scope.startup_disabled||scope.scope==='security.settings'} onChange={yes=>{const scopes=disabled??permissions.scopes.filter(s=>s.disabled).map(s=>s.scope);setDisabled(yes?[...scopes,scope.scope]:scopes.filter(s=>s!==scope.scope));}}/>)}</div><ReviewButton disabled={!permissions||frame.busy} onClick={()=>run(command('permissions.configure',{disabled_scopes:disabled??permissions!.scopes.filter(s=>s.disabled).map(s=>s.scope)}))}>Review capability restrictions</ReviewButton>
      <p className="quiet-note">Cloud privacy and offline routing are managed in Intelligence. Microphone/background policy is managed in Voice. A wake word is not authentication. Approvals do not sandbox native same-user code.</p></Panel>
    <Panel title="A familiar way back" eyebrow="LEGACY FALLBACK"><Keyboard className="section-icon"/><p>The existing legacy Studio and standalone Smart Widget remain available. Start the voice launcher with <code>--legacy</code> after closing this window to use the fallback. Switching HUD views keeps this Core and its timers alive.</p></Panel>
  </div>;
}
