import {OperatingPage,type OperatingPageName} from '../features/automation/OperatingPage';
import {useEffect,useRef,useState} from 'react';
import {Activity,MessageSquare,CircuitBoard,Brain,Mic,SlidersHorizontal,Bell,UserRound,LayoutDashboard,ShieldCheck,ArrowUpRight,Monitor,Maximize2,VolumeX,LockKeyhole,ChevronRight,Layers,Command as CommandIcon,LoaderCircle} from 'lucide-react';
import logo from '../../../assets/branding/clydex_logo_reference.png';
import {desktop,useDesktop} from '../stores/desktop';
import {read,command} from '../services/bridge';
import {Panel,ErrorNotice} from '../components/ui';
import {Avatar} from '../features/avatar/Avatar';
import {Chat} from '../features/chat/Chat';
import {VoiceControls} from '../features/voice/VoiceControls';
import {VoicePage,PersonalityPage} from '../features/voice/VoicePage';
import {IntelligencePage,History} from '../features/intelligence/IntelligencePage';
import {MemoryPage} from '../features/memory/MemoryPage';
import {SettingsPage} from '../features/settings/SettingsPage';
import {WidgetPage,useClock,duration} from '../features/settings/WidgetPage';
import {NotificationsPage} from '../features/notifications/NotificationsPage';
import {SoundEvents} from '../features/notifications/sounds';
import {Approval} from '../features/permissions/Approval';
import {CloudPage} from '../features/cloud/CloudPage';
import {KnowledgePage} from '../features/knowledge/KnowledgePage';
import {DevicesPage} from '../features/devices/DevicesPage';
import {SynchronizationPage} from '../features/synchronization/SynchronizationPage';
import {readableAccent} from '../themes/colors';
import type {Bootstrap,DisplayMode,Frame,Page} from '../types/bridge';

