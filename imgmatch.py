#!/usr/bin/env python3
"""
Image Match Search - Find Instagram accounts using the same picture (>= 80% match)
Part of Instagram OSINT v5 | Author: n5za
"""

import io
import os
import re
import json
import time
import hashlib
import urllib.parse
from datetime import datetime

import requests
import numpy as np
from PIL import Image

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'
MATCH_THRESHOLD = 0.80


class C:
    H = '\033[95m'; B = '\033[94m'; G = '\033[92m'
    W = '\033[93m'; F = '\033[91m'; E = '\033[0m'; BO = '\033[1m'


def log(msg='', color=C.E):
    print(f"  {color}{msg}{C.E}")


def fetch(url, session=None, timeout=25, headers=None):
    s = session or requests
    h = {'User-Agent': UA}
    if headers:
        h.update(headers)
    r = s.get(url, headers=h, timeout=timeout)
    r.raise_for_status()
    return r


def phash(img_bytes):
    """Perceptual hash (64-bit) for similarity detection."""
    img = Image.open(io.BytesIO(img_bytes)).convert('L').resize((32, 32), Image.LANCZOS)
    a = np.asarray(img, dtype=np.float64)
    dct = np.fft.fft2(a)
    top = dct[:8, :8]
    avg = top.mean()
    bits = (top > avg).flatten()
    return ''.join('1' if b else '0' for b in bits)


def hamming(h1, h2):
    return sum(c1 != c2 for c1, c2 in zip(h1, h2))


def similarity(h1, h2):
    return 1 - hamming(h1, h2) / 64


def sanitize_ig_url(image_url):
    """Strip volatile CDN tokens so search engines can index/match the URL."""
    p = urllib.parse.urlparse(image_url)
    params = urllib.parse.parse_qsl(p.query)
    stable = [(k, v) for k, v in params
              if k not in ('_nc_oc', '_nc_ohc', '_nc_gid', '_nc_sid', 'edm',
                           '_nc_zt', 'oh', 'oe', 'ccb', 'efg', 'sep', 'efg',
                           '_nc_rid', '_nc_ab', 'ig_cache_key')]
    return urllib.parse.urlunparse(p._replace(query=urllib.parse.urlencode(stable)))


def bing_search(image_url, session):
    enc = urllib.parse.quote(image_url, safe='')
    r = session.get(
        f'https://www.bing.com/images/search?q=imgurl%3A{enc}&form=HDRSC2', timeout=25)
    murls = re.findall(r'murl&quot;:&quot;(.*?)&quot;', r.text)
    turls = re.findall(r'turl&quot;:&quot;(.*?)&quot;', r.text)
    page_urls = re.findall(r'purl&quot;:&quot;(.*?)&quot;', r.text)
    return murls + turls + page_urls


def text_query_search(image_url, session):
    """Text queries on the unique photo id / filename - catches repost pages."""
    base = os.path.basename(urllib.parse.urlparse(image_url).path)
    photo_id = re.sub(r'\.(jpg|jpeg|png|webp)$', '', base)
    queries = [base, photo_id]
    found = []
    for q in queries:
        if not q:
            continue
        for url in (
            f'https://www.bing.com/search?q={urllib.parse.quote(q)}%20instagram',
            f'https://duckduckgo.com/html/?q={urllib.parse.quote(q)}%20instagram',
        ):
            try:
                r = session.get(url, timeout=20)
                found += re.findall(r'https?://[^\s"\'<>]+', r.text)
            except Exception:
                pass
    return found


def google_search(image_url, session):
    """Google Images by-URL search; may hit captcha but often yields IG links."""
    enc = urllib.parse.quote(image_url, safe='')
    try:
        r = session.get(
            f'https://www.google.com/searchbyimage?image_url={enc}&safe=off', timeout=25)
        if r.status_code != 200 or 'captcha' in r.text.lower():
            return []
        page_urls = re.findall(r'href="(https?://[^"]+)"', r.text)
        return [u for u in page_urls if 'google' not in u]
    except Exception:
        return []


