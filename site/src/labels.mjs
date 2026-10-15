// Keep the existing label candidates and scores, while testing overlap only
// against nearby rectangles. Summing matches in insertion order preserves the
// original floating-point result and the first-candidate tie rule.
const overlap=(a,b)=>Math.max(0,Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x))*Math.max(0,Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y));
const fractions=[.5,.7,.3,.9,.1],distances=[12,-12,23,-23,36,-36,51,-51],sides=[0,1,-1];

class RectangleIndex {
  constructor(rectangles=[]){
    this.rectangles=[];this.cells=new Map();this.unindexed=[];this.seen=[];this.epoch=0;
    for(const rectangle of rectangles)this.add(rectangle);
  }
  range(rectangle){
    const x0=Math.floor(rectangle.x/64),x1=Math.floor((rectangle.x+rectangle.width)/64);
    const y0=Math.floor(rectangle.y/64),y1=Math.floor((rectangle.y+rectangle.height)/64);
    if(![x0,x1,y0,y1].every(Number.isFinite)||x1<x0||y1<y0||(x1-x0+1)*(y1-y0+1)>4096)return null;
    return {x0,x1,y0,y1};
  }
  add(rectangle){
    const id=this.rectangles.length;this.rectangles.push(rectangle);
    const range=this.range(rectangle);
    if(!range){this.unindexed.push(id);return;}
    for(let y=range.y0;y<=range.y1;y++)for(let x=range.x0;x<=range.x1;x++){
      const key=`${x}:${y}`;
      if(!this.cells.has(key))this.cells.set(key,[]);
      this.cells.get(key).push(id);
    }
  }
  sum(rectangle){
    const range=this.range(rectangle);
    if(this.rectangles.length<=12||!range){
      let total=0;for(const other of this.rectangles)total+=overlap(rectangle,other);
      return total;
    }
    const hits=[],epoch=++this.epoch;
    const visit=ids=>{
      if(!ids)return;
      for(const id of ids){
        if(this.seen[id]===epoch)continue;
        this.seen[id]=epoch;
        const other=this.rectangles[id];
        if(rectangle.x>=other.x+other.width||other.x>=rectangle.x+rectangle.width||
          rectangle.y>=other.y+other.height||other.y>=rectangle.y+rectangle.height)continue;
        hits.push(id);
      }
    };
    for(let y=range.y0;y<=range.y1;y++)for(let x=range.x0;x<=range.x1;x++)visit(this.cells.get(`${x}:${y}`));
    visit(this.unindexed);
    hits.sort((a,b)=>a-b);
    let total=0;for(const id of hits)total+=overlap(rectangle,this.rectangles[id]);
    return total;
  }
}

export function createLabelPlacer({left,top,width,height,obstacles=[]}){
  const placed=new RectangleIndex(),marks=new RectangleIndex(obstacles);
  return (item,box)=>{
    const lw=box.width,lh=box.height;
    const vx=item.b.x-item.a.x,vy=item.b.y-item.a.y,length=Math.hypot(vx,vy);
    const nx=length>1?-vy/length:0,ny=length>1?vx/length:-1;
    let best=null;
    for(const t of fractions)for(const distance of distances){
      const anchor={x:item.a.x+vx*t,y:item.a.y+vy*t};
      const center={x:anchor.x+nx*distance,y:anchor.y+ny*distance};
      for(const side of sides){
        const x=Math.max(left+2,Math.min(left+width-lw-2,center.x-lw/2+side*(lw/2+8)));
        const y=Math.max(top+2,Math.min(top+height-lh-2,center.y-lh/2));
        const padded={x:x-3,y:y-2,width:lw+6,height:lh+4};
        const collisions=placed.sum(padded);
        // Every remaining score component is nonnegative. A candidate that
        // already ties or exceeds the best cannot win the strict comparison.
        if(best&&collisions*1000>=best.score)continue;
        const markOverlap=marks.sum(padded),base=collisions*1000+markOverlap*20;
        if(best&&base>=best.score)continue;
        const offset=Math.hypot(x+lw/2-anchor.x,y+lh/2-anchor.y);
        const score=base+offset+Math.abs(t-.5)*5;
        if(!best||score<best.score)best={x,y,width:lw,height:lh,score,padded,anchor,collisions};
      }
    }
    if(!(width<500&&best.collisions>0))placed.add(best.padded);
    return best;
  };
}
