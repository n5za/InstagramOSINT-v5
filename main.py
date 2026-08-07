#!/usr/bin/env python3
"""
Instagram OSINT v5 - Professional Investigation Suite
Author: n5za
License: MIT
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

VERSION = "5.1.0"
BANNER = f"""
{'='*60}
  Instagram OSINT v{VERSION} - Professional Investigation Suite
  Author: n5za | https://github.com/n5za/InstagramOSINT-v5
{'='*60}
"""


class C:
    H = '\033[95m'; B = '\033[94m'; G = '\033[92m'
    W = '\033[93m'; F = '\033[91m'; E = '\033[0m'; BO = '\033[1m'


PLATFORMS = [
    ('GitHub', 'https://github.com/{}'),
    ('Twitter/X', 'https://x.com/{}'),
    ('TikTok', 'https://tiktok.com/@{}'),
    ('Reddit', 'https://reddit.com/user/{}'),
    ('YouTube', 'https://youtube.com/@{}'),
    ('Snapchat', 'https://snapchat.com/add/{}'),
    ('Pinterest', 'https://pinterest.com/{}'),
    ('Telegram', 'https://t.me/{}'),
    ('Twitch', 'https://twitch.tv/{}'),
    ('Steam', 'https://steamcommunity.com/id/{}'),
    ('SoundCloud', 'https://soundcloud.com/{}'),
    ('Medium', 'https://medium.com/@{}'),
    ('Keybase', 'https://keybase.io/{}'),
    ('About.me', 'https://about.me/{}'),
    ('Facebook', 'https://facebook.com/{}'),
    ('LinkedIn', 'https://linkedin.com/in/{}'),
    ('Threads', 'https://threads.net/@{}'),
    ('Spotify', 'https://open.spotify.com/user/{}'),
    ('VK', 'https://vk.com/{}'),
    ('Tumblr', 'https://tumblr.com/{}'),
    ('Patreon', 'https://patreon.com/{}'),
    ('ProductHunt', 'https://producthunt.com/@{}'),
    ('Behance', 'https://behance.net/{}'),
    ('Dribbble', 'https://dribbble.com/{}'),
    ('Flickr', 'https://flickr.com/people/{}'),
    ('CashApp', 'https://cash.app/${}'),
    ('PayPal', 'https://paypal.me/{}'),
    ('Venmo', 'https://venmo.com/{}'),
    ('BuyMeACoffee', 'https://buymeacoffee.com/{}'),
    ('Ko-fi', 'https://ko-fi.com/{}'),
    ('Dev.to', 'https://dev.to/{}'),
    ('Hashnode', 'https://hashnode.com/@{}'),
    ('Gravatar', 'https://gravatar.com/{}'),
    ('Last.fm', 'https://last.fm/user/{}'),
    ('Mastodon.social', 'https://mastodon.social/@{}'),
    ('Discord', 'https://discord.com/users/{}'),
    ('Roblox', 'https://roblox.com/user/{}'),
    ('Etsy', 'https://etsy.com/shop/{}'),
    ('Imgur', 'https://imgur.com/user/{}'),
    ('VSCO', 'https://vsco.co/{}'),
    ('Fiverr', 'https://fivers.com/{}'),
    ('Replit', 'https://replit.com/@{}'),
    ('CodePen', 'https://codepen.io/{}'),
    ('BitBucket', 'https://bitbucket.org/{}'),
    ('GitLab', 'https://gitlab.com/{}'),
    ('Wattpad', 'https://wattpad.com/user/{}'),
    ('Archive.org', 'https://archive.org/details/@{}'),
    ('MySpace', 'https://myspace.com/{}'),
    ('OK', 'https://ok.ru/{}'),
    ('Weibo', 'https://weibo.com/{}'),
    ('Badoo', 'https://badoo.com/en/{}'),
    ('Clubhouse', 'https://clubhouse.com/@{}'),
    ('Strava', 'https://strava.com/athletes/{}'),
    ('GIPHY', 'https://giphy.com/{}'),
    ('Disqus', 'https://disqus.com/by/{}'),
    ('Slack', 'https://{}.slack.com'),
    ('WordPress', 'https://{}.wordpress.com'),
]

REVERSE_ENGINES = [
    ('Google Lens', 'https://lens.google.com/uploadbyurl?url={}'),
    ('Google Images', 'https://www.google.com/searchbyimage?image_url={}&safe=off'),
    ('Bing Visual', 'https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIHDR&q=imgurl:{}'),
    ('Yandex', 'https://yandex.com/images/search?url={}&rpt=imageview'),
    ('TinEye', 'https://tineye.com/search?url={}'),
    ('SauceNAO', 'https://saucenao.com/search.php?url={}'),
    ('ImgOps', 'https://imgops.com/{}'),
]

GOOGLE_HACK_QUERIES = [
    ('reel-comments', '"{u}" site:instagram.com/reel'),
    ('post-comments', '"{u}" site:instagram.com/p'),
    ('comments', '"@{u}" site:instagram.com'),
    ('comments', '"{u}" site:instagram.com'),
    ('insta-activity', '"{u}" "instagram.com" comment'),
    ('mentions', '"@{u}"'),
    ('exact-username', '"{u}"'),
]

UA_FULL = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'


def _scrape_google(q, google_abuse='', timeout=12):
    """Scrape Google HTML results. Returns list of (title, url, snippet)."""
    url = f'https://www.google.com/search?q={urllib.parse.quote(q)}&num=20'
    if google_abuse:
        url += '&google_abuse=' + urllib.parse.quote(google_abuse)
    try:
        r = requests.get(url, headers={'User-Agent': UA_FULL}, timeout=timeout)
        if r.status_code != 200:
            return []
    except Exception:
        return []
    html = r.text
    hrefs = re.findall(r'href="/url\?q=([^"&]+)&', html)
    titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html)
    snips = re.findall(r'<div class="VwiC3b[^"]*"[^>]*>(.*?)</div>', html) or \
        re.findall(r'<span class="aCOpRe"[^>]*>(.*?)</span>', html)
    out = []
    for i, url in enumerate(hrefs):
        title = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else ''
        snip = re.sub(r'<[^>]+>', '', snips[i]).strip() if i < len(snips) else ''
        if url.startswith('http'):
            out.append((title, url, snip))
    return out


def _scrape_ddg(q, timeout=12):
    """Scrape DuckDuckGo HTML results. Returns list of (title, url, snippet)."""
    try:
        r = requests.post('https://html.duckduckgo.com/html/',
                          data={'q': q},
                          headers={'User-Agent': UA_FULL},
                          timeout=timeout)
        if r.status_code != 200:
            return []
    except Exception:
        return []
    html = r.text
    links = re.findall(r'class="result__a" href="([^"]+)"', html)
    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html)
    snips = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html)
    out = []
    for i, url in enumerate(links):
        title = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else ''
        snip = re.sub(r'<[^>]+>', '', snips[i]).strip() if i < len(snips) else ''
        if url.startswith('http'):
            out.append((title, url, snip))
    return out


def _clean(s):
    return re.sub(r'\s+', ' ', s).strip()


def _load_google_abuse():
    for p in ('google_abuse.txt', 'google_abuse.cookie', 'g_abuse.txt'):
        if os.path.exists(p):
            with open(p) as f:
                v = f.read().strip()
                if 'GOOGLE_ABUSE_EXEMPTION' in v:
                    return v.split('GOOGLE_ABUSE_EXEMPTION=', 1)[1]
                return v
    return ''


class InstagramOSINT:
    def __init__(self, username, cookies_file="acc.txt", use_tor=False,
                 all_posts=False, skip_platforms=False, skip_friends=False,
                 skip_comments=False, skip_image=False, skip_ghack=False, tz=0):
        self.username = username
        self.user_id = None
        self.use_tor = use_tor
        self.all_posts = all_posts
        self.skip_platforms = skip_platforms
        self.skip_friends = skip_friends
        self.skip_comments = skip_comments
        self.skip_image = skip_image
        self.skip_ghack = skip_ghack
        self.tz = tz
        self.cookies_file = cookies_file
        self.profile = {}
        self.posts = []
        self.following = []
        self.followers = []
        self.friends = []
        self.friend_bios = {}
        self.comments = []
        self.cross_platform = {}
        self.google_hack = {}
        self.session = None
        self.cookies_dict = {}
        self.output_dir = ""
        self.created_at = None

        self._log(C.G, f"[*] Target: @{self.username}")
        self._load_cookies()
        self._create_session()
        self._run()

    def _log(self, color, msg, raw=False):
        if raw:
            print(f"{msg}")
        else:
            print(f"  {color}{msg}{C.E}")

    def _load_cookies(self):
        if not os.path.exists(self.cookies_file):
            self._log(C.W, "[!] No cookies file")
            return
        with open(self.cookies_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        domain, _, _, _, _, name, value = parts[:7]
                        if domain.endswith('instagram.com'):
                            self.cookies_dict[name.strip()] = value.strip()
                elif '=' in line:
                    k, v = line.split('=', 1)
                    self.cookies_dict[k.strip()] = v.strip()
        if self.cookies_dict:
            self._log(C.G, "[+] Cookies loaded")
        else:
            self._log(C.W, "[!] No usable cookies found in file")

    def _create_session(self):
        self.session = requests.Session()
        if self.use_tor:
            self.session.proxies.update({'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'})
            self._log(C.G, "[+] Tor enabled")

        if self.cookies_dict and self.cookies_dict.get('sessionid'):
            self.session.cookies.update(self.cookies_dict)
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'X-IG-App-ID': '936619743392459',
                'X-CSRFToken': self.cookies_dict.get('csrftoken', ''),
            })

    def _plain_headers(self):
        h = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'X-IG-App-ID': '936619743392459',
            'X-CSRFToken': self.cookies_dict.get('csrftoken', ''),
        }
        if self.cookies_dict:
            h['Cookie'] = '; '.join(f"{k}={v}" for k, v in self.cookies_dict.items())
        return h

    def _api(self, url, retries=2):
        for i in range(retries):
            try:
                r = self.session.get(url, timeout=15)
                if r.status_code == 200:
                    return r.json()
                elif r.status_code == 429:
                    self._log(C.W, f"[!] Rate limited, waiting {(i+1)*5}s...")
                    time.sleep((i+1)*5)
            except Exception:
                time.sleep(2)
        return None

    def _paginate(self, endpoint, key='users', max_pages=10, delay=0.7):
        items, max_id = [], None
        for _ in range(max_pages):
            url = f'{endpoint}&max_id={max_id}' if max_id else endpoint
            data = self._api(url)
            if not data or not data.get(key):
                break
            batch = data[key]
            items.extend(batch)
            if len(batch) < 1:
                break
            try:
                next_id = data.get('next_max_id')
                if not next_id:
                    break
                max_id = next_id
            except:
                break
            time.sleep(delay)
        return items

    def _resolve(self):
        self._log(C.B, "\n╔═══════════════════════════════════════════════╗")
        self._log(C.B, "║ [1] Profile Resolution                       ║")
        self._log(C.B, "╚═══════════════════════════════════════════════╝")

        data = self._api(f'https://www.instagram.com/api/v1/web/search/topsearch/?query={self.username}&context=blended')
        similar = []
        if data and data.get('users'):
            for entry in data['users']:
                u = entry.get('user', {})
                uname = u.get('username', '')
                if uname.lower() == self.username.lower():
                    self.user_id = u.get('pk')
                    break
                similar.append(uname)

        if not self.user_id:
            info = self._api(f'https://www.instagram.com/api/v1/users/web_profile_info/?username={self.username}')
            gu = (info or {}).get('data', {}).get('user')
            if gu:
                self.user_id = gu.get('id')
                self._log(C.G, f"[+] Resolved via web_profile_info (id {self.user_id})")

        if not self.user_id:
            self._log(C.F, f"[-] User @{self.username} not found")
            if similar:
                self._log(C.W, f"[?] Did you mean: {', '.join('@'+n for n in similar[:8])}?")
            sys.exit(1)

        info = self._api(f'https://www.instagram.com/api/v1/users/{self.user_id}/info/')
        if not info or not info.get('user'):
            self._log(C.F, "[-] Failed to fetch profile info")
            sys.exit(1)

        u = info['user']
        pic_url = u.get('hd_profile_pic_url_info', {}).get('url', '') or u.get('profile_pic_url', '')
        bci = u.get('business_contact_info', {}) or {}
        self.profile = {
            'username': u.get('username'),
            'full_name': u.get('full_name', ''),
            'user_id': u.get('pk'),
            'bio': u.get('biography', ''),
            'followers': u.get('follower_count', 0),
            'following': u.get('following_count', 0),
            'posts': u.get('media_count', 0),
            'private': u.get('is_private', False),
            'verified': u.get('is_verified', False),
            'business': u.get('is_business', False),
            'external_url': u.get('external_url', ''),
            'category': u.get('category', ''),
            'email': u.get('public_email', '') or bci.get('email', ''),
            'phone': u.get('public_phone_number', '') or bci.get('phone_number', ''),
            'city': u.get('city_name', ''),
            'address': bci.get('address_street', ''),
            'zip': bci.get('zip', ''),
            'website': bci.get('website', ''),
            'profile_pic_url': pic_url,
        }

        self._log(C.G, f"[+] @{self.profile['username']} ({self.profile['full_name']})")
        self._log(C.G, f"[+] ID: {self.profile['user_id']}")
        self._log(C.G, f"[+] Followers: {self.profile['followers']:,} | Following: {self.profile['following']:,} | Posts: {self.profile['posts']:,}")
        if self.profile['bio']:
            self._log(C.G, f"[+] Bio: {self.profile['bio'][:80]}..." if len(self.profile['bio']) > 80 else f"[+] Bio: {self.profile['bio']}")
        if self.profile['external_url']:
            self._log(C.G, f"[+] URL: {self.profile['external_url']}")

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = f"osint_{self.username}_{ts}"
        os.makedirs(self.output_dir, exist_ok=True)

    def _posts(self):
        self._log(C.B, "\n╔═══════════════════════════════════════════════╗")
        self._log(C.B, "║ [2] Posts & Engagement Analysis              ║")
        self._log(C.B, "╚═══════════════════════════════════════════════╝")

        if self.profile.get('private') and not self.profile.get('posts'):
            self._log(C.W, "[!] Private account — posts are not accessible")
            return

        max_id = None
        max_pages = 100 if self.all_posts else 1
        page = 0
        while page < max_pages:
            page += 1
            endpoint = f'https://www.instagram.com/api/v1/feed/user/{self.user_id}/?count=12'
            if max_id:
                endpoint += f'&max_id={max_id}'
            data = self._api(endpoint)
            if not data:
                break
            self._process_feed_items(data)
            nid = data.get('next_max_id')
            if not nid:
                break
            max_id = nid
            if self.all_posts:
                self._log(C.G, f"[+] Fetched {len(self.posts)} posts so far...")
                time.sleep(0.6)

        if not self.posts:
            self._log(C.W, "[!] No posts found")
            return

        self._engagement_stats()

    def _engagement_stats(self):
        n = len(self.posts)
        timestamps = [p['ts'] for p in self.posts if p.get('ts')]
        total_likes = sum(p['likes'] for p in self.posts)
        total_comments = sum(p['comments'] for p in self.posts)
        all_hashtags = Counter(h for p in self.posts for h in p.get('hashtags', []))
        all_mentions = Counter(m for p in self.posts for m in p.get('mentions', []))

        avg_likes = total_likes / n if n else 0
        avg_comments = total_comments / n if n else 0
        followers = self.profile.get('followers', 1)
        er = ((avg_likes + avg_comments) / followers) * 100 if followers else 0

        if timestamps:
            earliest = min(timestamps)
            self.created_at = datetime.fromtimestamp(earliest, tz=timezone.utc)
            account_age_days = (datetime.now(timezone.utc) - self.created_at).days
            self.profile['estimated_account_age_days'] = account_age_days
            self.profile['estimated_created'] = self.created_at.strftime('%Y-%m-%d')
        else:
            account_age_days = 0

        days_span = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 1
        days_span_days = days_span / 86400 if days_span > 0 else 1
        posts_per_week = (n / days_span_days) * 7 if days_span_days > 0 else 0

        hours = [datetime.fromtimestamp(t, tz=timezone.utc).hour for t in timestamps if t]
        best_hour = Counter(hours).most_common(1)[0][0] if hours else 0

        best_post = max(self.posts, key=lambda p: p['likes']) if self.posts else None

        self.profile['engagement_rate'] = round(er, 2)
        self.profile['avg_likes'] = round(avg_likes, 0)
        self.profile['avg_comments'] = round(avg_comments, 0)
        self.profile['posts_per_week'] = round(posts_per_week, 1)
        self.profile['best_hour_utc'] = best_hour
        self.profile['best_hour_local'] = (best_hour + self.tz) % 24
        self.profile['top_hashtags'] = [h for h, _ in all_hashtags.most_common(10)]
        self.profile['top_mentions'] = [m for m, _ in all_mentions.most_common(10)]

        self._log(C.G, f"\n[+] 📊 Engagement Rate: {er:.2f}% (avg ❤️{avg_likes:.0f} 💬{avg_comments:.0f})")
        self._log(C.G, f"[+] 📅 Posts/Week: {posts_per_week:.1f}")
        self._log(C.G, f"[+] 🕐 Best hour: {best_hour}:00 UTC / {(best_hour + self.tz) % 24}:00 local")
        self._log(C.G, f"[+] 🏆 Most liked: ❤️{best_post['likes']} ({best_post['datetime']})" if best_post else "")
        if self.profile.get('estimated_created'):
            self._log(C.G, f"[+] 🎂 Est. account from: {self.profile['estimated_created']} (~{account_age_days} days)")
        if all_hashtags:
            self._log(C.G, f"[+] 🔖 Top hashtags: {', '.join('#'+h for h,_ in all_hashtags.most_common(5))}")
        if all_mentions:
            self._log(C.G, f"[+] 📢 Top mentions: {', '.join('@'+m for m,_ in all_mentions.most_common(5))}")

    def _process_feed_items(self, data):
        for item in data.get('items', []):
            mt = item.get('media_type', 0)
            ts = item.get('taken_at', 0)
            cap = item.get('caption', {})
            cap_text = cap.get('text', '') if cap else ''
            pid = item.get('id', '').split('_')[0]
            likes = item.get('like_count', 0)
            cc = item.get('comment_count', 0)

            tags = set(re.findall(r'#(\w+)', cap_text))
            mentions = set(re.findall(r'@(\w+)', cap_text))

            media = []
            if mt == 1:
                img = item.get('display_uri', '') or item.get('display_url', '')
                if img:
                    media.append(('image', img))
            elif mt == 2:
                vid = item.get('video_versions', [{}])[0].get('url', '') if item.get('video_versions') else ''
                thumb = item.get('display_uri', '') or item.get('display_url', '')
                if vid:
                    media.append(('video', vid))
                if thumb:
                    media.append(('thumbnail', thumb))
            elif mt == 8:
                for cm in item.get('carousel_media', []):
                    cmt = cm.get('media_type', 1)
                    if cmt == 1:
                        u = cm.get('image_versions2', {}).get('candidates', [{}])[0].get('url', '')
                        if u:
                            media.append(('image', u))
                    elif cmt == 2:
                        u = cm.get('video_versions', [{}])[0].get('url', '') if cm.get('video_versions') else ''
                        if u:
                            media.append(('video', u))

            self.posts.append({
                'id': pid, 'ts': ts,
                'datetime': datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if ts else '',
                'caption': cap_text, 'likes': likes, 'comments': cc,
                'type': {1: 'Image', 2: 'Video', 8: 'Carousel'}.get(mt, 'Unknown'),
                'hashtags': list(tags), 'mentions': list(mentions),
                'media': media,
            })

            cap_show = cap_text[:60] + '...' if len(cap_text) > 60 else cap_text
            self._log(C.G, f"[+] #{len(self.posts)} {self.posts[-1]['datetime']} | {self.posts[-1]['type']} | ❤️{likes} 💬{cc} | {cap_show}")

    def _download_pic(self):
        url = self.profile.get('profile_pic_url', '')
        if not url:
            self._log(C.W, "[!] No profile pic URL")
            return None
        try:
            r = self.session.get(url, timeout=15)
            if r.status_code == 200:
                path = os.path.join(self.output_dir, 'profile_pic.jpg')
                with open(path, 'wb') as f:
                    f.write(r.content)
                self._log(C.G, f"[+] Profile pic saved")
                return path
            else:
                self._log(C.W, f"[!] Profile pic HTTP {r.status_code}")
        except Exception as e:
            self._log(C.W, f"[!] Pic download: {e}")
        return None

    def _reverse_image_search(self, pic_path):
        self._log(C.B, "\n╔═══════════════════════════════════════════════╗")
        self._log(C.B, "║ [3] Reverse Image Search                     ║")
        self._log(C.B, "╚═══════════════════════════════════════════════╝")

        url = self.profile.get('profile_pic_url', '')
        if not url:
            self._log(C.W, "[!] No profile pic to search")
            return

        encoded = urllib.parse.quote(url, safe='')
        self._log(C.G, "[+] Opening all reverse image engines...\n")

        links_file = os.path.join(self.output_dir, 'reverse_image_search_urls.txt')
        with open(links_file, 'w') as f:
            for name, template in REVERSE_ENGINES:
                link = template.format(encoded)
                self._log(C.G, f"  {name}: {link}")
                f.write(f"{name}: {link}\n")

        self._log(C.G, f"\n[+] Saved search links to: {links_file}")

        # Try automated search on Google
        try:
            r = requests.get(
                f"https://www.google.com/searchbyimage?image_url={encoded}&safe=off",
                headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            if r.status_code == 200:
                ig_accounts = re.findall(r'instagram\.com/([a-zA-Z0-9_.]+)', r.text)
                ig_accounts = list(set(a.lower() for a in ig_accounts if a.lower() != self.username.lower() and len(a) > 2))
                if ig_accounts:
                    self._log(C.G, f"\n[+] Potential same pic on other IG accounts:")
                    for a in ig_accounts[:10]:
                        self._log(C.G, f"    https://instagram.com/{a}/")
        except Exception:
            pass

    def _friends(self):
        self._log(C.B, "\n╔═══════════════════════════════════════════════╗")
        self._log(C.B, "║ [4] Friends (Mutuals)                        ║")
        self._log(C.B, "╚═══════════════════════════════════════════════╝")

        if self.skip_friends:
            self._log(C.W, "[!] Skipped friends analysis")
            return

        if self.profile.get('private'):
            self._log(C.W, "[!] Private account — mutuals not accessible")
            return

        f_pages = min(10, max(1, (self.profile['following'] + 49) // 50))
        fl_pages = min(10, max(1, (self.profile['followers'] + 199) // 200))

        self._log(C.G, f"[+] Fetching following ({self.profile['following']}) & followers ({self.profile['followers']})...")
        self.following = self._paginate(
            f'https://www.instagram.com/api/v1/friendships/{self.user_id}/following/?count=50', max_pages=f_pages)
        self.followers = self._paginate(
            f'https://www.instagram.com/api/v1/friendships/{self.user_id}/followers/?count=200', max_pages=fl_pages, delay=0.8)

        f_set = {u['username'] for u in self.following}
        fl_set = {u['username'] for u in self.followers}
        mutual = f_set & fl_set
        self.friends = [u for u in self.following if u['username'] in mutual]

        self._log(C.G, f"[+] Following: {len(self.following)} | Followers: {len(self.followers)} | Friends: {len(self.friends)}")

        if not self.friends:
            self._log(C.W, "[!] No mutuals found")
            return

        Path(os.path.join(self.output_dir, 'friends.txt')).write_text('\n'.join(u['username'] for u in self.friends))
        self._log(C.G, "[+] --- Friends ---")
        for u in self.friends:
            self._log(C.G, f"    @{u['username']} ({u.get('full_name', '')})")

        # Scan friend bios
        self._log(C.G, "\n[+] Scanning friend bios...")
        keywords = {
            'school|highschool|hs|ghs|academy|college|university|student': 'Education',
            'dev|developer|engineer|programmer|code|hacker|cyber|security|software': 'Tech/Dev',
            'musician|singer|rapper|producer|artist|band|music|song': 'Music',
            'fitness|gym|trainer|coach|athlete|sport|workout': 'Fitness',
            'business|entrepreneur|ceo|founder|owner|startup|co-founder': 'Business',
            'morroco|moroccan|maghreb|darija|arab|islam|muslim': 'Cultural',
            'photo|photography|photographer|design|graphic|creative|art': 'Creative',
            'doctor|medical|nurse|health|hospital|pharmacy': 'Medical',
            'law|lawyer|attorney|legal|justice': 'Legal',
            'teacher|professor|educator|tutor|prof': 'Education',
        }
        patterns = {}

        def _fetch_bio(u):
            uid = u.get('pk')
            if not uid:
                return None
            try:
                r = requests.get(f'https://www.instagram.com/api/v1/users/{uid}/info/',
                                 headers=self._plain_headers(), timeout=8)
                if r.status_code == 200:
                    bio = r.json().get('user', {}).get('biography', '')
                    if bio:
                        return u['username'], bio
            except Exception:
                pass
            return None

        bios = []
        self._log(C.G, f"[+] Scanning {len(self.friends)} friend bios concurrently...")
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = [ex.submit(_fetch_bio, u) for u in self.friends]
            for fut in as_completed(futs):
                res = fut.result()
                if res:
                    bios.append(res)
            time.sleep(0.3)

        for uname, bio in bios:
            self.friend_bios[uname] = bio
            u = next((x for x in self.friends if x.get('username') == uname), {})
            text = f"{uname} {u.get('full_name','')} {bio}".lower()
            for pat, cat in keywords.items():
                if re.search(pat, text):
                    patterns.setdefault(cat, []).append(uname)
                    break

        if patterns:
            self._log(C.G, "\n[+] Friend Categories:")
            for cat, accs in sorted(patterns.items()):
                self._log(C.G, f"    {cat} ({len(accs)}): {', '.join(accs[:10])}")

    def _check_platform(self, name, url):
        try:
            r = requests.get(url, timeout=5, headers={'User-Agent': UA_FULL}, allow_redirects=True, stream=True)
            if r.status_code == 200:
                return name, url
        except Exception:
            pass
        return None

    def _username_search(self):
        self._log(C.B, "\n╔═══════════════════════════════════════════════╗")
        self._log(C.B, "║ [5] Cross-Platform Username Search            ║")
        self._log(C.B, "╚═══════════════════════════════════════════════╝")

        uname = self.username
        found = []
        if not self.skip_platforms:
            self._log(C.G, f"[+] Checking {len(PLATFORMS)} platforms concurrently...")
            with ThreadPoolExecutor(max_workers=10) as ex:
                futs = {ex.submit(self._check_platform, name, tmpl.format(uname)): name
                        for name, tmpl in PLATFORMS}
                for fut in as_completed(futs):
                    res = fut.result()
                    if res:
                        name, url = res
                        self.cross_platform[name] = url
                        found.append(f"{name}: {url}")
                        self._log(C.G, f"  [+] {name}: {url}")
        else:
            self._log(C.W, "[!] Skipped platform search")

        # Google dork search
        dorks = [
            f'site:instagram.com "{uname}"',
            f'site:tiktok.com "{uname}"',
            f'site:x.com "{uname}"',
            f'site:facebook.com "{uname}"',
            f'site:youtube.com "{uname}"',
            f'site:reddit.com "{uname}"',
            f'site:github.com "{uname}"',
            f'site:linkedin.com/in "{uname}"',
            f'site:medium.com "{uname}"',
        ]
        self._log(C.G, "\n[+] Google Dork Searches:")
        dork_file = os.path.join(self.output_dir, 'dork_searches.txt')
        with open(dork_file, 'w') as f:
            for dork in dorks:
                url = f"https://www.google.com/search?q={urllib.parse.quote(dork)}"
                self._log(C.G, f"    {url}")
                f.write(f"{url}\n")

        if found:
            path = os.path.join(self.output_dir, 'cross_platform.txt')
            Path(path).write_text('\n'.join(found))
        self._log(C.G, f"\n[+] Dork links saved: {dork_file}")

    def _google_hacker(self):
        self._log(C.B, "\n╔═══════════════════════════════════════════════╗")
        self._log(C.B, "║ [5b] Google Hacker (comments/mentions)        ║")
        self._log(C.B, "╚═══════════════════════════════════════════════╝")

        if self.skip_ghack:
            self._log(C.W, "[!] Skipped Google Hacker")
            return

        uname = self.username
        abuse = _load_google_abuse()
        if abuse:
            self._log(C.G, "[+] Google abuse-exemption cookie loaded")

        self._log(C.G, f"[*] Mining search engines for @{uname} comments/mentions...\n")

        hits = {}  # url -> (title, snippet)
        for label, tpl in GOOGLE_HACK_QUERIES:
            q = tpl.format(u=uname)
            self._log(C.G, f"  [-] dork [{label}]: \"{q}\"")
            for engine, fn in (('Google', lambda: _scrape_google(q, abuse)),
                               ('DuckDuckGo', lambda: _scrape_ddg(q))):
                try:
                    for title, url, snip in fn():
                        if url in hits:
                            continue
                        hits[url] = (title or url, _clean(snip))
                except Exception:
                    pass
            time.sleep(1.0)
        self.google_hack = hits

        if not hits:
            self._log(C.W, "[!] No results from search engines")
            return

        insta = {u: v for u, v in hits.items() if 'instagram.com' in u}
        self._log(C.G, f"\n[+] Found {len(hits)} results ({len(insta)} Instagram-related)")
        self._log(C.G, "\n[+] Instagram results:")
        for url, (title, snip) in list(insta.items())[:25]:
            self._log(C.G, f"    • {url}")
            if title and title != url:
                self._log(C.G, f"      {title[:110]}")
            if snip:
                self._log(C.G, f"      {snip[:150]}")

        self._log(C.G, "\n[+] Other results (possible mentions):")
        other = {u: v for u, v in hits.items() if 'instagram.com' not in u}
        for url, (title, snip) in list(other.items())[:15]:
            self._log(C.G, f"    • {url}")
            if snip:
                self._log(C.G, f"      {snip[:150]}")

        lines = [f"Google Hacker results for @{uname}",
                 f"Searched {len(GOOGLE_HACK_QUERIES)} dorks via Google + DuckDuckGo",
                 ""]
        lines.append(f"== Instagram ({len(insta)}) ==")
        for url, (title, snip) in insta.items():
            lines.append(f"URL: {url}")
            if title:
                lines.append(f"TITLE: {title}")
            if snip:
                lines.append(f"SNIPPET: {snip}")
            lines.append("")
        lines.append(f"== Other ({len(other)}) ==")
        for url, (title, snip) in other.items():
            lines.append(f"URL: {url}")
            if snip:
                lines.append(f"SNIPPET: {snip}")
            lines.append("")

        path = os.path.join(self.output_dir, 'google_hacker.txt')
        Path(path).write_text('\n'.join(lines))
        self._log(C.G, f"\n[+] Saved: {path}")

    def _comments(self):
        self._log(C.B, "\n╔═══════════════════════════════════════════════╗")
        self._log(C.B, "║ [6] Comments Extraction                      ║")
        self._log(C.B, "╚═══════════════════════════════════════════════╝")

        for post in self.posts:
            if post['comments'] == 0:
                continue
            time.sleep(1.5)
            try:
                r = self.session.get(
                    f'https://www.instagram.com/api/v1/media/{post["id"]}/comments/?can_support_threading=true&count=50',
                    timeout=15)
                if r.status_code != 200:
                    continue
                data = r.json()
                if not data or not data.get('comments'):
                    continue
                for c in data['comments']:
                    cu = c.get('user', {})
                    self.comments.append({'post_id': post['id'], 'username': cu.get('username'), 'text': c.get('text', '')})
                    self._log(C.G, f"    @{cu.get('username')}: {c.get('text', '')[:120]}")
            except:
                pass

        if self.comments:
            unique = set(c['username'] for c in self.comments if c.get('username'))
            self._log(C.G, f"\n[+] Comments: {len(self.comments)} from {len(unique)} users")
        else:
            self._log(C.W, "[!] No comments extracted")

    def _save(self):
        data = {
            'version': VERSION,
            'target': self.username,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'profile': self.profile,
            'posts': [{
                'id': p['id'], 'datetime': p['datetime'], 'caption': p['caption'],
                'likes': p['likes'], 'comments': p['comments'], 'type': p['type'],
                'hashtags': p['hashtags'], 'mentions': p['mentions'],
            } for p in self.posts],
            'friends': [{'username': u['username'], 'full_name': u.get('full_name', '')} for u in self.friends],
            'friend_categories': self.friend_bios,
            'comments': self.comments,
            'cross_platform': self.cross_platform,
            'google_hacker': [{'url': u, 'title': v[0], 'snippet': v[1]} for u, v in self.google_hack.items()],
        }
        path = os.path.join(self.output_dir, 'data.json')
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        self._log(C.G, f"\n[+] Data saved: {path}")

    def _report(self):
        self._log(C.B, "\n╔═══════════════════════════════════════════════╗")
        self._log(C.B, "║ [7] HTML Report                              ║")
        self._log(C.B, "╚═══════════════════════════════════════════════╝")

        abs_out = os.path.abspath(self.output_dir)
        html_path = os.path.join(abs_out, 'report.html')

        mutual_usernames = [u['username'] for u in self.friends]
        following_usernames = [u['username'] for u in self.following]
        followers_usernames = [u['username'] for u in self.followers]

        comments_by_post = {}
        for c in self.comments:
            comments_by_post.setdefault(c.get('post_id'), []).append(c)

        posts_html = ''
        for i, p in enumerate(self.posts):
            post_comments = comments_by_post.get(p['id'], [])
            comments_html = ''
            for c in post_comments:
                comments_html += f'<div class="comment"><b>@{c["username"]}:</b> {c["text"][:200]}</div>'
            tags_html = ''.join(f'<span class="tag">#{h}</span>' for h in p.get('hashtags', [])[:5])
            posts_html += f'''
            <div class="post">
              <div class="meta">#{i+1} | {p["datetime"]} | {p["type"]} | ❤️{p["likes"]} 💬{p["comments"]}</div>
              <div class="cap">{p["caption"]}</div>
              {tags_html}{comments_html}
            </div>'''

        friends_html = ''.join(f'<span class="tag">@{u}</span>' for u in mutual_usernames)

        pic_html = ''
        pic_path = os.path.join(abs_out, 'profile_pic.jpg')
        if os.path.exists(pic_path):
            pic_html = f'<img src="profile_pic.jpg" style="width:150px;height:150px;border-radius:50%;margin-bottom:15px;">'

        cross_html = ''
        for name, url in sorted(self.cross_platform.items()):
            cross_html += f'<div>🌐 <b>{name}:</b> <a href="{url}" target="_blank">{url}</a></div>'

        er = self.profile.get('engagement_rate', 0)
        ppw = self.profile.get('posts_per_week', 0)
        bh = self.profile.get('best_hour_utc', 0)
        age = self.profile.get('estimated_account_age_days', 0)
        top_tags = self.profile.get('top_hashtags', [])
        top_tags_html = ''.join(f'<span class="tag">#{h}</span>' for h in top_tags[:10])

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>OSINT Report - @{self.username}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#0f0f0f;color:#e0e0e0;padding:20px;}}
.container{{max-width:1000px;margin:auto;}}
.header{{background:linear-gradient(135deg,#833ab4,#fd1d1d,#fcb045);color:#fff;padding:25px;border-radius:10px;margin-bottom:20px;text-align:center;}}
.header h1{{font-size:28px;}}
.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:15px 0;}}
.metric{{background:#1a1a2e;border-radius:8px;padding:15px;text-align:center;}}
.metric .num{{font-size:24px;font-weight:bold;color:#fcb045;}}
.metric .lab{{font-size:11px;color:#999;margin-top:4px;}}
.section{{background:#1a1a2e;border-radius:8px;padding:20px;margin:15px 0;}}
.section h2{{color:#fcb045;border-bottom:1px solid #333;padding-bottom:8px;margin-bottom:12px;}}
.grid{{display:grid;grid-template-columns:180px 1fr;gap:6px;}}
.label{{color:#999;font-weight:bold;}}
.post{{border:1px solid #333;border-radius:6px;padding:12px;margin:8px 0;}}
.post .meta{{color:#666;font-size:12px;}}
.post .cap{{background:#0a0a1a;padding:8px;margin:5px 0;border-radius:4px;white-space:pre-wrap;}}
.comment{{background:#111122;padding:5px 10px;margin:3px 0;border-radius:4px;font-size:13px;}}
.tag{{display:inline-block;background:#833ab4;color:#fff;padding:3px 12px;border-radius:12px;margin:3px;font-size:12px;}}
a{{color:#4da6ff;}}
.footer{{text-align:center;color:#555;font-size:12px;margin-top:30px;}}
</style>
</head>
<body>
<div class="container">
<div class="header">
{pic_html}
<h1>@{self.username}</h1>
<p>{self.profile.get('full_name','')} | ID: {self.profile.get('user_id','')}</p>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
</div>

<div class="metrics">
<div class="metric"><div class="num">{self.profile.get('followers',0):,}</div><div class="lab">Followers</div></div>
<div class="metric"><div class="num">{self.profile.get('following',0):,}</div><div class="lab">Following</div></div>
<div class="metric"><div class="num">{self.profile.get('posts',0):,}</div><div class="lab">Posts</div></div>
<div class="metric"><div class="num">{er}%</div><div class="lab">Engagement Rate</div></div>
<div class="metric"><div class="num">{ppw}</div><div class="lab">Posts/Week</div></div>
<div class="metric"><div class="num">{bh}:00</div><div class="lab">Best Hour (UTC)</div></div>
<div class="metric"><div class="num">{age}d</div><div class="lab">Est. Account Age</div></div>
<div class="metric"><div class="num">{len(mutual_usernames)}</div><div class="lab">Friends (Mutual)</div></div>
</div>

<div class="section"><h2>Profile</h2><div class="grid">
'''
        for k, v in self.profile.items():
            if v and str(v) not in ('0', 'False', 'None', '', '0.0'):
                label = k.replace('_', ' ').title()
                if k not in ('user_id',):
                    html += f'<div class="label">{label}</div><div class="value">{v}</div>'
        html += '</div></div>'

        if self.profile.get('bio'):
            html += f'<div class="section"><h2>Biography</h2><div style="background:#0a0a1a;padding:15px;border-left:4px solid #fcb045;white-space:pre-wrap;">{self.profile["bio"]}</div></div>'

        if top_tags_html:
            html += f'<div class="section"><h2>Top Hashtags</h2>{top_tags_html}</div>'

        if self.posts:
            html += f'<div class="section"><h2>Posts ({len(self.posts)})</h2>{posts_html}</div>'

        if mutual_usernames:
            html += f'<div class="section"><h2>Friends - Mutual ({len(mutual_usernames)})</h2>{friends_html}</div>'

        if cross_html:
            html += f'<div class="section"><h2>Cross-Platform ({len(self.cross_platform)})</h2>{cross_html}</div>'

        if self.google_hack:
            gh_html = ''
            insta = {u: v for u, v in self.google_hack.items() if 'instagram.com' in u}
            other = {u: v for u, v in self.google_hack.items() if 'instagram.com' not in u}
            for url, (title, snip) in insta.items():
                gh_html += f'<div class="post"><a href="{url}" target="_blank">{url}</a>'
                if snip:
                    gh_html += f'<div class="cap">{snip[:200]}</div>'
                gh_html += '</div>'
            for url, (title, snip) in other.items():
                gh_html += f'<div class="post"><a href="{url}" target="_blank">{url}</a>'
                if snip:
                    gh_html += f'<div class="cap">{snip[:200]}</div>'
                gh_html += '</div>'
            html += f'<div class="section"><h2>Google Hacker (comments/mentions) ({len(self.google_hack)})</h2>{gh_html}</div>'

        if self.comments:
            html += f'<div class="section"><h2>Comments ({len(self.comments)})</h2>'
            commenters = set(c['username'] for c in self.comments if c.get('username'))
            for cu in sorted(commenters)[:30]:
                html += f'<span class="tag">@{cu}</span>'
            html += '</div>'

        html += f'''
<div class="section"><h2>Open Reports</h2>
<div><a href="file://{os.path.join(abs_out, 'data.json')}">📊 data.json</a></div>
<div><a href="file://{os.path.join(abs_out, 'friends.txt')}">👥 friends.txt</a></div>
<div><a href="file://{os.path.join(abs_out, 'cross_platform.txt')}">🌐 cross_platform.txt</a></div>
<div><a href="file://{os.path.join(abs_out, 'google_hacker.txt')}">🔍 google_hacker.txt</a></div>
<div><a href="file://{os.path.join(abs_out, 'reverse_image_search_urls.txt')}">🔍 reverse_image_search_urls.txt</a></div>
<div><a href="file://{os.path.join(abs_out, 'dork_searches.txt')}">🔎 dork_searches.txt</a></div>
</div>

<div class="footer">Instagram OSINT v{VERSION} | github.com/n5za/InstagramOSINT-v5</div>
</div></body></html>'''

        with open(html_path, 'w') as f:
            f.write(html)

        self._log(C.G, f"[+] Report: file://{html_path}")

    def _summary(self):
        self._log(C.B, "\n╔═══════════════════════════════════════════════╗")
        self._log(C.B, "║ INVESTIGATION COMPLETE                       ║")
        self._log(C.B, "╚═══════════════════════════════════════════════╝")
        self._log(C.G, f"  Target: @{self.profile.get('username')} ({self.profile.get('full_name', '')})", raw=True)
        self._log(C.G, f"  Posts: {len(self.posts)} | Friends: {len(self.friends)} | Platforms: {len(self.cross_platform)}", raw=True)
        self._log(C.G, f"  Google Hacker hits: {len(self.google_hack)} | Comments extracted: {len(self.comments)}", raw=True)
        self._log(C.G, f"  Engagement Rate: {self.profile.get('engagement_rate', 0):.2f}%", raw=True)
        self._log(C.G, f"  Output: file://{os.path.abspath(self.output_dir)}/", raw=True)

    def _run(self):
        self._resolve()
        self._posts()
        if not self.skip_image:
            pic_path = self._download_pic()
            self._reverse_image_search(pic_path)
        else:
            self._log(C.W, "[!] Skipped image search")
        self._friends()
        self._username_search()
        self._google_hacker()
        if not self.skip_comments:
            self._comments()
        else:
            self._log(C.W, "[!] Skipped comments extraction")
        self._save()
        self._report()
        self._summary()


def standalone_reverse_image(image_url):
    enc = urllib.parse.quote(image_url, safe='')
    print(f"  {C.G}[*] Image URL: {image_url}{C.E}\n")
    for name, template in REVERSE_ENGINES:
        link = template.format(enc)
        print(f"  {C.G}{name:15s}: {link}{C.E}")


def standalone_username_search(username):
    print(f"  {C.G}[*] Username: @{username}{C.E}\n")
    for platform, tmpl in PLATFORMS:
        url = tmpl.format(username)
        print(f"  {C.G}  [+] {platform:15s}: {url}{C.E}")

    print(f"\n  {C.G}[+] Google Dork Searches:{C.E}")
    dork_sites = ['instagram.com', 'tiktok.com', 'x.com', 'facebook.com',
                  'youtube.com', 'reddit.com', 'github.com', 'linkedin.com/in', 'medium.com']
    for site in dork_sites:
        q = f'site:{site} "{username}"'
        print(f"  {C.G}    https://www.google.com/search?q={urllib.parse.quote(q)}{C.E}")


def standalone_google_hack(username):
    print(f"  {C.G}[*] Google Hacker target: @{username}{C.E}")
    abuse = _load_google_abuse()
    if abuse:
        print(f"  {C.G}[+] Google abuse-exemption cookie loaded{C.E}")
    hits = {}
    for label, tpl in GOOGLE_HACK_QUERIES:
        q = tpl.format(u=username)
        print(f"\n  {C.G}[-] dork [{label}]: \"{q}\"{C.E}")
        for engine, fn in (('Google', lambda: _scrape_google(q, abuse)),
                           ('DuckDuckGo', lambda: _scrape_ddg(q))):
            try:
                for title, url, snip in fn():
                    if url in hits:
                        continue
                    hits[url] = (title or url, _clean(snip))
            except Exception:
                pass
        time.sleep(1.0)
    if not hits:
        print(f"  {C.W}[!] No results{C.E}")
        return
    print(f"\n  {C.G}[+] {len(hits)} results{C.E}")
    insta = {u: v for u, v in hits.items() if 'instagram.com' in u}
    for url, (title, snip) in insta.items():
        print(f"  {C.G}  • {url}{C.E}")
        if snip:
            print(f"  {C.G}    {snip[:150]}{C.E}")
    path = f'google_hack_{username}.txt'
    with open(path, 'w') as f:
        for url, (title, snip) in hits.items():
            f.write(f"URL: {url}\nSNIPPET: {snip}\n\n")
    print(f"\n  {C.G}[+] Saved: {path}{C.E}")


def main():
    print(BANNER)
    parser = argparse.ArgumentParser(description="Instagram OSINT v5")
    parser.add_argument("--username", "-u", help="Target username")
    parser.add_argument("--image", "-i", help="Reverse image search on any image URL")
    parser.add_argument("--search", "-s", help="Cross-platform username search only")
    parser.add_argument("--ghack", "-g", help="Google Hacker: mine comments/mentions for a username")
    parser.add_argument("--cookies", "-c", default="acc.txt", help="Cookies file")
    parser.add_argument("--tor", "-t", action='store_true', help="Use Tor proxy")
    parser.add_argument("--all-posts", action='store_true', help="Fetch ALL posts (paginated)")
    parser.add_argument("--skip-platforms", action='store_true', help="Skip cross-platform search")
    parser.add_argument("--skip-friends", action='store_true', help="Skip mutuals analysis")
    parser.add_argument("--skip-comments", action='store_true', help="Skip comments extraction")
    parser.add_argument("--skip-image", action='store_true', help="Skip profile pic + reverse image search")
    parser.add_argument("--skip-ghack", action='store_true', help="Skip Google Hacker module")
    parser.add_argument("--tz", type=int, default=0, help="Local timezone offset from UTC (e.g. 1 for Morocco GMT+1)")
    args = parser.parse_args()

    if args.image:
        standalone_reverse_image(args.image)
    elif args.search:
        standalone_username_search(args.search)
    elif args.ghack:
        standalone_google_hack(args.ghack)
    elif args.username:
        InstagramOSINT(
            username=args.username,
            cookies_file=args.cookies,
            use_tor=args.tor,
            all_posts=args.all_posts,
            skip_platforms=args.skip_platforms,
            skip_friends=args.skip_friends,
            skip_comments=args.skip_comments,
            skip_image=args.skip_image,
            skip_ghack=args.skip_ghack,
            tz=args.tz,
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
