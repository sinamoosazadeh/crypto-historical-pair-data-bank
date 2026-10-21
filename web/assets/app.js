(() => {
  'use strict';
  const DATA = window.CRYPTO_DATA_BANK || {sources:[],assets:[],timeframes:[],coverage:[],downloadResources:[],researchRows:0};
  const $ = (q, r=document) => r.querySelector(q);
  const $$ = (q, r=document) => [...r.querySelectorAll(q)];
  const state = { view:'overview', page:1, pageSize:25, sourcePage:1, toastTimer:null, coverageReady:false, coverageLoadPromise:null };
  const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const normalize = v => String(v ?? '').toLocaleLowerCase().normalize('NFKD');
  const labelStatus = s => {
    const v=normalize(s).replaceAll('_',' ');
    if(v==='verified') return ['PARTIAL EVIDENCE','state-doc'];
    if(v.includes('unverified') || v.includes('not confirmed') || v.includes('not checked') || v.includes('not measured') || v.includes('not tested')) return ['NOT CHECKED','state-muted'];
    if(v==='not_applicable' || v==='not applicable') return ['NOT APPLICABLE','state-muted'];
    if(v.includes('row') && v.includes('count')) return ['ROWS COUNTED','state-count'];
    if(v.includes('download verified')) return ['DOWNLOAD VERIFIED','state-pass'];
    if(v.includes('cross')) return ['CROSS-CHECKED','state-cross'];
    if(v.includes('inspected')) return ['INSPECTED','state-inspect'];
    if(v.includes('listing observed') || v.includes('listed')) return ['LISTED','state-list'];
    if(v.includes('documented')) return ['DOCUMENTED','state-doc'];
    if(v.includes('missing') || v.includes('failed')) return ['NOT CONFIRMED','state-muted'];
    if(!s) return ['NOT MEASURED','state-muted'];
    return [String(s).replaceAll('_',' '),'state-muted'];
  };
  function showToast(message){const t=$('#toast');if(!t)return;t.textContent=message;t.classList.add('show');clearTimeout(state.toastTimer);state.toastTimer=setTimeout(()=>t.classList.remove('show'),2400)}
  function go(view){if(!$('#view-'+view))return;state.view=view;state.page=1;$$('.view-panel').forEach(p=>p.classList.toggle('active',p.id==='view-'+view));$$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===view));const names={overview:'Overview',coverage:'Coverage explorer',sources:'Source registry',downloads:'Download directory',assets:'Asset universe',quality:'Evidence & quality'};$('#current-section').textContent=names[view]||'Overview';if(view==='coverage'&&!state.coverageReady)ensureCoverageLoaded();window.scrollTo({top:0,behavior:'smooth'});}
  $('#brand-home').addEventListener('click',event=>{event.preventDefault();go('overview')});
  $$('[data-view]').forEach(b=>b.addEventListener('click',()=>go(b.dataset.view)));
  $$('[data-go]').forEach(b=>b.addEventListener('click',()=>go(b.dataset.go)));
  const snapshotDate=DATA.generatedAt||'unknown';const snapshotDateObj=/^\d{4}-\d{2}-\d{2}$/.test(snapshotDate)?new Date(snapshotDate+'T00:00:00Z'):null;$('#snapshot-date').textContent=snapshotDateObj&&!Number.isNaN(snapshotDateObj.getTime())?new Intl.DateTimeFormat('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'}).format(snapshotDateObj):snapshotDate;$('#snapshot-label').textContent=DATA.snapshotLabel||'Metadata snapshot';
  $('#stat-sources').textContent=String(DATA.sources.length);$('#stat-assets').textContent=String(DATA.assets.length);$('#stat-coverage').textContent=Number(DATA.researchRows||DATA.coverage.length).toLocaleString('en-US');$('#stat-intervals').textContent=String(DATA.timeframes.length);
  $('#interval-cloud').innerHTML=DATA.timeframes.map(t=>`<span class="interval-chip">${safe(t.code)}<small>${safe(t.label||'')}</small></span>`).join('');
  function populate(select, vals){const uniq=[...new Set(vals.filter(v=>v!==null&&v!==undefined&&String(v).trim()!==''))].sort((a,b)=>String(a).localeCompare(String(b)));const first=select.options[0];select.innerHTML='';select.append(first);uniq.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v;select.append(o)});}
  const sourceById=Object.fromEntries(DATA.sources.map(s=>[s.source_id,s]));
  function populateCoverageFilters(){
    populate($('#filter-asset'),DATA.coverage.map(r=>r.asset));
    populate($('#filter-interval'),DATA.coverage.map(r=>r.interval));
    populate($('#filter-source'),DATA.sources.map(s=>s.source_id+' — '+s.name));
    populate($('#filter-status'),DATA.coverage.map(r=>r.status));
    populate($('#filter-market'),DATA.coverage.map(r=>r.market_type));
  }
  function ensureCoverageLoaded(){
    if(state.coverageReady)return Promise.resolve(true);
    if(state.coverageLoadPromise)return state.coverageLoadPromise;
    const body=$('#coverage-tbody');
    body.innerHTML='<tr><td colspan="7"><div class="empty-state"><strong>Loading coverage catalogue…</strong>The detailed coverage dataset is loaded on demand to keep the landing page lightweight.</div></td></tr>';
    state.coverageLoadPromise=new Promise(resolve=>{
      const script=document.createElement('script');
      script.src=new URL('web/assets/coverage-data.js',document.baseURI).toString();
      script.async=true;
      script.onload=()=>{
        DATA.coverage=Array.isArray(window.CRYPTO_COVERAGE_DATA)?window.CRYPTO_COVERAGE_DATA:[];
        if(!DATA.coverage.length){
          body.innerHTML='<tr><td colspan="7"><div class="empty-state"><strong>Coverage data unavailable</strong>The coverage bundle loaded but contained no records.</div></td></tr>';
          state.coverageLoadPromise=null;script.remove();showToast('Coverage data is empty.');resolve(false);return;
        }
        state.coverageReady=true;populateCoverageFilters();renderCoverage();script.remove();resolve(true);
      };
      script.onerror=()=>{
        body.innerHTML='<tr><td colspan="7"><div class="empty-state"><strong>Could not load coverage data</strong>Check that web/assets/coverage-data.js is present, then reload the page.</div></td></tr>';
        state.coverageLoadPromise=null;script.remove();showToast('Coverage data failed to load.');resolve(false);
      };
      document.head.append(script);
    });
    return state.coverageLoadPromise;
  }
  function coverageFiltered(){const search=normalize($('#coverage-search').value);const asset=$('#filter-asset').value,interval=$('#filter-interval').value,source=$('#filter-source').value,status=$('#filter-status').value,market=$('#filter-market').value;return DATA.coverage.filter(r=>{const src=sourceById[r.source_id]||{};const text=normalize([r.source_id,src.name,src.market_scope,r.market_type,r.asset,r.candidate_symbol,r.interval,r.status,src.eligibility_note,src.coverage_evidence_and_limits,src.access_mechanism].join(' '));return (!search||text.includes(search))&&(!asset||r.asset===asset)&&(!interval||r.interval===interval)&&(!source||(r.source_id+' — '+(src.name||''))===source)&&(!status||r.status===status)&&(!market||r.market_type===market)});}
  function renderCoverage(){
    if(!state.coverageReady)return;
    const filtered=coverageFiltered();
    const maxPage=Math.max(1,Math.ceil(filtered.length/state.pageSize));
    state.page=Math.min(state.page,maxPage);
    const start=(state.page-1)*state.pageSize;
    const rows=filtered.slice(start,start+state.pageSize);
    $('#coverage-result-count').textContent=filtered.length.toLocaleString('en-US');
    $('#coverage-page-label').textContent=filtered.length?`Showing ${start+1}–${Math.min(start+state.pageSize,filtered.length).toLocaleString('en-US')} of ${filtered.length.toLocaleString('en-US')}`:'Showing 0 rows';
    $('#page-number').textContent=`${state.page} / ${maxPage}`;
    $('#page-prev').disabled=state.page<=1;
    $('#page-next').disabled=state.page>=maxPage;
    const body=$('#coverage-tbody');
    if(!rows.length){body.innerHTML='<tr><td colspan="7"><div class="empty-state"><strong>No matching coverage records</strong>Change the filters or reset the search. No result is not proof that a dataset does not exist.</div></td></tr>';return}
    body.innerHTML=rows.map(r=>{
      const source=sourceById[r.source_id]||{};
      const status=labelStatus(r.status);
      const symbol=r.candidate_symbol||'—';
      const hasCount=r.published_candle_count!==null&&r.published_candle_count!==undefined&&String(r.published_candle_count)!=='';
      const isPublisher=String(r.count_basis||'').includes('PUBLISHER_REPORTED');
      let countHtml='<span class="count-na">Not measured</span>';
      if(hasCount){
        const countBasis=isPublisher?'Publisher-reported; not independently counted':'Count basis recorded in metadata';
        countHtml=`<span>${safe(Number(r.published_candle_count).toLocaleString('en-US'))}</span><small class="count-basis">${countBasis}</small>`;
      }
      const evidence=r.evidence_summary||source.coverage_evidence_and_limits||'No detailed evidence note recorded.';
      return `<tr>
        <td class="source-cell">${safe(source.name||r.source_id)}<small>${safe(r.source_id)}</small></td>
        <td><span class="pair-code">${safe(r.market_type||'market n/a')}</span><br><span class="mono">${safe(symbol)}</span></td>
        <td><span class="asset-tag">${safe(r.interval||'—')}</span><div style="font-size:8px;color:var(--subtle);margin-top:4px">${safe(r.interval_label||'')}</div></td>
        <td><span class="asset-tag">${safe(r.asset||'—')}</span></td>
        <td><span class="state-tag ${status[1]}">${safe(status[0])}</span><small class="count-basis">${safe(r.count_basis||'NOT_MEASURED').replaceAll('_',' ')}</small></td>
        <td>${countHtml}</td>
        <td><a class="evidence-link" title="${safe(evidence)}" href="${safe(source.landing_url||'#')}" target="_blank" rel="noreferrer">Open source ↗</a><details class="evidence-details"><summary>Evidence notes</summary><p>${safe(evidence)}</p></details></td>
      </tr>`;
    }).join('');
  }
  ['coverage-search','filter-asset','filter-interval','filter-source','filter-status','filter-market'].forEach(id=>$('#'+id).addEventListener(id==='coverage-search'?'input':'change',()=>{state.page=1;renderCoverage()}));$('#reset-filters').addEventListener('click',()=>{['coverage-search','filter-asset','filter-interval','filter-source','filter-status','filter-market'].forEach(id=>$('#'+id).value='');state.page=1;renderCoverage()});$('#page-prev').addEventListener('click',()=>{state.page--;renderCoverage()});$('#page-next').addEventListener('click',()=>{state.page++;renderCoverage()});
  function csvDownload(filename, rows){if(!rows.length){showToast('No rows to export.');return}const headers=[...new Set(rows.flatMap(r=>Object.keys(r)))];const quote=v=>{let s=String(v??'');return /[",\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s};const csv='\ufeff'+[headers.join(','),...rows.map(r=>headers.map(h=>quote(r[h])).join(','))].join('\r\n');const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url);showToast(`Exported ${rows.length.toLocaleString('en-US')} rows.`)}
  $('#export-coverage').addEventListener('click',()=>{const exportRows=coverageFiltered().map(r=>{const s=sourceById[r.source_id]||{};return {...r,source_name:s.name||'',source_landing_url:s.landing_url||'',direct_download_url:s.download_url||'',source_eligibility:s.eligibility_note||'',source_access_notes:s.access_mechanism||''}});csvDownload('crypto-data-bank-filtered-coverage.csv',exportRows)});
  function statusLabel(s){if(s==='qualified_candidate')return ['Qualified candidate','status-qualified'];if(s==='conditional')return ['Conditional','status-conditional'];return [s.replaceAll('_',' '),'status-other']}
  function sourceFiltered(){const q=normalize($('#source-search').value),status=$('#source-status-filter').value,type=$('#source-type-filter').value;return DATA.sources.filter(s=>{const text=normalize([s.name,s.source_id,s.provider,s.source_class,s.market_scope,s.schema_format,s.access_mechanism,s.eligibility_note,s.timeframes_note,s.free_access_classification,s.operational_status,s.evidence_level].join(' '));return (!q||text.includes(q))&&(!status||s.status===status)&&(!type||s.source_class===type)})}
  populate($('#source-type-filter'),DATA.sources.map(s=>s.source_class));
  function renderSources(){const rows=sourceFiltered();$('#source-result-count').textContent=rows.length;const root=$('#source-card-grid');if(!rows.length){root.innerHTML='<div class="empty-state">No sources match this filter.</div>';return}root.innerHTML=rows.map(s=>{const status=statusLabel(s.status);const levels=(s.data_levels||[]).slice(0,3).map(x=>`<span class="source-pill">${safe(x)}</span>`).join('');const fam=(s.data_families||[]).slice(0,3).map(x=>`<span class="source-pill">${safe(x)}</span>`).join('');return `<article class="source-card"><div class="source-card-head"><div><span class="source-id">${safe(s.source_id)}</span><h3>${safe(s.name)}</h3></div><span class="source-status ${status[1]}">${safe(status[0])}</span></div><p class="source-desc">${safe(s.coverage_evidence_and_limits||s.eligibility_note||'No scope notes recorded.')}</p><div class="source-meta">${fam}${levels}<span class="source-pill">${safe(s.confidence||'Confidence n/a')}</span></div><div style="font-size:9px;color:var(--muted);line-height:1.7;margin-bottom:12px"><b style="color:var(--text)">Access:</b> ${safe(s.access_mechanism||'Not recorded')}<br><b style="color:var(--text)">Market:</b> ${safe(s.market_scope||'Not recorded')}</div><div class="source-links"><a href="${safe(s.landing_url||'#')}" target="_blank" rel="noreferrer">Landing page ↗</a>${s.download_url?`<a href="${safe(s.download_url)}" target="_blank" rel="noreferrer">Archive / repo ↗</a>`:''}<a href="catalog/sources.json" download>Record JSON ↓</a></div></article>`}).join('')}
  ['source-search','source-status-filter','source-type-filter'].forEach(id=>$('#'+id).addEventListener(id==='source-search'?'input':'change',renderSources));
  const downloadResources = DATA.downloadResources || [];
  const downloadStatusLabel = value => ({
    static_download_candidate:'Static download candidate',
    file_verification_required:'Verify each file',
    community_archive_candidate:'Community archive candidate',
    unverified_public_root:'Public root not verified',
    access_not_verified:'Access not verified',
    conditional_or_excluded:'Conditional / excluded',
    complementary_not_pair_candles:'Complementary; not pair candles',
  }[value] || String(value || 'Needs review').replaceAll('_',' '));
  populate($('#download-access-filter'), downloadResources.map(r=>r.access_classification));
  populate($('#download-status-filter'), downloadResources.map(r=>r.eligibility_status));
  populate($('#download-family-filter'), downloadResources.map(r=>r.data_family));
  function downloadFiltered(){
    const query=normalize($('#download-search').value);
    const access=$('#download-access-filter').value;
    const status=$('#download-status-filter').value;
    const family=$('#download-family-filter').value;
    return downloadResources.filter(r=>{
      const haystack=normalize([r.resource_id,r.provider,r.resource_name,r.data_family,r.market_scope,r.access_classification,r.intervals_or_granularity,r.reported_coverage,r.evidence_state,r.license_or_terms,r.known_limitations,r.next_verification_step].join(' '));
      return (!query||haystack.includes(query))&&(!access||r.access_classification===access)&&(!status||r.eligibility_status===status)&&(!family||r.data_family===family);
    });
  }
  function renderDownloadResources(){
    const rows=downloadFiltered();
    $('#download-result-count').textContent=rows.length.toLocaleString('en-US');
    const root=$('#download-resource-grid');
    if(!rows.length){root.innerHTML='<div class="empty-state">No resource leads match the current filters.</div>';return;}
    root.innerHTML=rows.map(r=>{
      const accessLabel=downloadStatusLabel(r.eligibility_status);
      const family=safe(r.data_family||'Data family not recorded');
      const cadence=safe(r.intervals_or_granularity||'Not documented');
      const coverage=safe(r.reported_coverage||'No scope statement recorded');
      const limitations=safe(r.known_limitations||'No specific limitation recorded');
      const terms=safe(r.license_or_terms||'Terms not recorded');
      const next=safe(r.next_verification_step||'Review the exact artifact and access requirements.');
      const href=r.source_url||'';
      const index=r.direct_download_or_index_url||'';
      return `<article class="source-card resource-card"><div class="source-card-head"><div><span class="source-id">${safe(r.resource_id)} · ${safe(r.provider)}</span><h3>${safe(r.resource_name)}</h3></div><span class="source-status ${r.eligibility_status==='static_download_candidate'?'status-qualified':r.eligibility_status==='conditional_or_excluded'?'status-other':'status-conditional'}">${safe(accessLabel)}</span></div><div class="source-meta"><span class="source-pill">${family}</span><span class="source-pill">${safe(r.market_scope||'Market scope n/a')}</span></div><div class="resource-detail"><b>Access classification</b><span>${safe(r.access_classification)}</span><b>Intervals / granularity</b><span>${cadence}</span><b>Reported coverage</b><span>${coverage}</span><b>Evidence state</b><span>${safe(r.evidence_state||'Not recorded')}</span><b>Terms</b><span>${terms}</span></div><details class="evidence-details"><summary>Limitations and next verification</summary><p><b>Known limitations:</b> ${limitations}</p><p><b>Next step:</b> ${next}</p><p><b>Verification state:</b> ${safe(r.verification_state||'Not recorded')}. Snapshot date: ${safe(r.snapshot_date||DATA.generatedAt||'unknown')}.</p></details><div class="source-links">${href?`<a href="${safe(href)}" target="_blank" rel="noopener noreferrer">Source page ↗</a>`:''}${index?`<a href="${safe(index)}" target="_blank" rel="noopener noreferrer">Download / index ↗</a>`:''}<a href="catalog/download-resources.json" download>Record JSON ↓</a></div></article>`;
    }).join('');
  }
  ['download-search','download-access-filter','download-status-filter','download-family-filter'].forEach(id=>$('#'+id).addEventListener(id==='download-search'?'input':'change',renderDownloadResources));
  $('#reset-download-filters').addEventListener('click',()=>{['download-search','download-access-filter','download-status-filter','download-family-filter'].forEach(id=>$('#'+id).value='');renderDownloadResources();});
  $('#export-download-resources').addEventListener('click',()=>csvDownload('crypto-public-download-resource-leads.csv',downloadFiltered()));
  $('#export-assets').addEventListener('click',()=>csvDownload('crypto-data-bank-assets.csv',DATA.assets));
  $('#asset-grid').innerHTML=DATA.assets.map(a=>`<article class="asset-card"><div class="asset-top"><span class="asset-symbol">${safe(a.symbol)}</span><span class="asset-name"><b>${safe(a.name)}</b><small>${safe(a.asset_id)}</small></span></div><div class="asset-meta"><span>Mapping state</span><span>${safe((a.verification_state||'unverified').replaceAll('_',' '))}</span></div><div style="font-size:9px;color:var(--muted);margin-top:9px;line-height:1.6">${safe(a.notes||'')}</div></article>`).join('');
  $('#theme-toggle').addEventListener('click',()=>{const html=document.documentElement;const next=html.dataset.theme==='dark'?'light':'dark';html.dataset.theme=next;try{localStorage.setItem('crypto-bank-theme',next)}catch{}showToast(`${next==='dark'?'Dark':'Light'} theme enabled.`)});try{const saved=localStorage.getItem('crypto-bank-theme');if(saved)document.documentElement.dataset.theme=saved}catch{}
  renderSources();renderDownloadResources();
  if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) {
    navigator.serviceWorker.register(new URL('./sw.js', location.href).toString()).catch(() => { /* offline cache is optional */ });
  }
})();
