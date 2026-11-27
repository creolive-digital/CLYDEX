import {useEffect, useState} from 'react';
import {CircuitBoard, Shield, ArrowRight, FolderClock, KeyRound} from 'lucide-react';
import {useRead} from '../../hooks/useRead';
import {command, read} from '../../services/bridge';
import {ConfigFields} from '../../components/ConfigFields';
import {Panel, Field, Toggle, ErrorNotice, Refresh, Empty, ReviewButton, Loading} from '../../components/ui';
import type {Conversation, Frame, Json, Values} from '../../types/bridge';

const providerKeys = ['enabled','model','endpoint','allow_paid','local_only_confirmed','upstream','stream','timeout','max_request_bytes','max_response_bytes','max_output_tokens','retries','max_request_cost','input_price_per_million','output_price_per_million','task_types','api_version','workspace_id','token_parameter'];
const names: Record<string,string> = {codex:'Codex CLI',openai:'OpenAI',anthropic:'Claude',gemini:'Gemini',ollama:'Ollama',openrouter:'OpenRouter',custom:'Custom endpoint'};
export function IntelligencePage({frame, onError}: {frame: Frame; onError: (e: string) => void}) {
  const {data, error, refresh} = useRead('intelligence', frame.revision), [selected, setSelected] = useState('codex');
  const [provider, setProvider] = useState<Values>({}), [routing, setRouting] = useState<Values>({}), [secret,setSecret]=useState(''),[removeKey,setRemoveKey]=useState(false);
  const [tab,setTab]=useState('providers');
  useEffect(() => {if (data) {setProvider({...data.providers.find(p => p.id === selected)}); setRouting({...data.routing}); setSecret(''); setRemoveKey(false);}}, [data, selected]);
  const run = (work: Promise<void>) => {void work.catch(e => onError(e.message));};
  const changeProvider = (key: string,value: Json) => setProvider(p=>({...p,[key]:value}));
  const saveProvider = () => {
    const values = Object.fromEntries(providerKeys.filter(k=>k in provider).map(k=>[k,provider[k]])) as Values;
    const key = secret; setSecret(''); run(command('provider.configure',{name:selected,values,...(key?{secret:key}:{}),remove_key:removeKey}));
  };
  return <div className="page-stack"><div className="segmented" role="tablist" aria-label="Intelligence sections">{['providers','routing','history'].map(t=><button role="tab" aria-selected={tab===t} key={t} onClick={()=>setTab(t)}>{t === 'history' ? 'Conversation history' : t}</button>)}</div><ErrorNotice text={error}/><Loading active={!data&&!error}/>
    {tab==='providers' && <div className="provider-layout"><Panel title="Your intelligence network" eyebrow="SEVEN CONFIGURABLE ADAPTERS" action={<Refresh onClick={()=>void refresh()}/>}>{data?.providers.map(p=><button className={`provider-card ${selected===p.id?'selected':''}`} onClick={()=>setSelected(p.id)} key={p.id}><CircuitBoard size={19}/><span><b>{names[p.id]}</b><small>{p.status.replaceAll('_',' ')}</small></span><span className={`tag ${p.enabled?'':'muted-tag'}`}>{p.enabled?'ENABLED':'OFF'}</span></button>)}<p className="quiet-note">Availability is configured metadata. No startup request checks an account or runs inference.</p></Panel>
      <Panel title={names[selected]} eyebrow="PROVIDER CONFIGURATION"><p className="section-intro">Choose your model and limits. Every change is reviewed before applying.</p>
        <ConfigFields values={provider} keys={['enabled','model','endpoint','allow_paid',...(selected==='ollama'?['local_only_confirmed']:[]),...(selected==='openrouter'?['upstream']:[])]} readonly={['codex','openai','anthropic','gemini','openrouter'].includes(selected)?['endpoint']:[]} onChange={changeProvider}/>
        {!['codex','ollama'].includes(selected) && <div className="credential-box"><KeyRound size={17}/><div><Field label="Replace API key" hint="Stored only in Windows Credential Manager. Leave blank to keep the current key."><input type="password" autoComplete="new-password" maxLength={1280} value={secret} onChange={e=>setSecret(e.target.value)}/></Field><Toggle label="Remove stored key" checked={removeKey} onChange={setRemoveKey}/></div></div>}
        <details className="advanced"><summary>Limits and compatibility</summary><ConfigFields values={provider} keys={providerKeys.filter(k=>!['enabled','model','endpoint','allow_paid','local_only_confirmed','upstream'].includes(k))} onChange={changeProvider} choices={{token_parameter:['max_tokens','max_completion_tokens']}}/></details>
        <div className="form-actions"><ReviewButton disabled={frame.busy} onClick={saveProvider}>Review provider settings</ReviewButton><button className="button" disabled={frame.busy} onClick={()=>run(command('provider.check',{name:selected}))}>Review connection check<ArrowRight size={14}/></button></div>
        <p className="quiet-note">Connection checks contact the configured destination after approval. They do not prove successful inference. No key is returned to this screen.</p></Panel></div>}
    {tab==='routing' && <Panel title="The right route, under your control" eyebrow="HYBRID INTELLIGENCE" action={<Refresh onClick={()=>void refresh()}/> }><div className="security-banner"><Shield size={22}/><p>{data?.privacy_ceiling?'Startup privacy ceiling blocks cloud requests.':data?.cloud_allowed?'Cloud destinations still require outbound policy and action review.':'Startup policy blocks cloud requests.'}</p></div>
      <ConfigFields values={routing} keys={Object.keys(routing)} onChange={(k,v)=>setRouting(p=>({...p,[k]:v}))} choices={{selected:Object.keys(names),profile:['fast','balanced','advanced','offline']}}/>
      <p className="quiet-note">Profiles use the first eligible configured provider. Explicit fallbacks receive fresh review. Offline is local-only; changing a personality never grants permissions.</p><ReviewButton disabled={frame.busy} onClick={()=>run(command('routing.configure',{values:routing}))}>Review routing policy</ReviewButton></Panel>}
    {tab==='history' && <History frame={frame} onError={onError}/>}
  </div>;
}
export function History({frame,onError}:{frame:Frame;onError:(e:string)=>void}) {
  const {data:records,error,refresh,setData}=useRead('conversations',frame.revision);
  const [title,setTitle]=useState(''),[query,setQuery]=useState(''),[days,setDays]=useState(0),[exported,setExported]=useState('');
  const run=(work:Promise<void>)=>{void work.catch(e=>onError(e.message));};
  const manage=(operation:string,id='',persistent=false)=>run(command('conversation.manage',{values:{operation,id,title:title.trim()||'Saved conversation',persistent,days}}));
  return <Panel title="Your conversations" eyebrow="OWNED, ENCRYPTED HISTORY" action={<Refresh onClick={()=>void refresh()}/> }><ErrorNotice text={error}/><Loading active={!records&&!error}/><div className="history-summary"><FolderClock/><div><b>{frame.session?.temporary?'Temporary by default':frame.session?.title}</b><p>Only explicitly saved sessions persist. Sensitive tool/mail turns are excluded.</p></div></div>
    <div className="form-grid"><Field label="Conversation title"><input value={title} maxLength={120} onChange={e=>setTitle(e.target.value)}/></Field><Field label="Search recent history"><input value={query} maxLength={200} onChange={e=>setQuery(e.target.value)}/></Field></div>
    <div className="form-actions"><button className="button" disabled={frame.busy} onClick={()=>manage('new')}>New temporary</button><ReviewButton disabled={frame.busy} onClick={()=>manage('new','',true)}>Review saved conversation</ReviewButton><button className="button" onClick={()=>void read('conversations',{query}).then(setData).catch(e=>onError(e.message))}>Search</button></div>
    <div className="record-list">{records?.length?records.map((r:Conversation)=><article key={r.id} className="record"><div><h3>{r.title}</h3><small>{r.status} · {new Date(r.updated_at).toLocaleString()}</small></div><div className="record-actions"><button onClick={()=>run(command('conversation.resume',{id:r.id}))}>Resume</button>{['rename',r.status==='archived'?'unarchive':'archive','delete'].map(op=><button key={op} onClick={()=>manage(op,r.id)}>{op}</button>)}<button onClick={()=>void read('export',{id:r.id}).then(setExported).catch(e=>onError(e.message))}>Export</button></div></article>):records&&<Empty>No saved conversations. Temporary chat stays in memory.</Empty>}</div>
    <details className="advanced"><summary>Retention and export</summary><Field label="Retention days (0 disables automatic deletion)"><input type="number" min={0} max={3650} value={days} onChange={e=>setDays(Number(e.target.value))}/></Field><ReviewButton disabled={frame.busy} onClick={()=>manage('retention')}>Review retention and purge</ReviewButton><button className="button" onClick={()=>void read('export').then(setExported).catch(e=>onError(e.message))}>Export current session</button>{exported&&<Field label="Private JSON export · copy to your chosen location"><textarea readOnly rows={9} value={exported}/></Field>}<p className="quiet-note">Deletion cannot revoke backups or provider-held data. Lists are bounded; no automatic upload or export file.</p></details>
  </Panel>;
}
