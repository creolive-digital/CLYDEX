import type {Frame} from '../src/types/bridge';
export function frame():Frame{return {version:1,locked:false,state:'READY',busy:false,recording:false,
  voice:{state:'standby',muted:true,locked:false,visible:true,background_armed:false,wake_capture_active:false,wake_status:'off',half_duplex:true,microphone_enabled:false},
  review:null,messages:[],notifications:[],revision:0,level:0,bands:[],wave:[],
  preferences:{theme:'cyber',accent:'#00d9ff',reduced_motion:false,animations:true,resource_saving:false,fps:30,particles:180,detail:'balanced',startup_animation:false,startup_sound:false,startup_greeting:false,sounds_muted:true,sound_volume:25,dnd:false,native_notifications:false},
  display:{mode:'window',visible:true,monitor:0,modes:['window','fullscreen','widget','floating','mini','tray'],monitors:[]},
  session:{title:'Temporary conversation',temporary:true},personality:'personal',language:'en'};}
