export function luminance(color:string){const values=color.slice(1).match(/../g)!.map(x=>parseInt(x,16)/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return values[0]*.2126+values[1]*.7152+values[2]*.0722;}
export function readableAccent(color:string){
  if(!/^#[0-9a-f]{6}$/i.test(color))return '#00d9ff';
  let output=color;
  for(let i=0;i<10&&(luminance(output)+.05)/(luminance('#102432')+.05)<4.5;i++)output='#'+output.slice(1).match(/../g)!.map(x=>Math.min(255,Math.round(parseInt(x,16)*.8+255*.2)).toString(16).padStart(2,'0')).join('');
  return output;
}
