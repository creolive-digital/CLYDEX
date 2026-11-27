import {describe,it,expect} from 'vitest';
import {validateFrame} from '../src/services/bridge';
import {contract,type CommandPayloads} from '../src/types/bridge';
import {DesktopStore} from '../src/stores/desktop';
import {frame} from './fixtures';
import {renderBudget} from '../src/features/avatar/renderer';
import {luminance,readableAccent} from '../src/themes/colors';
describe('desktop event/privacy contract',()=>{
  it('rejects incompatible or malformed audio instead of pretending to connect',()=>{expect(()=>validateFrame({version:4})).toThrow();expect(()=>validateFrame({...frame(),level:NaN})).toThrow();expect(()=>validateFrame({...frame(),bands:[Infinity]})).toThrow();});
  it('clears private cached messages and review on lock',()=>{const store=new DesktopStore();store.accept({...frame(),messages:[{id:'1',role:'user',text:'synthetic private text'}]});expect(store.getSnapshot().frame?.messages).toHaveLength(1);store.accept({...frame(),locked:true,messages:[{id:'2',role:'bot',text:'must not render'}]});expect(store.getSnapshot().frame?.messages).toEqual([]);expect(store.getSnapshot().frame?.review).toBeNull();store.stop();});
  it('uses the shared backend operation inventory',()=>{const known:Record<keyof CommandPayloads,true>={'chat.send':true,'chat.clear':true,'voice.capture':true,'voice.mute':true,'voice.stop':true,'voice.test':true,'voice.arm':true,'voice.configure':true,'voice.download':true,'personality.configure':true,'provider.configure':true,'provider.check':true,'routing.configure':true,'conversation.manage':true,'conversation.resume':true,'memory.manage':true,'memory.configure':true,'approval.decide':true,'display.mode':true,'display.monitor':true,'preferences.configure':true,'permissions.configure':true,'widget.action':true,'notifications.clear':true,'notifications.native_test':true,'startup.greet':true};expect(Object.keys(known).sort()).toEqual(Object.keys(contract.command).sort());expect(Object.keys(contract.command)).not.toContain('shell.run');});
});
describe('adaptive rendering and readable custom accents',()=>{
  it('suspends hidden/reduced-motion animation and constrains gaming/focus',()=>{const p=frame().preferences;expect(renderBudget(p,false,false)).toEqual({fps:0,particles:0});expect(renderBudget({...p,reduced_motion:true},true,false).fps).toBe(0);expect(renderBudget(p,true,true)).toEqual({fps:15,particles:60});});
  it('keeps foreground contrast at least 4.5:1 over the raised panel',()=>{for(const color of ['#000000','#123456','#ff0000','#00d9ff','#ffff00'])expect((luminance(readableAccent(color))+.05)/(luminance('#102432')+.05)).toBeGreaterThanOrEqual(4.5);});
});
