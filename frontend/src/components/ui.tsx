import {cloneElement, isValidElement, useId, useEffect, useRef, type ReactNode, type ReactElement} from 'react';
import {X, RefreshCw, ArrowUpRight} from 'lucide-react';

export function Panel({title, eyebrow, children, className = '', action}: {title?: string; eyebrow?: string; children: ReactNode; className?: string; action?: ReactNode}) {
  return <section className={`panel ${className}`}>{(title || eyebrow) && <header className="panel-heading"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}{title && <h2>{title}</h2>}</div>{action}</header>}{children}</section>;
}
export function Field({label, children, hint}: {label: string; children: ReactNode; hint?: string}) {
  const id=useId();
  return <div className="field"><label htmlFor={id}>{label}</label>{isValidElement(children)?cloneElement(children as ReactElement<Record<string,unknown>>, {id,'aria-describedby':hint?`${id}-hint`:undefined}):children}{hint&&<small id={`${id}-hint`}>{hint}</small>}</div>;
}
export function Toggle({label, checked, onChange, disabled = false}: {label: string; checked: boolean; onChange: (v: boolean) => void; disabled?: boolean}) {return <label className="toggle"><input type="checkbox" checked={checked} disabled={disabled} onChange={e => onChange(e.target.checked)}/><span>{label}</span></label>;}
export function Refresh({onClick}: {onClick: () => void}) {return <button className="icon-button" aria-label="Refresh current settings" onClick={onClick}><RefreshCw size={15}/></button>;}
export function Empty({children}: {children: ReactNode}) {return <p className="empty">{children}</p>;}
export function Loading({active}: {active: boolean}) {return active ? <p className="quiet-note" role="status">Reading local configuration…</p> : null;}
export function ErrorNotice({text}: {text: string}) {return text ? <p role="alert" className="error-notice">{text}</p> : null;}
export function ReviewButton({children = 'Review changes', onClick, disabled = false}: {children?: ReactNode; onClick: () => void; disabled?: boolean}) {return <button className="button primary" disabled={disabled} onClick={onClick}>{children}<ArrowUpRight size={14}/></button>;}
export function Dialog({title, children, onClose, critical = false}: {title: string; children: ReactNode; onClose?: () => void; critical?: boolean}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {const dialog = ref.current!; dialog.showModal(); dialog.querySelector<HTMLElement>('[data-initial-focus]')?.focus(); return () => {dialog.close();};}, []);
  return <dialog className={`modal ${critical ? 'security-modal' : ''}`} ref={ref} aria-label={title} onCancel={e => {e.preventDefault(); onClose?.();}}>
    <div className="modal-title"><h2>{title}</h2>{onClose && <button className="icon-button" onClick={onClose} aria-label="Close dialog"><X/></button>}</div>{children}</dialog>;
}
