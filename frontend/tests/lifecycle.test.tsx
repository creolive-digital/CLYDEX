import {describe,it,expect,vi,afterEach} from 'vitest';
import {render,screen,waitFor} from '@testing-library/react';
import {DesktopStore} from '../src/stores/desktop';
import {frame} from './fixtures';
const graphics=vi.hoisted(()=>({dispose:vi.fn(),update:vi.fn(),fallback:null as null|(()=>void)}));
vi.mock('../src/features/avatar/renderer',()=>({HologramField:class{constructor(_host:unknown,_signal:unknown,fallback:()=>void){graphics.fallback=fallback;}dispose=graphics.dispose;update=graphics.update;}}));
import {Avatar} from '../src/features/avatar/Avatar';
import {Startup} from '../src/app/App';
afterEach(()=>{vi.useRealTimers();});
describe('lifecycle and privacy',()=>{
  it('finishes startup despite continuous cloned bridge preferences',async()=>{
    vi.useFakeTimers();const onFinish=vi.fn();const data={version:1,initialization:[],preferences:{...frame().preferences,startup_animation:true},display:frame().display};
    const view=render(<Startup data={data} onFinish={onFinish}/>);
    const {act}=await import('@testing-library/react');
    for(let i=0;i<20;i++){await act(async()=>{await vi.advanceTimersByTimeAsync(100);});view.rerender(<Startup data={{...data,preferences:{...data.preferences}}} onFinish={onFinish}/>);}
    expect(onFinish).toHaveBeenCalledTimes(1);
  });
  it('ignores an in-flight snapshot after stop; repeated starts do not duplicate polling',async()=>{
    let resolve:(value:unknown)=>void=()=>{};const snapshot=vi.fn(()=>new Promise(r=>{resolve=r;}));
    window.pywebview={api:{hud_snapshot:snapshot,hud_read:vi.fn(),hud_command:vi.fn()}};
    const store=new DesktopStore();store.start();store.start();expect(snapshot).toHaveBeenCalledTimes(1);store.stop();resolve(frame());await Promise.resolve();expect(store.getSnapshot().frame).toBeNull();
  });
  it('erases private visible data after a failed bridge poll',async()=>{
    vi.useFakeTimers();window.pywebview={api:{hud_snapshot:vi.fn().mockRejectedValue(new Error('unavailable')),hud_read:vi.fn(),hud_command:vi.fn()}};
    const store=new DesktopStore();store.accept({...frame(),messages:[{id:'private',role:'user',text:'synthetic secret'}]});store.start();await vi.advanceTimersByTimeAsync(1);expect(store.getSnapshot()).toMatchObject({frame:null,connected:false});store.stop();
  });
  it('disposes graphics on navigation and retains the approved reference on context loss',async()=>{
    graphics.dispose.mockClear();const view=render(<Avatar frame={frame()}/>);await waitFor(()=>expect(graphics.fallback).toBeTypeOf('function'));
    const {act}=await import('@testing-library/react');await act(async()=>graphics.fallback?.());expect(screen.getByText(/WebGL unavailable/)).toBeVisible();expect(screen.getByAltText(/Owner-approved masculine/)).toBeVisible();view.unmount();expect(graphics.dispose).toHaveBeenCalledTimes(1);
  });
});
