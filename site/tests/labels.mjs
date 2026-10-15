import assert from 'node:assert/strict';
import {createLabelPlacer} from '../src/labels.mjs';

// Independent copy of the prior exhaustive scoring formula: exact output,
// candidate ties and mobile crowding must survive the indexed search.
function referencePlacer({left,top,width,height,obstacles=[]}){
  const placed=[];
  const overlap=(a,b)=>Math.max(0,Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x))*Math.max(0,Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y));
  return (item,box)=>{
    const lw=box.width,lh=box.height;
    const vx=item.b.x-item.a.x,vy=item.b.y-item.a.y,length=Math.hypot(vx,vy);
    const nx=length>1?-vy/length:0,ny=length>1?vx/length:-1;
    let best=null;
    for(const t of [.5,.7,.3,.9,.1])for(const distance of [12,-12,23,-23,36,-36,51,-51]){
      const anchor={x:item.a.x+vx*t,y:item.a.y+vy*t};
      const center={x:anchor.x+nx*distance,y:anchor.y+ny*distance};
      for(const side of [0,1,-1]){
        const x=Math.max(left+2,Math.min(left+width-lw-2,center.x-lw/2+side*(lw/2+8)));
        const y=Math.max(top+2,Math.min(top+height-lh-2,center.y-lh/2));
        const candidate={x,y,width:lw,height:lh};
        const padded={x:x-3,y:y-2,width:lw+6,height:lh+4};
        const collisions=placed.reduce((sum,other)=>sum+overlap(padded,other),0);
        const marks=obstacles.reduce((sum,other)=>sum+overlap(padded,other),0);
        const offset=Math.hypot(x+lw/2-anchor.x,y+lh/2-anchor.y);
        const score=collisions*1000+marks*20+offset+Math.abs(t-.5)*5;
        if(!best||score<best.score)best={...candidate,score,padded,anchor,collisions};
      }
    }
    if(!(width<500&&best.collisions>0))placed.push(best.padded);
    return best;
  };
}

let seed=0x514f321a;
const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32;};
let checked=0;
for(const width of [190,290,499,500,900])for(const obstacleCount of [0,8,24,130]){
  const bounds={left:75,top:30,width,height:330,obstacles:Array.from({length:obstacleCount},()=>({
    x:random()*(width+180)-30,y:random()*450-30,width:random()*30,height:random()*30,
  }))};
  // Include a long rectangle spanning many cells and a fallback-sized one.
  if(obstacleCount){bounds.obstacles.push({x:-64,y:64,width:width+256,height:1/3});bounds.obstacles.push({x:-1e6,y:-1e6,width:2e6,height:1/7});}
  const saved=JSON.stringify(bounds),reference=referencePlacer(bounds),candidate=createLabelPlacer(bounds);
  for(let i=0;i<65;i++){
    const a={x:75+random()*width,y:30+random()*330};
    const item={a,b:i%7?{x:75+random()*width,y:30+random()*330}:a};
    const box={width:i%11?35+random()*180:width+25,height:i%13?11+random()*8:0};
    assert.deepEqual(candidate(item,box),reference(item,box),`Placement changed at width ${width}, obstacles ${obstacleCount}, label ${i}`);
    checked++;
  }
  assert.equal(JSON.stringify(bounds),saved,'Placement must not mutate input geometry.');
}
console.log(`Label placement: ${checked} exact exhaustive-oracle matches across mobile/desktop, crowding, ties, clipping and grid-boundary cases.`);
