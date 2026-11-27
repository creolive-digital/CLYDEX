import {describe,it,expect,vi} from 'vitest';
import {SoundEvents} from '../src/features/notifications/sounds';
import {frame} from './fixtures';

describe('private optional sound events',()=>{
  it('never initializes audio for muted defaults, lock or a background snapshot',()=>{
    const audio=vi.fn();vi.stubGlobal('AudioContext',audio);const manager=new SoundEvents();manager.update(frame());manager.unlock();expect(audio).not.toHaveBeenCalled();manager.update({...frame(),locked:true});manager.play('security');expect(audio).not.toHaveBeenCalled();manager.dispose();vi.unstubAllGlobals();
  });
  it('does not replay muted notification history after unmuting',()=>{
    const manager=new SoundEvents(),play=vi.spyOn(manager,'play');const notices=[{id:'old',code:'task.complete',message:'Completed',timestamp:1}];manager.update({...frame(),notifications:notices});manager.update({...frame(),preferences:{...frame().preferences,sounds_muted:false},notifications:notices});expect(play).not.toHaveBeenCalled();manager.update({...frame(),preferences:{...frame().preferences,sounds_muted:false},notifications:[...notices,{id:'new',code:'task.complete',message:'Completed',timestamp:2}]});expect(play).toHaveBeenCalledWith('completion');manager.dispose();
  });
});
