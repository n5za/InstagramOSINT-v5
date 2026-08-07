# Instagram OSINT v5

Professional Instagram OSINT investigation suite by n5za.

## Features

- **Full account investigation** - profile, posts, engagement metrics, mutual friends, comments
- **Comment Hunter** (`-g`) - pulls the target's reels/posts straight from Instagram's GraphQL
  API and extracts the **real comment texts** people wrote on them (no search-engine scraping)
- **Reverse image search** - 7 engines, plus automated similarity matching (>= 80%)
- **Image match tool** (`imgmatch.py`) - find Instagram accounts using the same picture
  - Perceptual hashing (pHash) similarity detection
  - Searches Bing, DuckDuckGo, Google + photo-ID text queries
  - Verifies every candidate account's profile pic against the source (>= 80% match)
  - Generates an HTML report with matched accounts + links + manual search shortcuts
- **Cross-platform username search** - 50+ platforms checked concurrently + Google dorks
- **Engagement analysis** - engagement rate, posting frequency, best hours, top hashtags
- **Business contact info** - public email, phone, address, website, category
- **Smart resolution** - falls back to `web_profile_info` and shows "did you mean" candidates
- **Private-account aware** - skips inaccessible data gracefully

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Full investigation of an Instagram account
python3 main.py -u USERNAME

# Fetch ALL posts (paginated), not just the latest 12
python3 main.py -u USERNAME --all-posts

# Comment Hunter: pull the target's reels/posts + the comments people wrote on them
python3 main.py -g USERNAME

# Standalone reverse image search on any image URL
python3 main.py -i "https://example.com/image.jpg"

# Cross-platform username search only
python3 main.py -s USERNAME

# Find Instagram accounts using the same picture (>= 80% match)
python3 imgmatch.py -i "https://example.com/image.jpg"
```

### Speed / module control

```bash
# Skip slow modules to finish faster
python3 main.py -u USERNAME --skip-platforms --skip-friends --skip-comments --skip-image --skip-ghack

# Local timezone offset for "best hour" (Morocco = +1)
python3 main.py -u USERNAME --tz 1
```

Optional: drop a `google_abuse.txt` file containing a `GOOGLE_ABUSE_EXEMPTION=...` value to
avoid Google CAPTCHA during the Google Hacker module.

### Cookies

Create `acc.txt` in the tool directory (one cookie per line, from browser devtools):

```
ds_user_id=123456789
sessionid=...
csrftoken=...
```

**Netscape-format cookie files are also supported** (tab-separated `domain\tflag\tpath\tsecure\texpiry\tname\tvalue`,
as exported by browser extensions) — both formats are parsed automatically.

Without valid cookies, profile data access is limited (Instagram login wall + API rate limits).

## Output

Each investigation creates a timestamped folder:

- `report.html` - full HTML report
- `data.json` - raw investigation data
- `profile_pic.jpg` - downloaded profile picture
- `friends.txt`, `cross_platform.txt`, `google_hacker.txt`, `dork_searches.txt` - link lists
- `google_hack_<username>.txt` - Comment Hunter report: every post + the extracted comments
- `reverse_image_search_urls.txt` - all engine search links

Image match runs create `imgmatch_<timestamp>/` with `report.html`, `matches.json`, `matches_links.txt`, `source.jpg`.

## Disclaimer

For educational and authorized security research only. Respect Instagram's ToS and privacy.