def duckduckgo_search(image_url, session):
    q = urllib.parse.quote(image_url, safe='')
    try:
        html = session.get(
            f'https://duckduckgo.com/?q={q}&iax=images&ia=images', timeout=25).text
        m = re.search(r'vqd[=:]["\']([0-9\-]+)["\']', html)
        if not m:
            return []
        j = session.get(
            f'https://duckduckgo.com/i.js?q={q}&vqd={m.group(1)}&o=json', timeout=25).json()
        urls = []
        for res in j.get('results', []):
            urls.append(res.get('url', ''))
            urls.append(res.get('image', ''))
        return urls
    except Exception:
        return []


def extract_instagram_accounts(urls, exclude=None):
    users = set()
    for u in urls:
        if 'instagram.com' not in u:
            continue
        u = u.replace('\\u0026', '&').replace('\\/', '/')
        m = re.search(r'instagram\.com/(?:[A-Za-z0-9_.]*/)?([A-Za-z0-9_.]{2,30})', u)
        if not m:
            continue
        name = m.group(1)
        if name in ('p', 'reel', 'tv', 'explore', 'accounts', 'stories', 'discover',
                    'direct', 'directory', 'legal', 'about', 'help', 'api'):
            continue
        users.add(name.lower())
    if exclude:
        users.discard(exclude.lower())
    return sorted(users)