const navigation:{id:Page;label:string;icon:typeof Activity}[]=[{id:'overview',label:'Overview',icon:LayoutDashboard},{id:'conversation',label:'Conversation',icon:MessageSquare},{id:'intelligence',label:'Intelligence',icon:CircuitBoard},{id:'memory',label:'Memory',icon:Brain},{id:'voice',label:'Voice',icon:Mic},{id:'personality',label:'Personality',icon:UserRound},{id:'cloud',label:'Personal Cloud',icon:CircuitBoard},{id:'knowledge',label:'Knowledge Vault',icon:Brain},{id:'devices',label:'Devices',icon:Monitor},{id:'synchronization',label:'Synchronization',icon:Layers},...(['automation','developer','routines','triggers','feeds','plugins','integrations','monitoring','activity'] as const).map(id=>({id,label:({automation:'Automation Studio',developer:'Developer Center',routines:'Routines',triggers:'Triggers',feeds:'Intelligence Feeds',plugins:'Plugins',integrations:'Integrations',monitoring:'Monitoring',activity:'Activity'})[id],icon:Activity})),{id:'notifications',label:'Notifications',icon:Bell},{id:'settings',label:'Settings',icon:SlidersHorizontal}];
const modeLabels:Record<DisplayMode,string>={window:'Desktop window',fullscreen:'Full-screen command center',widget:'Smart Widget',floating:'Floating Hologram',mini:'Mini Voice Bar',tray:'System Tray'};
export function Startup({data,onFinish}:{data:Bootstrap;onFinish:()=>void}){
  useEffect(()=>{if(!data.preferences.startup_animation||data.preferences.reduced_motion){onFinish();return;}const timer=setTimeout(onFinish,1800);return()=>clearTimeout(timer);},[data.preferences.startup_animation,data.preferences.reduced_motion]);
  return <div className="startup" role="status" aria-label="Local component initialization"><img src={logo} alt="CLYDEX Intelligence Core official reference"/><span className="eyebrow">YOUR PERSONAL DIGITAL INTELLIGENCE</span><h1>A clear connection.</h1><div className="startup-components">{data.initialization.map(c=><div key={c.component}><span className={`component-state ${c.status}`}/><b>{c.component}</b><span>{c.detail}</span><small>{c.status}</small></div>)}</div><div className="form-actions"><button className="button" onClick={onFinish}>Skip animation<ChevronRight size={15}/></button><span><VolumeX size={13}/>Silent by default · no provider probe</span></div></div>;
}
export function App(){
  const {frame:received,connected,error:connectionError}=useDesktop(),[page,setPage]=useState<Page>('overview'),[error,setError]=useState(''),[bootstrap,setBootstrap]=useState<Bootstrap|null>(null),[boot,setBoot]=useState(true),[reduced,setReduced]=useState(window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const sounds=useRef<SoundEvents|null>(null);
  const now=useClock();
  useEffect(()=>{const start=()=>desktop.start();if(window.pywebview?.api)start();window.addEventListener('pywebviewready',start);return()=>{window.removeEventListener('pywebviewready',start);desktop.stop();};},[]);
  useEffect(()=>{if(connected&&!bootstrap)void read('bootstrap').then(setBootstrap).catch(e=>setError(e.message));},[connected,bootstrap]);
  useEffect(()=>{const media=window.matchMedia('(prefers-reduced-motion: reduce)'),change=()=>setReduced(media.matches);media.addEventListener('change',change);return()=>media.removeEventListener('change',change);},[]);
  useEffect(()=>{const manager=new SoundEvents();sounds.current=manager;const quiet=()=>{if(document.hidden)manager.stop();};window.addEventListener('pointerdown',manager.unlock);window.addEventListener('keydown',manager.unlock);document.addEventListener('visibilitychange',quiet);return()=>{window.removeEventListener('pointerdown',manager.unlock);window.removeEventListener('keydown',manager.unlock);document.removeEventListener('visibilitychange',quiet);manager.dispose();};},[]);
  useEffect(()=>{if(received)sounds.current?.update(received);},[received]);
  useEffect(()=>{const goodbye=()=>sounds.current?.play('shutdown');window.addEventListener('beforeunload',goodbye);return()=>window.removeEventListener('beforeunload',goodbye);},[]);
  useEffect(()=>{if(received?.locked)setError('');},[received?.locked]);
  useEffect(()=>{if(bootstrap&&!boot&&received&&!received.locked&&bootstrap.preferences.startup_greeting)void command('startup.greet',{}).catch(()=>{});},[bootstrap,boot]);
  const run=(work:Promise<void>)=>{void work.catch(e=>setError(e.message));};
  const selectMode=(mode:DisplayMode)=>run(command('display.mode',{mode}));
  useEffect(()=>{const escape=(event:KeyboardEvent)=>{if(event.key==='Escape'&&!event.defaultPrevented&&received?.display.mode==='fullscreen')selectMode('window');};window.addEventListener('keydown',escape);return()=>window.removeEventListener('keydown',escape);},[received?.display.mode]);
  if(!received)return <div className="disconnected"><img src={logo} alt="CLYDEX Intelligence Core"/><h1>CLYDEX</h1><p>{connectionError||'Waiting for the local desktop bridge.'}</p><small>Launch the Windows app to connect to your Core. This view does not simulate services.</small><ErrorNotice text={error}/></div>;
  const frame:Frame={...received,preferences:{...received.preferences,reduced_motion:received.preferences.reduced_motion||reduced}};
  const activeMotion=frame.preferences.animations&&!frame.preferences.reduced_motion&&!['focus','gaming'].includes(frame.personality||'');
  document.documentElement.dataset.theme=frame.preferences.theme;
  document.documentElement.dataset.motion=activeMotion?'on':'off';
  document.documentElement.style.setProperty('--accent',frame.preferences.accent);
  document.documentElement.style.setProperty('--accent-ink',readableAccent(frame.preferences.accent));
  if(frame.locked)return <div className="privacy-shield" role="status"><LockKeyhole size={38}/><h1>Your space stays private.</h1><p>Microphone muted. Pending actions canceled.<br/>Unlock Windows to return. Unmute and wake arming remain explicit.</p><div className="form-actions"><button className="button" onClick={()=>run(command('voice.stop',{}))}>Stop task</button><button className="button" onClick={()=>run(command('voice.mute',{muted:true}))}>Mute microphone</button></div></div>;
  const mode=frame.display.mode,compact=['widget','floating','mini'].includes(mode);
  const provider=frame.provider?.provider||'No request yet';
  return <div className={`application display-${mode}`}>
    {!compact&&<aside className="navigation"><a className="identity" href="#main" aria-label="CLYDEX command center"><img src={logo} alt="Intelligence Core"/></a><nav aria-label="Main navigation">{navigation.map(item=><button key={item.id} className={page===item.id?'active':''} aria-current={page===item.id?'page':undefined} onClick={()=>{setPage(item.id);setError('');}} title={item.label}><item.icon size={20}/><span>{item.id==='synchronization'?'Sync':item.label}</span>{item.id==='notifications'&&!!frame.notifications.length&&<i>{frame.notifications.length}</i>}</button>)}</nav><div className="nav-bottom"><ShieldCheck size={17}/><span>SUPERVISED<br/>BY DESIGN</span></div></aside>}
    <div className="workspace"><header className="topbar"><div className="workspace-label"><CommandIcon size={15}/><span>PERSONAL WORKSPACE</span><span className="divider">/</span><b>{compact?modeLabels[mode]:navigation.find(x=>x.id===page)?.label}</b></div>
      <div className="topbar-right"><span className={`connection-indicator ${connected?'':'offline'}`}><i/>{connected?'LOCAL CORE CONNECTED':'CONNECTION LOST'}</span><time>{now.toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit',hour12:false})}</time><label className="mode-picker"><span className="sr-only">Display mode</span><select value={mode} onChange={e=>selectMode(e.target.value as DisplayMode)}>{frame.display.modes.map(m=><option key={m} value={m}>{modeLabels[m]}</option>)}</select></label>{compact&&<button className="icon-button" title="Open command center" aria-label="Open command center" onClick={()=>selectMode('window')}><Maximize2 size={17}/></button>}</div></header>
      <main id="main" className="main-content" tabIndex={-1}>
        {!compact&&<div className="page-title"><div><span className="eyebrow">CLYDEX / {page==='overview'?'COMMAND CENTER':page.toUpperCase()}</span><h1>{page==='overview'?'Intelligence, in your element.':navigation.find(x=>x.id===page)?.label}</h1></div><span className="page-mode"><span className="status-dot"/>{(frame.personality||'personal').replaceAll('_',' ')} mode</span></div>}
        <ErrorNotice text={error}/>
        {mode==='mini'?<VoiceControls frame={frame} onError={setError} small/>:mode==='floating'?<><Avatar frame={frame} compact/><VoiceControls frame={frame} onError={setError} small/><button className="button floating-open" onClick={()=>selectMode('window')}>Open command center<ArrowUpRight size={14}/></button></>:mode==='widget'?<><WidgetPage frame={frame} onError={setError}/><VoiceControls frame={frame} onError={setError} small/></>:
          page==='overview'?<><div className="overview-grid"><div className="presence-panel"><div className="presence-heading"><div><span className="eyebrow">INTELLIGENCE CORE</span><h2>Your personal digital intelligence.</h2></div><span className="presence-index">01 / LIVE STATE</span></div><Avatar frame={frame}/><div className="presence-bottom"><span><ShieldCheck size={13}/> {frame.review?'ACTION REVIEW REQUIRED':'YOUR PERMISSIONS. ALWAYS.'}</span><span>{frame.language?.toUpperCase()||'—'} / LOCAL SPEECH</span></div></div><Chat frame={frame} onError={setError}/></div>
          <VoiceControls frame={frame} onError={setError}/><div className="insights"><Panel eyebrow="INTELLIGENCE ROUTE"><CircuitBoard size={20}/><b>{provider}</b><small>{frame.provider?.model||'Model resolved on request'} · {frame.provider?.status||'No inference observed'}</small></Panel><Panel eyebrow="PERSONAL CONTEXT"><Brain size={20}/><b>{frame.session?.temporary?'Temporary session':'Encrypted saved session'}</b><small>{frame.provider?.memory_used??0} memories used in the latest observed request</small></Panel><Panel eyebrow="SYSTEM OBSERVATION"><Activity size={20}/><b>CPU {frame.system?.cpu_percent==null?'—':`${frame.system.cpu_percent}%`}<span>RAM {frame.system?.memory_percent==null?'—':`${frame.system.memory_percent}%`}</span></b><small>{frame.system?`${frame.system.os} ${frame.system.release}`:'Counters unavailable'} · uptime {duration(frame.uptime_seconds)}</small></Panel></div></>:
          page==='conversation'?<div className="conversation-layout"><Chat frame={frame} onError={setError} full/><History frame={frame} onError={setError}/></div>:
          (['automation','developer','routines','triggers','feeds','plugins','integrations','monitoring','activity'].includes(page))?<OperatingPage page={page as OperatingPageName} frame={frame} onError={setError}/>:page==='cloud'?<CloudPage frame={frame} onError={setError}/>:page==='knowledge'?<KnowledgePage frame={frame} onError={setError}/>:page==='devices'?<DevicesPage frame={frame} onError={setError}/>:page==='synchronization'?<SynchronizationPage frame={frame} onError={setError}/>:page==='intelligence'?<IntelligencePage frame={frame} onError={setError}/>:page==='memory'?<MemoryPage frame={frame} onError={setError}/>:page==='voice'?<VoicePage frame={frame} onError={setError}/>:page==='personality'?<PersonalityPage frame={frame} onError={setError}/>:page==='notifications'?<NotificationsPage frame={frame} onError={setError}/>:<SettingsPage frame={frame} onError={setError}/>}
      </main>{!compact&&<footer className="status-footer"><span><span className="status-dot"/>{frame.busy?'TASK IN PROGRESS':'READY FOR YOUR NEXT THOUGHT'}</span><span>CYBER CYAN <i/> LOCAL CORE <i/> V2 · PHASE 06</span><span><Layers size={12}/> {frame.review?'1 PENDING REVIEW':'NO PENDING REVIEW'}</span></footer>}
    </div>{!compact&&<div className="emergency-dock" aria-label="Persistent emergency controls"><button title="Stop current and pending actions" onClick={()=>run(command('voice.stop',{}))}>STOP</button><button title="Mute microphone and stop pending work" onClick={()=>run(command('voice.mute',{muted:true}))}>MUTE</button></div>}
    {frame.review&&<Approval key={frame.review.id} review={frame.review} onError={setError}/>}
    {boot&&bootstrap&&!frame.review&&<Startup data={{...bootstrap,preferences:{...bootstrap.preferences,reduced_motion:bootstrap.preferences.reduced_motion||reduced}}} onFinish={()=>setBoot(false)}/>}
  </div>;
}
