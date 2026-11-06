(() => {
  'use strict';
  const DATA = window.CRYPTO_DATA_BANK || {sources:[],assets:[],timeframes:[],coverage:[],downloadResources:[],researchRows:0};
  const $ = (q, root=document) => root.querySelector(q);
  const $$ = (q, root=document) => [...root.querySelectorAll(q)];
  const state = {view:'overview',page:1,pageSize:25,sourcePage:1,sourcePageSize:12,toastTimer:null,coverageReady:false,coverageLoadPromise:null,restoring:false,initialized:false};
  const names = {overview:'Overview',coverage:'Coverage explorer',sources:'Source registry',downloads:'Download directory',assets:'Asset universe',quality:'Evidence & quality'};
  const coverageControls = {'coverage-search':'q','filter-asset':'asset','filter-interval':'interval','filter-source':'source','filter-status':'status','filter-market':'market'};
  const sourceControls = {'source-search':'q','source-status-filter':'status','source-type-filter':'type'};
  const downloadControls = {'download-search':'q','download-access-filter':'access','download-status-filter':'status','download-family-filter':'family'};
  const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const normalize = value => String(value ?? '').toLocaleLowerCase().normalize('NFKD');
  const number = value => Number(value).toLocaleString('en-US');
  const externalUrl = value => {try {const u=new URL(String(value||''));return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password?u.href:'';} catch {return '';}};
  const sourceById = Object.fromEntries(DATA.sources.map(s=>[s.source_id,s]));
  const downloadResources = DATA.downloadResources || [];
  const labelStatus = value => {
    if(value==='VERIFIED') return ['PARTIAL EVIDENCE','state-doc'];
    if(value==='NOT_APPLICABLE') return ['NOT APPLICABLE','state-muted'];
    return ['NOT CHECKED','state-muted'];
  };
  const statusLabel = value => ({qualified_candidate:['Download candidate','status-qualified'],conditional:['Conditional','status-conditional'],needs_review:['Needs review','status-conditional'],out_of_scope_or_unverified:['Outside scope / unverified','status-other']}[value] || [String(value).replaceAll('_',' '),'status-other']);
  const downloadStatusLabel = value => ({static_download_candidate:'Static download candidate',file_verification_required:'Verify each file',community_archive_candidate:'Community archive candidate',unverified_public_root:'Public root not verified',access_not_verified:'Access not verified',conditional_or_excluded:'Conditional / excluded',complementary_not_pair_candles:'Complementary; not pair candles'}[value] || String(value||'Needs review').replaceAll('_',' '));

  function showToast(message) {const t=$('#toast');t.textContent=message;t.classList.add('show');clearTimeout(state.toastTimer);state.toastTimer=setTimeout(()=>t.classList.remove('show'),3200);}
  function readHash() {const raw=location.hash.slice(1);const match=raw.match(/^view-([a-z]+)(?:\?(.*))?$/);return {view:match&&names[match[1]]?match[1]:'overview',params:new URLSearchParams(match?.[2]||'')};}
  function writeHash(replace=false) {
    if(state.restoring||!state.initialized||(state.view==='coverage'&&!state.coverageReady))return;
    const controls=state.view==='coverage'?coverageControls:state.view==='sources'?sourceControls:state.view==='downloads'?downloadControls:{};
    const params=new URLSearchParams();
    Object.entries(controls).forEach(([id,key])=>{const value=$('#'+id).value;if(value)params.set(key,value);});
    if(state.view==='coverage'&&state.page>1)params.set('page',String(state.page));
    if(state.view==='sources'&&state.sourcePage>1)params.set('page',String(state.sourcePage));
    const hash='#view-'+state.view+(params.size?'?'+params.toString():'');
    if(location.hash!==hash)history[replace?'replaceState':'pushState'](null,'',hash);
  }
  function restoreControls() {
    if(state.view==='coverage'&&!state.coverageReady)return;
    const {params}=readHash();
    const controls=state.view==='coverage'?coverageControls:state.view==='sources'?sourceControls:state.view==='downloads'?downloadControls:{};
    Object.entries(controls).forEach(([id,key])=>{const el=$('#'+id);const value=params.get(key)||'';el.value=value;if(el.tagName==='SELECT'&&el.selectedIndex<0)el.value='';});
    const page=Math.max(1,Math.min(100000,parseInt(params.get('page'),10)||1));
    if(state.view==='coverage')state.page=page;
    if(state.view==='sources')state.sourcePage=page;
  }
  function go(view,force=false) {
    if(!$('#view-'+view))return;
    const changed=state.view!==view||force;
    state.view=view;
    $$('.view-panel').forEach(p=>{p.classList.toggle('active',p.id==='view-'+view);p.inert=p.id!=='view-'+view;});
    $$('[data-view]').forEach(link=>{const active=link.dataset.view===view;link.classList.toggle('active',active);if(active)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});
    $('#current-section').textContent=names[view];
    document.title=(view==='overview'?'PairAtlas — Historical crypto data':names[view]+' — PairAtlas');
    if(view==='coverage'&&!state.coverageReady)ensureCoverageLoaded();
    if(changed){restoreControls();renderCurrent();writeHash();window.scrollTo({top:0,behavior:'instant'});}
  }
  function renderCurrent() {if(state.view==='coverage')renderCoverage();if(state.view==='sources')renderSources();if(state.view==='downloads')renderDownloadResources();}
  $$('[data-view]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();go(link.dataset.view);}));
  $$('[data-go]').forEach(button=>button.addEventListener('click',()=>go(button.dataset.go)));
  $('#brand-home').addEventListener('click',event=>{event.preventDefault();go('overview');});
  window.addEventListener('hashchange',()=>{const {view}=readHash();if(view!==state.view)go(view);else{state.restoring=true;restoreControls();renderCurrent();state.restoring=false;}});

  const snapshot=DATA.generatedAt||'unknown';
  $('#snapshot-date').textContent=/^\d{4}-\d{2}-\d{2}$/.test(snapshot)?new Intl.DateTimeFormat('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'}).format(new Date(snapshot+'T00:00:00Z')):snapshot;
  $('#snapshot-label').textContent='Snapshot · '+snapshot+' · not live';
  $('#stat-sources').textContent=number(DATA.sources.length);$('#stat-assets').textContent=number(DATA.assets.length);$('#stat-coverage').textContent=number(DATA.researchRows);$('#stat-intervals').textContent=number(DATA.timeframes.length);
  $('#interval-cloud').innerHTML=DATA.timeframes.map(t=>`<button class="interval-chip" data-interval="${safe(t.code)}" title="Explore ${safe(t.label||t.code)} records">${safe(t.code)}</button>`).join('');
  $('#interval-cloud').addEventListener('click',event=>{const button=event.target.closest('[data-interval]');if(!button)return;go('coverage');$('#filter-interval').value=button.dataset.interval;state.page=1;renderCoverage();writeHash();});
  const summary=DATA.snapshotSummary?.coverageStatusCounts||{};
  const total=DATA.researchRows||1;
  if($('#evidence-meter')){
    const values=[['VERIFIED','Partial evidence','var(--amber)'],['NOT_CHECKED','Not checked','var(--line)'],['NOT_APPLICABLE','Not applicable','var(--subtle)']];
    $('#evidence-meter').innerHTML=values.map(([key,label,color])=>`<span style="width:${(summary[key]||0)/total*100}%;background:${color}" title="${label}: ${number(summary[key]||0)}"></span>`).join('');
    $('#evidence-legend').innerHTML=values.map(([key,label,color])=>`<button class="text-button" data-evidence="${key}"><span><i style="background:${color}"></i>${label}<b>${number(summary[key]||0)} <small>(${((summary[key]||0)/total*100).toFixed(1)}%)</small></b></span></button>`).join('');
    $('#evidence-legend').addEventListener('click',event=>{const button=event.target.closest('[data-evidence]');if(!button)return;go('coverage');$('#filter-status').value=button.dataset.evidence;state.page=1;renderCoverage();writeHash();});
  }
  function populate(select,values) {const first=select.options[0];select.innerHTML='';select.append(first);[...new Set(values.filter(v=>v!=null&&String(v).trim()))].sort((a,b)=>String(a).localeCompare(String(b))).forEach(value=>{const option=document.createElement('option');option.value=value;option.textContent=value;select.append(option);});}
  function populateCoverageFilters() {populate($('#filter-asset'),DATA.assets.map(a=>a.symbol));populate($('#filter-interval'),[...DATA.timeframes.map(t=>t.code),'UNRESOLVED']);populate($('#filter-source'),DATA.sources.map(s=>s.source_id));populate($('#filter-status'),Object.keys(summary));populate($('#filter-market'),DATA.coverage.map(r=>r.market_type));}
  function ensureCoverageLoaded() {
    if(state.coverageReady)return Promise.resolve(true);
    if(state.coverageLoadPromise)return state.coverageLoadPromise;
    const body=$('#coverage-tbody');
    body.innerHTML='<tr><td colspan="7"><div class="empty-state"><strong>Loading the evidence grid…</strong>The 10,458-row dataset loads only when you need it.</div></td></tr>';
    $('#export-coverage').disabled=true;
    state.coverageLoadPromise=new Promise(resolve=>{
      const script=document.createElement('script');script.src=new URL('web/assets/coverage-data.js',document.baseURI).href;script.async=true;
      const fail=message=>{body.innerHTML=`<tr><td colspan="7"><div class="empty-state"><strong>${safe(message)}</strong>No coverage results are available yet.<button class="secondary-button" id="retry-coverage">Retry loading</button></div></td></tr>`;$('#retry-coverage').onclick=()=>ensureCoverageLoaded();state.coverageLoadPromise=null;script.remove();resolve(false);};
      script.onload=()=>{DATA.coverage=Array.isArray(window.CRYPTO_COVERAGE_DATA)?window.CRYPTO_COVERAGE_DATA:[];if(!DATA.coverage.length){fail('Coverage data is empty.');return;}state.coverageReady=true;populateCoverageFilters();restoreControls();renderCoverage();$('#export-coverage').disabled=false;script.remove();resolve(true);};
      script.onerror=()=>fail('Could not load the coverage dataset.');document.head.append(script);
    });
    return state.coverageLoadPromise;
  }
  function coverageFiltered() {
    const query=normalize($('#coverage-search').value).trim();
    const asset=$('#filter-asset').value,interval=$('#filter-interval').value,source=$('#filter-source').value,status=$('#filter-status').value,market=$('#filter-market').value;
    return DATA.coverage.filter(r=>{const src=sourceById[r.source_id]||{};const text=normalize([r.source_id,src.name,r.market_type,r.asset,r.candidate_symbol,r.interval,r.status,src.eligibility_note,src.coverage_evidence_and_limits,src.access_mechanism].join(' '));return query.split(/\s+/).every(term=>text.includes(term))&&(!asset||r.asset===asset)&&(!interval||r.interval===interval)&&(!source||r.source_id===source)&&(!status||r.status===status)&&(!market||r.market_type===market);});
  }
  function emptyRow(message) {return `<tr><td colspan="7"><div class="empty-state"><strong>${safe(message)}</strong>Unknown does not mean unavailable. Try fewer filters.<button class="secondary-button" data-reset="coverage">Clear filters</button></div></td></tr>`;}
  function renderCoverage() {
    if(!state.coverageReady)return;
    const filtered=coverageFiltered(),maxPage=Math.max(1,Math.ceil(filtered.length/state.pageSize));state.page=Math.max(1,Math.min(state.page,maxPage));
    const start=(state.page-1)*state.pageSize,rows=filtered.slice(start,start+state.pageSize);
    $('#coverage-result-count').textContent=number(filtered.length);$('#coverage-page-label').textContent=filtered.length?`Showing ${number(start+1)}–${number(Math.min(start+state.pageSize,filtered.length))} of ${number(filtered.length)}`:'Showing 0 rows';
    $('#page-number').textContent=`${state.page} / ${maxPage}`;$('#page-prev').disabled=state.page<=1;$('#page-next').disabled=state.page>=maxPage;
    $('#coverage-tbody').innerHTML=rows.length?rows.map(r=>{
      const source=sourceById[r.source_id]||{},status=labelStatus(r.status),href=externalUrl(source.landing_url);
      const hasCount=r.published_candle_count!=null&&r.published_candle_count!=='';
      const publisher=String(r.count_basis||'').includes('PUBLISHER_REPORTED');
      const count=hasCount?`<span>${number(r.published_candle_count)}</span><small class="count-basis">${publisher?'Publisher-reported; not independently counted':'Count basis recorded in metadata'}</small>`:'<span class="count-na">Not measured</span>';
      const evidence=r.evidence_summary||source.coverage_evidence_and_limits||'No detailed evidence note recorded.';
      return `<tr><td class="source-cell">${safe(source.name||r.source_id)}<small>${safe(r.source_id)}</small></td><td><span class="pair-code">${safe(r.market_type||'Market not recorded')}</span><br><span class="mono">${safe(r.candidate_symbol||'Not resolved')}</span></td><td><span class="asset-tag">${safe(r.interval||'—')}</span><small class="count-basis">${safe(r.interval_label||'')}</small></td><td><span class="asset-tag">${safe(r.asset)}</span></td><td><span class="state-tag ${status[1]}">${status[0]}</span><small class="count-basis">${safe(r.count_basis||'NOT_MEASURED').replaceAll('_',' ')}</small></td><td>${count}</td><td>${href?`<a class="evidence-link" href="${safe(href)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>`:'<span class="count-na">No source URL recorded</span>'}<details class="evidence-details"><summary>Evidence notes</summary><p>${safe(evidence)}</p></details></td></tr>`;
    }).join(''):emptyRow('No matching evidence records');
    writeHash(true);
  }
  function resetControls(controls) {Object.keys(controls).forEach(id=>$('#'+id).value='');state.page=1;state.sourcePage=1;renderCurrent();writeHash();}
  Object.keys(coverageControls).forEach(id=>$('#'+id).addEventListener(id==='coverage-search'?'input':'change',()=>{state.page=1;renderCoverage();}));
  $('#reset-filters').addEventListener('click',()=>resetControls(coverageControls));
  $('#page-prev').addEventListener('click',()=>{state.page--;renderCoverage();});$('#page-next').addEventListener('click',()=>{state.page++;renderCoverage();});
  $('#coverage-tbody').addEventListener('click',event=>{if(event.target.closest('[data-reset]'))resetControls(coverageControls);});
  $('#copy-view-link').addEventListener('click',async()=>{writeHash(true);try{await navigator.clipboard.writeText(location.href);showToast('Filter link copied. It opens this same snapshot and query.');}catch{showToast('Copy the address from your browser to share these filters.');}});

  function fileDownload(filename,content,type) {const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}
  function csvDownload(filename,rows) {
    if(!rows.length){showToast('No rows to export.');return;}
    const headers=[...new Set(rows.flatMap(r=>Object.keys(r)))];
    const quote=value=>{let text=String(value??'');if(typeof value==='string'&&/^[\s]*[=+\-@\t\r]/.test(text))text="'"+text;return /[",\r\n]/.test(text)?'"'+text.replaceAll('"','""')+'"':text;};
    const csv='\ufeff'+[headers.join(','),...rows.map(r=>headers.map(h=>quote(r[h])).join(','))].join('\r\n');
    fileDownload(filename,csv,'text/csv;charset=utf-8;');showToast(`Exported ${number(rows.length)} rows. Raw JSON remains unchanged.`);
  }
  $('#export-coverage').addEventListener('click',()=>csvDownload('pairatlas-filtered-coverage.csv',coverageFiltered().map(r=>{const s=sourceById[r.source_id]||{};return {...r,source_name:s.name||'',source_landing_url:s.landing_url||'',source_download_url:s.download_url||'',source_eligibility:s.eligibility_note||'',source_access_notes:s.access_mechanism||''};})));

  populate($('#source-type-filter'),DATA.sources.map(s=>s.source_class));
  function sourceFiltered() {const query=normalize($('#source-search').value).trim(),status=$('#source-status-filter').value,type=$('#source-type-filter').value;return DATA.sources.filter(s=>{const text=normalize([s.name,s.source_id,s.provider,s.source_class,s.market_scope,s.schema_format,s.access_mechanism,s.eligibility_note,s.timeframes_note,s.free_access_classification,s.operational_status,s.evidence_level].join(' '));return query.split(/\s+/).every(term=>text.includes(term))&&(!status||s.status===status)&&(!type||s.source_class===type);});}
  function renderSources() {
    const rows=sourceFiltered(),maxPage=Math.max(1,Math.ceil(rows.length/state.sourcePageSize));state.sourcePage=Math.max(1,Math.min(state.sourcePage,maxPage));const start=(state.sourcePage-1)*state.sourcePageSize;
    $('#source-result-count').textContent=number(rows.length);$('#source-page-label').textContent=`${rows.length?start+1:0}–${Math.min(start+state.sourcePageSize,rows.length)} of ${rows.length} source routes`;$('#source-page-number').textContent=`${state.sourcePage} / ${maxPage}`;$('#source-prev').disabled=state.sourcePage<=1;$('#source-next').disabled=state.sourcePage>=maxPage;
    $('#source-card-grid').innerHTML=rows.length?rows.slice(start,start+state.sourcePageSize).map(s=>{
      const status=statusLabel(s.status),href=externalUrl(s.landing_url),download=externalUrl(s.download_url);
      const tags=[...(s.data_families||[]).slice(0,3),...(s.data_levels||[]).slice(0,2)].map(x=>`<span class="source-pill">${safe(x)}</span>`).join('');
      return `<article class="source-card"><div class="source-card-head"><div><span class="source-id">${safe(s.source_id)}</span><h3>${safe(s.name)}</h3></div><span class="source-status ${status[1]}">${safe(status[0])}</span></div><p class="source-desc">${safe(s.coverage_evidence_and_limits||s.eligibility_note||'No scope notes recorded.')}</p><div class="source-meta">${tags}</div><div class="source-access"><b>Access:</b> ${safe(s.access_mechanism||'Not recorded')}<br><b>Market:</b> ${safe(s.market_scope||'Not recorded')}</div><div class="source-links">${href?`<a href="${safe(href)}" target="_blank" rel="noopener noreferrer">Documentation ↗</a>`:''}${download?`<a href="${safe(download)}" target="_blank" rel="noopener noreferrer">Archive / endpoint ↗</a>`:''}<button class="text-button" data-source-json="${safe(s.source_id)}" aria-label="Download JSON record for ${safe(s.name)}">This record JSON ↓</button></div></article>`;
    }).join(''):'<div class="empty-state"><strong>No matching sources</strong>Try a provider name or clear the filters.<button class="secondary-button" data-reset="sources">Clear filters</button></div>';
    writeHash(true);
  }
  Object.keys(sourceControls).forEach(id=>$('#'+id).addEventListener(id==='source-search'?'input':'change',()=>{state.sourcePage=1;renderSources();}));
  $('#reset-source-filters').addEventListener('click',()=>resetControls(sourceControls));
  $('#source-prev').addEventListener('click',()=>{state.sourcePage--;renderSources();});$('#source-next').addEventListener('click',()=>{state.sourcePage++;renderSources();});
  $('#source-card-grid').addEventListener('click',event=>{if(event.target.closest('[data-reset]'))resetControls(sourceControls);const button=event.target.closest('[data-source-json]');if(button){const source=sourceById[button.dataset.sourceJson];fileDownload(source.source_id+'.json',JSON.stringify(source,null,2)+'\n','application/json');showToast('Downloaded this source record, not the entire registry.');}});
  $('#export-sources').addEventListener('click',()=>csvDownload('pairatlas-sources.csv',sourceFiltered()));

  populate($('#download-access-filter'),downloadResources.map(r=>r.access_classification));populate($('#download-status-filter'),downloadResources.map(r=>r.eligibility_status));populate($('#download-family-filter'),downloadResources.map(r=>r.data_family));
  function downloadFiltered() {const query=normalize($('#download-search').value).trim(),access=$('#download-access-filter').value,status=$('#download-status-filter').value,family=$('#download-family-filter').value;return downloadResources.filter(r=>{const text=normalize(Object.values(r).join(' '));return query.split(/\s+/).every(term=>text.includes(term))&&(!access||r.access_classification===access)&&(!status||r.eligibility_status===status)&&(!family||r.data_family===family);});}
  function renderDownloadResources() {
    const rows=downloadFiltered();$('#download-result-count').textContent=number(rows.length);
    $('#download-resource-grid').innerHTML=rows.length?rows.map(r=>{
      const href=externalUrl(r.source_url),index=externalUrl(r.direct_download_or_index_url);
      const details=[['Access classification',r.access_classification],['Intervals / granularity',r.intervals_or_granularity],['Reported coverage',r.reported_coverage],['Evidence state',r.evidence_state],['Terms',r.license_or_terms]].map(([key,value])=>`<b>${key}</b><span>${safe(value||'Not recorded')}</span>`).join('');
      return `<article class="source-card resource-card"><div class="source-card-head"><div><span class="source-id">${safe(r.resource_id)} · ${safe(r.provider)}</span><h3>${safe(r.resource_name)}</h3></div><span class="source-status status-conditional">${safe(downloadStatusLabel(r.eligibility_status))}</span></div><div class="source-meta"><span class="source-pill">${safe(r.data_family)}</span><span class="source-pill">${safe(r.market_scope)}</span></div><div class="resource-detail">${details}</div><details class="evidence-details"><summary>Limitations & next verification</summary><p><b>Known limitations:</b> ${safe(r.known_limitations)}</p><p><b>Next step:</b> ${safe(r.next_verification_step)}</p><p><b>State:</b> ${safe(r.verification_state)}. Snapshot: ${safe(r.snapshot_date)}.</p></details><div class="source-links">${href?`<a href="${safe(href)}" target="_blank" rel="noopener noreferrer">Source page ↗</a>`:''}${index?`<a href="${safe(index)}" target="_blank" rel="noopener noreferrer">Download / index ↗</a>`:''}<button class="text-button" data-resource-json="${safe(r.resource_id)}">This record JSON ↓</button></div></article>`;
    }).join(''):'<div class="empty-state"><strong>No matching download leads</strong>This directory is a curated supplement, not the complete source registry.<button class="secondary-button" data-reset="downloads">Clear filters</button></div>';
    writeHash(true);
  }
  Object.keys(downloadControls).forEach(id=>$('#'+id).addEventListener(id==='download-search'?'input':'change',renderDownloadResources));
  $('#reset-download-filters').addEventListener('click',()=>resetControls(downloadControls));
  $('#download-resource-grid').addEventListener('click',event=>{if(event.target.closest('[data-reset]'))resetControls(downloadControls);const button=event.target.closest('[data-resource-json]');if(button){const row=downloadResources.find(r=>r.resource_id===button.dataset.resourceJson);fileDownload(row.resource_id+'.json',JSON.stringify(row,null,2)+'\n','application/json');showToast('Downloaded one resource record.');}});
  $('#export-download-resources').addEventListener('click',()=>csvDownload('pairatlas-download-leads.csv',downloadFiltered()));
  $('#export-assets').addEventListener('click',()=>csvDownload('pairatlas-assets.csv',DATA.assets));
  $('#asset-grid').innerHTML=DATA.assets.map(a=>`<article class="asset-card"><div class="asset-top"><span class="asset-symbol">${safe(a.symbol)}</span><span class="asset-name"><b>${safe(a.name)}</b><small>${safe(a.asset_id)}</small></span></div><div class="asset-meta"><span>Mapping state</span><span>Scope only · not a listing</span></div><p class="asset-note">${safe(a.notes||'')}</p><button class="text-button" data-asset-go="${safe(a.symbol)}">Explore ${safe(a.symbol)} evidence →</button></article>`).join('');
  $('#asset-grid').addEventListener('click',event=>{const button=event.target.closest('[data-asset-go]');if(!button)return;go('coverage');$('#filter-asset').value=button.dataset.assetGo;state.page=1;renderCoverage();writeHash();});

  function setTheme(theme){document.documentElement.dataset.theme=theme;$('#theme-toggle').setAttribute('aria-label','Switch to '+(theme==='dark'?'light':'dark')+' theme');$('#theme-toggle').setAttribute('title','Switch to '+(theme==='dark'?'light':'dark')+' theme');try{localStorage.setItem('crypto-bank-theme',theme);}catch{}}
  $('#theme-toggle').addEventListener('click',()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark'));
  setTheme(document.documentElement.dataset.theme==='dark'?'dark':'light');
  document.addEventListener('keydown',event=>{if(event.key==='/'&&!event.ctrlKey&&!event.metaKey&&!event.altKey&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){const input=$('#view-'+state.view+' input[type="search"]');if(input){event.preventDefault();input.focus();}}});
  state.restoring=true;const initial=readHash();state.view=initial.view;restoreControls();state.restoring=false;state.initialized=true;
  renderSources();renderDownloadResources();go(initial.view,true);
  if('serviceWorker' in navigator&&/^https?:$/.test(location.protocol))navigator.serviceWorker.register(new URL('./sw.js',document.baseURI).href).catch(()=>{});
})();
