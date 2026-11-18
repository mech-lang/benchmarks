let campaignsPromise,nativePromise;
const assetURL=name=>{const url=new URL('./'+name,import.meta.url);url.search=new URL(import.meta.url).search;return url;};
export function loadCampaigns() {
  if(!campaignsPromise)campaignsPromise=(async()=>{
    const compressed=typeof DecompressionStream==='function';
    const response=await fetch(assetURL(compressed?'campaigns.json.gz':'campaigns.json'));
    if(!response.ok)throw new Error(`Could not load task measurements (${response.status})`);
    const bundle=compressed&&response.headers.get('content-encoding')!=='gzip'
      ?await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).json():await response.json();
    if(!['mech.benchmark-dashboard.v1','mech.benchmark-dashboard.v2'].includes(bundle.schema))throw new Error('Unsupported task measurements');
    return bundle;
  })();
  return campaignsPromise;
}
export function validateNative(data) {
  if(data.schema!=='mech.deflate-results.v1'||data.cases?.length!==81||new Set(data.cases.map(row=>row.id)).size!==81)throw new Error('The compression result set is incomplete.');
  for(const order of ['forward','reverse']){
    if(data.cases.some(row=>!['ratio','mech_seconds','libdeflate_seconds'].every(key=>Number.isFinite(row.runs?.[order]?.[key])&&row.runs[order][key]>0)
      ||!['mech_output_bytes','libdeflate_output_bytes'].every(key=>Number.isSafeInteger(row[key])&&row[key]>0)))throw new Error('A compression measurement is missing.');
    if(data.cases.filter(row=>row.runs[order].ratio<1).length!==data.wins[order])throw new Error('The compression counts differ from the measurements.');
  }
  return data;
}
export function loadNative() {
  if(!nativePromise)nativePromise=(async()=>{
    const response=await fetch(assetURL('deflate-m3-results-20261118.json'));
    if(!response.ok)throw new Error('The compression results could not be loaded. The timing download remains available.');
    return validateNative(await response.json());
  })();
  return nativePromise;
}
