import {summaryNumber,rankingDotLayout} from './math.mjs?v=20261013-combined2';

const svgNS='http://www.w3.org/2000/svg';
function html(tag,className,parent,text){
  const element=document.createElement(tag);
  if(className)element.className=className;
  if(text!==undefined)element.textContent=text;
  if(parent)parent.append(element);
  return element;
}
function svg(tag,attributes,parent,text){
  const element=document.createElementNS(svgNS,tag);
  for(const [key,value] of Object.entries(attributes))element.setAttribute(key,String(value));
  if(text!==undefined)element.textContent=text;
  if(parent)parent.append(element);
  return element;
}

export function renderRankingCharts({container,rankings,labelFor,colorFor,onOpenLanguage,locTitle='LOC'}){
  container.replaceChildren();
  const extent=Math.max(3,Math.ceil(Math.max(rankings.speed.max_abs_sigma,rankings.loc.max_abs_sigma)));
  for(const [key,title,below,above] of [['speed','Speed','Faster','Slower'],['loc',locTitle,'Smaller','Larger']]){
    const metric=rankings[key],card=html('article','ranking-card',container);
    const referenceLanguage=metric.reference_language??null,referenceLabel=referenceLanguage===null?'Median':labelFor(referenceLanguage);
    card.dataset.rankingMetric=key;
    card.dataset.rankingMedian=String(metric.median);
    card.dataset.rankingReference=String(metric.reference??metric.median);
    if(referenceLanguage!==null)card.dataset.rankingReferenceLanguage=referenceLanguage;
    card.dataset.rankingLogSd=String(metric.log_sample_sd);
    html('h3','',card,title);
    html('p','ranking-metric-summary',card,metric.n?
      `${referenceLanguage===null?'Median':`${referenceLabel} = 0σ ·`} ${summaryNumber(metric.reference??metric.median)}× best${metric.log_sample_sd===0?' · zero log spread':''}`:
      'No eligible measured languages.');
    const directions=html('div','ranking-direction-labels',card);
    html('span','',directions,below);html('span','',directions,above);
    const width=Math.max(240,card.clientWidth||container.clientWidth||640),left=32,right=24;
    const plotWidth=width-left-right;
    const chart=svg('svg',{class:'ranking-chart',viewBox:`0 0 ${width} 100`,role:'group',
      'aria-label':`${title} distances from ${referenceLanguage===null?'the coordinate median':referenceLabel} in log₂ sample standard deviations`,
      'data-ranking-metric':key,'data-ranking-extent':extent},card);
    const labels=new Map(metric.entries.map(row=>{
      const node=svg('text',{class:'ranking-language-label',visibility:'hidden'},chart,labelFor(row.entry.language.key));
      return [row,{node,width:node.getBBox().width}];
    }));
    const labelOffset=9;
    const labelPosition=(row,x)=>{
      const labelWidth=labels.get(row).width;
      if(x+labelOffset+labelWidth<=plotWidth)
        return {anchor:'start',x:x+labelOffset,dy:0,start:x-4.5,end:x+labelOffset+labelWidth};
      if(x-labelOffset-labelWidth>=0)
        return {anchor:'end',x:x-labelOffset,dy:0,start:x-labelOffset-labelWidth,end:x+4.5};
      const labelX=Math.max(0,Math.min(x-labelWidth/2,plotWidth-labelWidth));
      return {anchor:'start',x:labelX,dy:-13,start:Math.min(x-4.5,labelX),end:Math.max(x+4.5,labelX+labelWidth)};
    };
    const layout=rankingDotLayout(metric.entries,{extent,width:plotWidth,gap:12,
      boundsFor:(row,x)=>{const label=labelPosition(row,x);return [label.start,label.end];}});
    const top=14,laneGap=28,plotHeight=Math.max(38,layout.lanes*laneGap+12),height=top+plotHeight+32;
    chart.setAttribute('viewBox',`0 0 ${width} ${height}`);
    chart.dataset.rankingLanes=String(layout.lanes);
    const X=z=>left+(z+extent)/(2*extent)*plotWidth;
    for(let band=-extent;band<extent;band++){
      const distance=Math.ceil(Math.abs(band+.5));
      svg('rect',{x:X(band),y:top,width:plotWidth/(2*extent),height:plotHeight,
        class:'ranking-sigma-band',fill:'var(--mech-surface-subtle)','fill-opacity':distance%2?.85:.35,
        'data-lower-sigma':band,'data-upper-sigma':band+1,'data-absolute-sigma-band':distance,
        'pointer-events':'none'},chart);
    }
    const tickStep=Math.max(1,Math.ceil(24*2*extent/plotWidth));
    for(let z=-extent;z<=extent;z++){
      svg('line',{x1:X(z),x2:X(z),y1:top,y2:top+plotHeight,
        class:z===0?'ranking-median-line':'ranking-tick-line',stroke:z===0?'var(--gold)':'var(--border)',
        'stroke-width':z===0?1.5:1,'stroke-dasharray':z===0?'0':'2 4','pointer-events':'none'},chart);
      const edge=Math.abs(z)===extent;
      if(z===0||edge||z%tickStep===0&&extent-Math.abs(z)>=tickStep)
        svg('text',{x:X(z),y:top+plotHeight+20,class:'ranking-axis-label','text-anchor':'middle'},chart,
          z===0?(referenceLanguage===null?'Median':'0σ'):`${z<0?'−':'+'}${Math.abs(z)}σ`);
    }
    const readout=html('div','ranking-readout',card);
    readout.setAttribute('role','status');readout.setAttribute('aria-live','polite');
    readout.setAttribute('aria-atomic','true');
    const languageButton=html('button','ranking-readout-language',readout,'Choose a language dot');
    languageButton.type='button';languageButton.disabled=true;
    const values=html('span','ranking-readout-values',readout,'Hover or focus a dot for values.');
    let selectedLanguage=null;
    languageButton.addEventListener('click',()=>{if(selectedLanguage!==null)onOpenLanguage(selectedLanguage);});
    for(const point of layout.points){
      const {row,lane}=point,language=row.entry.language.key,label=labelFor(language),color=colorFor(language);
      const coverage=row.entry.coverage;
      const partial=coverage&&coverage.measured<coverage.selected?` · ${coverage.measured}/${coverage.selected} benchmarks · partial`:'';
      const distance=`${summaryNumber(row.sigma_distance,{signed:true})}σ${referenceLanguage===null?'':` from ${referenceLabel}`}`;
      const description=`${label} · ${summaryNumber(row.value)}× best · ${distance}${partial}`;
      const y=top+10+lane*laneGap,labelPositioned=labelPosition(row,point.x);
      const mark=svg('g',{class:'ranking-mark',tabindex:0,role:'button',
        'aria-label':`${description}. Open language timings and sources.`,
        'data-ranking-language':language,'data-ranking-metric':key,'data-median-ratio':row.ratio_to_median,
        'data-sigma-distance':row.sigma_distance,'data-ranking-value':row.value,'data-ranking-lane':lane,
        'data-ranking-reference':language===referenceLanguage},chart);
      svg('circle',{cx:left+point.x,cy:y,r:4.5,fill:color,
        stroke:language===referenceLanguage?'var(--gold)':'var(--mech-surface-elevated)','stroke-width':language===referenceLanguage?2.5:1,class:'ranking-dot','aria-hidden':'true'},mark);
      const labelNode=labels.get(row).node;
      labelNode.setAttribute('x',left+labelPositioned.x);labelNode.setAttribute('y',y+labelPositioned.dy);
      labelNode.setAttribute('text-anchor',labelPositioned.anchor);labelNode.setAttribute('dominant-baseline','central');
      labelNode.setAttribute('aria-hidden','true');labelNode.removeAttribute('visibility');mark.append(labelNode);
      const show=()=>{
        selectedLanguage=language;languageButton.disabled=false;languageButton.textContent=label;
        languageButton.style.color=color;
        values.textContent=`${summaryNumber(row.value)}× best · ${distance}${partial}`;
      };
      const open=()=>onOpenLanguage(language);
      mark.addEventListener('pointerenter',show);mark.addEventListener('pointermove',show);mark.addEventListener('focus',show);
      mark.addEventListener('click',open);
      mark.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();open();}});
    }
  }
}
