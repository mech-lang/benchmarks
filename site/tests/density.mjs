import assert from 'node:assert/strict';
import {densityGrid} from '../src/math.mjs';

// Independent direct two-dimensional estimator. The optimized implementation
// must retain every observation, equal-position observations and remote tails.
function direct(points,domain,options={}){
  const {columns=48,rows=36,bandwidthCells=1.25}=options;
  const {xMin,xMax,yMin,yMax}=domain;
  const inputs=points.filter(point=>[point.x,point.y,point.weight].every(value=>Number.isFinite(value)&&value>0));
  const bx=(xMax-xMin)/columns*bandwidthCells,by=(yMax-yMin)/rows*bandwidthCells;
  return Array.from({length:rows*columns},(_,index)=>{
    const x=xMin+(index%columns+.5)*(xMax-xMin)/columns;
    const y=yMin+(Math.floor(index/columns)+.5)*(yMax-yMin)/rows;
    return inputs.reduce((sum,point)=>sum+point.weight*Math.exp(-.5*(
      ((x-Math.log2(point.x))/bx)**2+((y-Math.log2(point.y))/by)**2)),0)/(2*Math.PI*bx*by);
  });
}
const points=Array.from({length:103},(_,i)=>({
  x:2**((i*17%101)/10-2),y:2**((i*31%103)/8-3),weight:i%5+1,
  program:`program-${i%13}`,language:`language-${i%7}`,run:i+1
}));
points.push({...points[0],run:104},{...points[0],run:105});
const invalid=[{x:0,y:2,weight:1},{x:1,y:NaN,weight:1},{x:2,y:2,weight:0},{x:Infinity,y:1,weight:1}];
const cases=[
  {points:[],domain:{xMin:-.15,xMax:6,yMin:-.18,yMax:12}},
  {points:points.slice(0,1),domain:{xMin:-.15,xMax:6,yMin:-.18,yMax:12}},
  {points:[...points,...invalid],domain:{xMin:-.15,xMax:6,yMin:-.18,yMax:12}},
  {points,domain:{xMin:-12,xMax:20,yMin:-15,yMax:15},options:{columns:17,rows:11,bandwidthCells:.4}},
  {points,domain:{xMin:2,xMax:3,yMin:4,yMax:5},options:{columns:1,rows:1,bandwidthCells:4}},
  {points,domain:{xMin:-.2,xMax:10,yMin:-.3,yMax:11},options:{columns:120,rows:120,bandwidthCells:2}},
];
for(const item of cases){
  const before=JSON.stringify(item),field=densityGrid(item.points,item.domain,item.options);
  const expected=direct(item.points,item.domain,item.options);
  for(const [i,cell] of field.cells.entries()){
    assert.equal(cell.row,Math.floor(i/field.columns));assert.equal(cell.column,i%field.columns);
    assert.ok(Math.abs(cell.value-expected[i])<=Math.max(1e-300,Math.abs(expected[i])*2e-12),`Density cell ${i} changed: ${cell.value} vs ${expected[i]}`);
  }
  assert.equal(field.peak,Math.max(...field.cells.map(cell=>cell.value)));
  const eligible=item.points.filter(point=>[point.x,point.y,point.weight].every(value=>Number.isFinite(value)&&value>0));
  assert.equal(field.runs,eligible.length);
  assert.equal(field.total_sample_weight,eligible.reduce((sum,p)=>sum+p.weight,0));
  assert.equal(field.programs,new Set(eligible.map(p=>p.program)).size);
  assert.equal(field.variants,new Set(eligible.map(p=>p.language)).size);
  assert.equal(JSON.stringify(item),before);
}
console.log('Density: six independent estimator comparisons preserve all cells, observations, weights, metadata and inputs.');
