import {useEffect, useState} from 'react';
import {ShieldAlert, X, Check} from 'lucide-react';
import {command} from '../../services/bridge';
import {Dialog, ErrorNotice} from '../../components/ui';
import type {Review} from '../../types/bridge';

export function Approval({review, onError}: {review: Review; onError: (error: string) => void}) {
  const [remaining, setRemaining] = useState(review.expires_in), [error, setError] = useState('');
  useEffect(() => {const end = performance.now() + review.expires_in * 1000; const timer = setInterval(() => setRemaining(Math.max(0, Math.ceil((end - performance.now()) / 1000))), 250); return () => clearInterval(timer);}, [review.id]);
  let action: {tool?: string; target?: string; arguments?: unknown} = {};
  try {action = JSON.parse(review.script);} catch (_) { /* Raw exact snapshot remains visible. */ }
  const decide = async (approve: boolean) => {try {await command('approval.decide', {id: review.id, approve});} catch (e) {setError((e as Error).message); onError((e as Error).message);}};
  return <Dialog title="An action needs your approval" critical onClose={() => void decide(false)}><div className="security-banner"><ShieldAlert size={22}/><div><b>One action. One explicit decision.</b><p>Inspect the target and exact data before continuing.</p></div></div>
    <dl className="review-facts"><div><dt>Requested action</dt><dd>{action.tool || 'See exact action below'}</dd></div><div><dt>Target / destination</dt><dd>{action.target || 'See exact action below'}</dd></div><div><dt>Approval expires</dt><dd>{remaining} seconds</dd></div></dl>
    <p className="review-consequence">Provider actions transmit the displayed context to the destination. Operating actions may modify external applications or files. Stop prevents subsequent work; completed effects cannot be undone.</p>
    <p className="review-description">{review.description}</p><details open><summary>Exact arguments and data being transmitted</summary><pre className="exact-action" tabIndex={0}>{review.script}</pre></details><small className="digest">ACTION DIGEST {review.digest}</small><ErrorNotice text={error}/>
    <div className="dialog-actions"><button autoFocus data-initial-focus className="button" onClick={() => void decide(false)}><X size={15}/>Cancel action</button><button className="button primary" disabled={remaining <= 0} onClick={() => void decide(true)}><Check size={16}/>Approve once</button></div>
  </Dialog>;
}
