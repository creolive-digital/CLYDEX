import {Bell, Check, ShieldAlert, CircleAlert} from 'lucide-react';
import {Panel, Empty} from '../../components/ui';
import {command} from '../../services/bridge';
import type {Frame} from '../../types/bridge';

export function NotificationsPage({frame,onError}:{frame:Frame;onError:(e:string)=>void}) {
  return <Panel title="Your signal, without the noise" eyebrow="NOTIFICATION CENTER" action={<button className="button" onClick={()=>void command('notifications.clear',{}).catch(e=>onError(e.message))}>Clear history</button>}>
    <p className="section-intro">Local status only. The latest 100 notices stay in memory and are cleared on lock. Private prompts, task arguments and mail content never appear here.</p>
    {!frame.notifications.length&&<Empty>You’re all caught up. New local events will appear here.</Empty>}
    <div className="notification-list">{[...frame.notifications].reverse().map(n=><article className={`notification notice-${n.code.replace('.','-')}`} key={n.id}><span className="notice-icon">{n.code.includes('approval')?<ShieldAlert size={18}/>:n.code.includes('error')?<CircleAlert size={18}/>:n.code==='task.complete'?<Check size={18}/>:<Bell size={18}/>}</span><div><p>{n.message}</p><small>{new Date(n.timestamp*1000).toLocaleTimeString()} · {n.code}</small></div></article>)}</div>
  </Panel>;
}
