import * as THREE from 'three';
import type {Preferences, VoiceState} from '../../types/bridge';

export interface AvatarSignal {state: VoiceState; amplitude: number; spectrum: number[]; playbackFrames?: number; sampleRate?: number | null; active: boolean; preferences: Preferences; constrained: boolean}
export interface AvatarRenderer {update(signal: AvatarSignal): void; dispose(): void; readonly frames: number}
export function renderBudget(p: Preferences, active: boolean, constrained: boolean): {fps: number; particles: number} {
  if (!active || !p.animations || p.reduced_motion) return {fps: 0, particles: 0};
  return {fps: constrained || p.resource_saving ? Math.min(15, p.fps) : p.fps,
    particles: constrained || p.resource_saving ? Math.min(60, p.particles) : p.particles};
}

/** Decorative holographic field only. It never constructs or substitutes a face. */
export class HologramField implements AvatarRenderer {
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(42, 1, .1, 100);
  private renderer: THREE.WebGLRenderer;
  private ring: THREE.LineLoop;
  private points: THREE.Points;
  private resize: ResizeObserver;
  private request = 0;
  private disposed = false;
  private last = 0;
  private signal: AvatarSignal;
  private lost: (event: Event) => void;
  frames = 0;
  constructor(private host: HTMLElement, initial: AvatarSignal, onLost: () => void) {
    this.signal = initial;
    this.renderer = new THREE.WebGLRenderer({alpha: true, antialias: false, powerPreference: 'low-power'});
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, initial.preferences.detail === 'high' ? 1.5 : 1));
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.domElement.setAttribute('aria-hidden', 'true');
    this.camera.position.z = 7;
    const positions = new Float32Array(500 * 3);
    for (let i = 0; i < 500; i++) {
      const a = i * 2.399963;
      const radius = 2 + (Math.sin(i * 91.7) + 1) * .6;
      positions[i * 3] = Math.cos(a) * radius;
      positions[i * 3 + 1] = Math.sin(a) * radius * 1.2;
      positions[i * 3 + 2] = Math.sin(i * 3.1) * .8;
    }
    const geometry = new THREE.BufferGeometry(); geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    this.points = new THREE.Points(geometry, new THREE.PointsMaterial({size: .018, color: initial.preferences.accent, transparent: true, opacity: .55}));
    this.scene.add(this.points);
    const ring = new THREE.BufferGeometry().setFromPoints(Array.from({length: 128}, (_, i) => new THREE.Vector3(Math.cos(i / 128 * Math.PI * 2) * 2.45, Math.sin(i / 128 * Math.PI * 2) * 2.45, 0)));
    this.ring = new THREE.LineLoop(ring, new THREE.LineBasicMaterial({color: initial.preferences.accent, transparent: true, opacity: .25}));
    this.ring.rotation.x = 1.15; this.ring.position.y = -2.1; this.scene.add(this.ring);
    this.host.append(this.renderer.domElement);
    this.lost = event => {event.preventDefault(); this.dispose(); onLost();};
    this.renderer.domElement.addEventListener('webglcontextlost', this.lost);
    this.resize = new ResizeObserver(() => this.size()); this.resize.observe(host); this.size();
    this.update(initial);
  }
  private size() {if (this.disposed) return; const {width, height} = this.host.getBoundingClientRect(); this.camera.aspect = width / Math.max(1, height); this.camera.updateProjectionMatrix(); this.renderer.setSize(width, height, false);}
  update(signal: AvatarSignal) {
    if (this.disposed) return;
    const previous = this.signal;
    this.signal = signal;
    const budget = renderBudget(signal.preferences, signal.active, signal.constrained);
    this.points.geometry.setDrawRange(0, budget.particles);
    (this.points.material as THREE.PointsMaterial).color.set(signal.preferences.accent);
    (this.ring.material as THREE.LineBasicMaterial).color.set(signal.preferences.accent);
    if (budget.fps > 0) {if (!this.request) this.request = requestAnimationFrame(this.tick);}
    else {
      cancelAnimationFrame(this.request); this.request = 0;
      if (signal.active && (!this.frames || previous.state !== signal.state || previous.preferences.accent !== signal.preferences.accent)) this.draw(0);
    }
  }
  private draw(now: number) {
    if (this.disposed) return;
    const level = Math.min(1, Math.max(0, this.signal.amplitude));
    const spectralEnergy = this.signal.spectrum.length ? Math.min(1, this.signal.spectrum.reduce((a,b)=>a+b,0)/this.signal.spectrum.length) : 0;
    (this.points.material as THREE.PointsMaterial).size = .018 + spectralEnergy * .035;
    this.points.rotation.y = now * .000025;
    this.ring.scale.setScalar(1 + level * .14);
    (this.points.material as THREE.PointsMaterial).opacity = .32 + level * .5;
    this.renderer.render(this.scene, this.camera); this.frames++;
    this.host.dataset.renderFrames = String(this.frames);
  }
  private tick = (now: number) => {
    if (this.disposed) return;
    const {fps} = renderBudget(this.signal.preferences, this.signal.active, this.signal.constrained);
    if (!fps) return;
    if (now - this.last >= 1000 / fps) {this.last = now; this.draw(now);}
    this.request = requestAnimationFrame(this.tick);
  };
  dispose() {
    if (this.disposed) return;
    this.disposed = true; cancelAnimationFrame(this.request); this.resize?.disconnect();
    this.renderer.domElement.removeEventListener('webglcontextlost', this.lost);
    this.points.geometry.dispose(); (this.points.material as THREE.Material).dispose();
    this.ring.geometry.dispose(); (this.ring.material as THREE.Material).dispose();
    this.renderer.dispose(); this.renderer.forceContextLoss(); this.renderer.domElement.remove();
  }
}
