#!/usr/bin/env python3
"""Fetch free HTTP(S) proxies, verify them against instagram.com, write good ones to proxies.txt.

Usage:
    python3 fetch_proxies.py [--limit N]

Instagram rate-limits/blocks some IPs. A fresh list of working proxies helps the
Comment Hunter (-g) bypass IP-based search/feed blocks. Refresh proxies.txt regularly
(free proxies die fast). Add premium proxies manually to proxies.txt (one per line).
"""

import argparse
import sys
import threading
import time

import requests

SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://api.proxyscrape.com/v3/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all",
]

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"


def fetch_all():
    seen, out = set(), []
    for src in SOURCES:
        try:
            r = requests.get(src, timeout=25)
            for line in r.text.splitlines():
                line = line.strip()
                if line and line not in seen:
                    seen.add(line)
                    out.append(line)
        except Exception:
            pass
    return out


def verify(proxy):
    p = proxy if "://" in proxy else f"http://{proxy}"
    try:
        r = requests.get(
            "https://www.instagram.com/api/v1/web/search/topsearch/?query=test&context=blended",
            proxies={"http": p, "https": p},
            headers={"User-Agent": UA},
            timeout=6,
        )
        if r.status_code == 200 and r.text.strip().startswith("{"):
            return proxy
    except Exception:
        pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20, help="max proxies to verify")
    args = ap.parse_args()

    print("[*] fetching proxy list ...")
    proxies = fetch_all()
    print(f"[*] {len(proxies)} raw proxies fetched, verifying against instagram.com ...")

    good = []
    lock = threading.Lock()

    def worker(p):
        if verify(p):
            with lock:
                good.append(p)
                print(f"  [+] OK {p}")

    threads = []
    for p in proxies[: args.limit * 4]:
        t = threading.Thread(target=worker, args=(p,))
        t.start()
        threads.append(t)
        if len(threads) >= 60:
            for t in threads:
                t.join()
            threads = []
            if len(good) >= args.limit:
                break
    for t in threads:
        t.join()

    with open("proxies.txt", "w") as f:
        f.write("# free proxies - refresh with: python3 fetch_proxies.py\n")
        for p in good:
            f.write(p + "\n")

    print(f"\n[*] {len(good)} working proxies -> proxies.txt")
    for p in good:
        print(f"    {p}")


if __name__ == "__main__":
    main()