def instagram_profile_pic(username, cookies_file='acc.txt'):
    """Get profile pic URL + hd version via Instagram web API."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': UA,
        'X-IG-App-ID': '936619743392459',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'https://www.instagram.com/{username}/',
    })
    if os.path.exists(cookies_file):
        with open(cookies_file) as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    k, v = line.split('=', 1)
                    session.cookies.set(k, v, domain='.instagram.com')
    r = session.get(
        f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}', timeout=20)
    if r.status_code != 200:
        return None
    data = r.json()
    user = data.get('data', {}).get('user', {})
    return user.get('profile_pic_url_hd') or user.get('profile_pic_url')


def match_image(image_url, cookies_file='acc.txt', max_results=25):
    log(f"Target image: {image_url}", C.G)
    src_bytes = fetch(image_url).content
    src_hash = phash(src_bytes)
    log(f"Source pHash: {src_hash}", C.B)
    log(f"Searching Bing + DuckDuckGo + Google...", C.B)
    session = requests.Session()
    session.headers.update({
        'User-Agent': UA,
        'Referer': 'https://www.bing.com/',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    results = []
    search_urls = [image_url]
    sanitized = sanitize_ig_url(image_url)
    if sanitized != image_url:
        search_urls.append(sanitized)
        log(f"[*] Also searching with sanitized URL (stable CDN link)", C.W)

    for su in search_urls:
        try:
            results += bing_search(su, session)
        except Exception as e:
            log(f"Bing: {e}", C.W)
        try:
            results += duckduckgo_search(su, session)
        except Exception as e:
            log(f"DuckDuckGo: {e}", C.W)
        try:
            results += google_search(su, session)
        except Exception as e:
            log(f"Google: {e}", C.W)
    try:
        results += text_query_search(image_url, session)
    except Exception as e:
        log(f"Text query: {e}", C.W)

    log(f"Collected {len(results)} candidate URLs from search engines", C.B)
    accounts = extract_instagram_accounts(results)[:max_results]
    log(f"Found {len(accounts)} candidate Instagram accounts, verifying pics...\n", C.B)

    matches = []
    for i, uname in enumerate(accounts):
        try:
            pic_url = instagram_profile_pic(uname, cookies_file)
            if not pic_url:
                continue
            pic_bytes = fetch(pic_url, timeout=15).content
            sim = similarity(src_hash, phash(pic_bytes))
            status = f"[{i+1}/{len(accounts)}] @{uname}: {sim*100:.0f}% match"
            if sim >= MATCH_THRESHOLD:
                log(status + "  <<<", C.G)
                matches.append({
                    'username': uname,
                    'similarity': round(sim * 100, 1),
                    'profile_pic': pic_url,
                    'url': f'https://instagram.com/{uname}/',
                })
            else:
                log(status, C.W)
        except Exception as e:
            log(f"[{i+1}] @{uname}: error {e}", C.F)
        time.sleep(0.5)

    return src_hash, matches


def save_report(image_url, src_hash, matches, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'source.jpg'), 'wb') as f:
        f.write(fetch(image_url).content)

    enc = urllib.parse.quote(image_url, safe='')
    manual_links = [
        ('Google Lens', f'https://lens.google.com/uploadbyurl?url={enc}'),
        ('Google Images', f'https://www.google.com/searchbyimage?image_url={enc}&safe=off'),
        ('Bing Visual', f'https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIHDR&q=imgurl:{enc}'),
        ('Yandex', f'https://yandex.com/images/search?url={enc}&rpt=imageview'),
        ('TinEye', f'https://tineye.com/search?url={enc}'),
        ('SauceNAO', f'https://saucenao.com/search.php?url={enc}'),
        ('ImgOps', f'https://imgops.com/{enc}'),
    ]
    manual_html = ' '.join(
        f'<a class="btn2" href="{u}" target="_blank">{n}</a>' for n, u in manual_links)

    cards = ''
    for m in matches:
        cards += f'''
        <div class="card">
          <img src="{m['profile_pic']}" onerror="this.style.display='none'">
          <h3><a href="{m['url']}" target="_blank">@{m['username']}</a></h3>
          <div class="sim">{m['similarity']}% match</div>
          <a class="btn" href="{m['url']}" target="_blank">Open Profile</a>
        </div>'''

    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Image Match Report</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0f0f14; color: #eee; padding: 30px; }}
  h1 {{ color: #58a6ff; }}
  .source {{ max-width: 200px; border-radius: 10px; border: 2px solid #333; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin-top: 20px; }}
  .card {{ background: #1a1a22; border-radius: 12px; padding: 14px; text-align: center; border: 1px solid #2a2a35; }}
  .card img {{ width: 100px; height: 100px; border-radius: 50%; object-fit: cover; }}
  .card h3 {{ margin: 10px 0 4px; font-size: 15px; }}
  .card h3 a {{ color: #58a6ff; text-decoration: none; }}
  .sim {{ color: #3fb950; font-weight: bold; margin-bottom: 10px; }}
  .btn {{ display: inline-block; background: #238636; color: #fff; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 13px; }}
  .btn2 {{ display: inline-block; background: #1f6feb; color: #fff; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 13px; margin: 4px; }}
  .none {{ color: #f0883e; }}
</style></head><body>
<h1>Instagram Image Match Report</h1>
<p>Source: <code>{image_url}</code></p>
<img class="source" src="source.jpg">
<p>Source pHash: <code>{src_hash}</code></p>
<h2>{len(matches)} account(s) using the same picture (&gt;= 80% match)</h2>
<div class="grid">
{cards if cards else '<p class="none">No matching accounts found in engine indexes. Check manually:</p>'}
</div>
<h3 style="margin-top:20px">Manual reverse image search</h3>
<p>{manual_html}</p>
</body></html>'''

    report_path = os.path.join(out_dir, 'report.html')
    with open(report_path, 'w') as f:
        f.write(html)

    with open(os.path.join(out_dir, 'matches.json'), 'w') as f:
        json.dump({'image_url': image_url, 'phash': src_hash, 'matches': matches}, f, indent=2)

    links_file = os.path.join(out_dir, 'matches_links.txt')
    with open(links_file, 'w') as f:
        for m in matches:
            f.write(f"@{m['username']} | {m['similarity']}% | {m['url']}\n")

    return report_path


def run(image_url, cookies_file='acc.txt'):
    src_hash, matches = match_image(image_url, cookies_file)
    out_dir = f"imgmatch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    report_path = save_report(image_url, src_hash, matches, out_dir)
    log(f"\nMatches: {len(matches)}", C.G)
    for m in matches:
        log(f"  @{m['username']}  {m['similarity']}%  {m['url']}", C.G)
    log(f"\nReport: file://{os.path.abspath(report_path)}", C.B)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Find Instagram accounts using the same image (>=80% match)")
    parser.add_argument('--image', '-i', required=True, help="Image URL to match")
    parser.add_argument('--cookies', '-c', default='acc.txt', help="Instagram cookies file")
    args = parser.parse_args()
    run(args.image, args.cookies)
