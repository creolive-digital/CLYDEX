import {useSyncExternalStore} from 'react';
import {api, validateFrame} from '../services/bridge';
import type {Frame} from '../types/bridge';

export interface DesktopState {frame: Frame | null; connected: boolean; error: string; received: number}
export class DesktopStore {
  private state: DesktopState = {frame: null, connected: false, error: '', received: 0};
  private listeners = new Set<() => void>();
  private timer: ReturnType<typeof setTimeout> | undefined;
  private running = false;
  private generation = 0;
  subscribe = (listener: () => void) => {this.listeners.add(listener); return () => {this.listeners.delete(listener);};};
  getSnapshot = () => this.state;
  accept(value: unknown) {
    this.state = {frame: validateFrame(value), connected: true, error: '', received: performance.now()};
    this.listeners.forEach(x => x());
  }
  start() {
    if (this.running) return;
    this.running = true; const generation = ++this.generation;
    const poll = async () => {
      try {const value = await api().hud_snapshot(); if (this.running && generation === this.generation) this.accept(value);}
      catch (_) {
        if (this.running && generation === this.generation) {
          // Do not continue showing private/stale state after a bridge failure.
          this.state = {frame: null, connected: false, error: 'Desktop connection unavailable. Stop/mute remain native tray controls.', received: 0};
          this.listeners.forEach(x => x());
        }
      }
      if (this.running && generation === this.generation) this.timer = setTimeout(poll, document.hidden ? 1000 : 120);
    };
    void poll();
  }
  stop() {this.running = false; ++this.generation; clearTimeout(this.timer);}
}
export const desktop = new DesktopStore();
export const useDesktop = () => useSyncExternalStore(desktop.subscribe, desktop.getSnapshot);
