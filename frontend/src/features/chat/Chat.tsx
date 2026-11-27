import {useEffect, useRef, useState} from 'react';
import {ArrowUp, CornerDownLeft, Copy, Plus, MessageSquare, LockKeyhole} from 'lucide-react';
import {command} from '../../services/bridge';
import {Panel} from '../../components/ui';
import type {Frame} from '../../types/bridge';

export function Chat({frame, onError, full = false}: {frame: Frame; onError: (error: string) => void; full?: boolean}) {
  const [text, setText] = useState(''), end = useRef<HTMLDivElement>(null), [copied, setCopied] = useState('');
  const last = frame.messages.at(-1)?.id;
  useEffect(() => {end.current?.scrollIntoView({behavior: frame.preferences.reduced_motion ? 'instant' : 'smooth', block: 'nearest'});}, [last, frame.preferences.reduced_motion]);
  const send = async () => {if (!text.trim() || frame.busy) return; try {await command('chat.send', {message: text.trim()}); setText('');} catch (e) {onError((e as Error).message);}};
  return <Panel title="Conversation" eyebrow="YOUR WORKING CONTEXT" className={`chat-panel ${full ? 'full-chat' : ''}`} action={<button className="icon-button" aria-label="Clear conversation context" disabled={frame.busy} onClick={() => void command('chat.clear', {}).catch(e => onError(e.message))}><Plus size={18}/></button>}>
    <div className="session-note"><LockKeyhole size={12}/>{frame.session?.temporary ? 'Temporary session · not saved' : frame.session?.title || 'Owned local session'}</div>
    <div className="messages" role="log" aria-label="Conversation messages" aria-live="polite">
      {!frame.messages.length && <div className="chat-empty"><div className="empty-glyph"><MessageSquare size={25}/></div><h3>Ready when you are.</h3><p>Ask a question. Think through an idea.<br/>Put a task in motion.</p><small>Every sensitive action stays under your control.</small></div>}
      {frame.messages.map(message => <article className={`message message-${message.role}`} key={message.id}><div className="message-role">{message.role === 'bot' ? 'CLYDEX' : message.role === 'user' ? 'YOU' : 'LOCAL STATUS'}
        <button className="icon-button" aria-label="Copy message" onClick={() => {void navigator.clipboard.writeText(message.text).then(() => setCopied(message.id)).catch(() => onError('Clipboard unavailable. Select and copy the text.'));}}><Copy size={12}/></button></div>
        <pre>{message.text}</pre>{copied === message.id && <small>Copied</small>}</article>)}
      {frame.busy && <div className="working"><span className="status-dot"/>{frame.review ? 'Waiting for your review' : frame.voice.state.replaceAll('_', ' ')}</div>}<div ref={end}/>
    </div>
    <form className="composer" onSubmit={e => {e.preventDefault(); void send();}}>
      <label className="sr-only" htmlFor="chat-input">Message CLYDEX</label><textarea id="chat-input" placeholder="What’s on your mind?" value={text} maxLength={16000} rows={2} onChange={e => setText(e.target.value)} onKeyDown={e => {if (e.key === 'Enter' && !e.shiftKey) {e.preventDefault(); void send();}}}/>
      <div><span><CornerDownLeft size={11}/> Send · Shift + Enter for a new line</span><button type="submit" className="send-button" disabled={!!frame.busy || !text.trim()} aria-label="Send message"><ArrowUp size={17}/></button></div>
    </form><p className="composer-note">Local tools first. Provider requests follow your privacy policy.</p>
  </Panel>;
}
