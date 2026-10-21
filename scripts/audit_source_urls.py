#!/usr/bin/env python3
"""Polite anonymous HTTP metadata probe for source catalogue URLs.

This tool sends no authentication, cookies or API keys. It checks only a small
range when HEAD is unavailable and never downloads or stores an entire archive.
It measures link/response behavior, not data completeness or redistribution rights.
"""
from __future__ import annotations
import argparse, json, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
USER_AGENT='CryptoPairHistoricalDataBank-LinkAudit/0.1 (+https://github.com/sinamoosazadeh/crypto-historical-pair-data-bank)'

def is_web_url(url: str) -> bool:
    p=urlparse(url)
    return p.scheme in {'http','https'} and bool(p.netloc)

def headers_snapshot(headers):
    want=('Content-Type','Content-Length','Content-Range','Accept-Ranges','Last-Modified','ETag','Location')
    return {k.lower().replace('-','_'):headers.get(k) for k in want if headers.get(k) is not None}

def attempt(url: str, method: str, timeout: float, sniff_bytes: int) -> dict:
    req=urllib.request.Request(url,method=method,headers={'User-Agent':USER_AGENT,'Range':f'bytes=0-{max(0,sniff_bytes-1)}'} if method=='GET' else {'User-Agent':USER_AGENT})
    opened=None
    try:
        opened=urllib.request.urlopen(req,timeout=timeout)
        status=getattr(opened,'status',opened.getcode())
        headers=headers_snapshot(opened.headers)
        final_url=opened.geturl()
        if not is_web_url(final_url):
            return {'http_status':status,'final_url':None,'error':'redirect ended at a non-HTTP(S) URL','response_headers':headers}
        sample_bytes=0
        if method=='GET': sample_bytes=len(opened.read(sniff_bytes))
        return {'http_status':status,'final_url':final_url,'response_headers':headers,'range_sample_bytes_read':sample_bytes,'error':None}
    except urllib.error.HTTPError as exc:
        return {'http_status':exc.code,'final_url':exc.geturl() if is_web_url(exc.geturl()) else None,'response_headers':headers_snapshot(exc.headers or {}),'range_sample_bytes_read':0,'error':f'HTTPError: {exc.code}'}
    except Exception as exc:
        return {'http_status':None,'final_url':None,'response_headers':{},'range_sample_bytes_read':0,'error':f'{type(exc).__name__}: {exc}'}
    finally:
        if opened is not None:
            try: opened.close()
            except Exception: pass

def probe(url: str, timeout: float=12, sniff_bytes: int=4096) -> dict:
    checked=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
    base={'requested_url':url,'checked_at_utc':checked,'auth_sent':False,'api_key_sent':False,'purpose':'anonymous link metadata probe only'}
    if not is_web_url(url):
        return base|{'result':'invalid_url','error':'Only http/https URLs are supported.'}
    head=attempt(url,'HEAD',timeout,sniff_bytes)
    # A failed or unsupported HEAD request is followed by a bounded GET range.
    if head.get('http_status') in (400,403,405,501) or head.get('http_status') is None:
        get=attempt(url,'GET',timeout,sniff_bytes)
        result={'head':head,'get_range':get}
        if get.get('http_status') in (200,206): outcome='http_reachable_range_response'
        elif get.get('http_status') in (401,403): outcome='access_restricted_or_denied'
        elif get.get('http_status')==404: outcome='not_found'
        else: outcome='inconclusive_or_failed'
    else:
        result={'head':head}
        st=head.get('http_status')
        if st and 200<=st<400: outcome='http_head_reachable'
        elif st in (401,403): outcome='access_restricted_or_denied'
        elif st==404: outcome='not_found'
        else: outcome='inconclusive_or_failed'
    return base|{'result':outcome,'responses':result,'warning':'A reachable landing page does not prove an anonymous file download, complete coverage, or redistribution rights.'}

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--registry',default='catalog/sources.json')
    p.add_argument('--output',default='source_url_observations.jsonl')
    p.add_argument('--source-id',action='append',default=[])
    p.add_argument('--timeout',type=float,default=12)
    p.add_argument('--delay',type=float,default=1.0,help='Seconds between requested URLs')
    p.add_argument('--sniff-bytes',type=int,default=4096)
    p.add_argument('--include-landing',action='store_true',help='Also probe landing/documentation pages (default probes download_url only)')
    args=p.parse_args()
    if args.timeout<=0 or args.delay<0 or args.sniff_bytes<1: p.error('timeout/sniff-bytes must be positive and delay nonnegative')
    registry=json.loads((ROOT/args.registry).read_text(encoding='utf-8'))
    sources=registry.get('sources',[])
    if args.source_id:
        sources=[s for s in sources if s.get('source_id') in set(args.source_id)]
        missing=set(args.source_id)-{s.get('source_id') for s in sources}
        if missing: p.error('Unknown source ids: '+', '.join(sorted(missing)))
    urls=[]
    for s in sources:
        if s.get('download_url'): urls.append((s.get('source_id'),s.get('name'), 'download_url',s['download_url']))
        elif args.include_landing and s.get('landing_url'): urls.append((s.get('source_id'),s.get('name'),'landing_url',s['landing_url']))
        if args.include_landing and s.get('landing_url'): urls.append((s.get('source_id'),s.get('name'),'landing_url',s['landing_url']))
    # Deduplicate exact source/URL pair while retaining a stable order.
    uniq=[]; seen=set()
    for item in urls:
        if (item[0],item[3]) not in seen: uniq.append(item);seen.add((item[0],item[3]))
    out=ROOT/args.output
    with out.open('w',encoding='utf-8') as f:
        for idx,(sid,name,field,url) in enumerate(uniq):
            row=probe(url,args.timeout,args.sniff_bytes)|{'source_id':sid,'source_name':name,'registry_field':field}
            f.write(json.dumps(row,ensure_ascii=False)+'\n');f.flush()
            print(f'[{idx+1}/{len(uniq)}] {sid} {field}: {row.get("result")}')
            if idx+1<len(uniq): time.sleep(args.delay)
    print(f'Wrote {len(uniq)} observations to {out.relative_to(ROOT)}')
    return 0
if __name__=='__main__': raise SystemExit(main())
