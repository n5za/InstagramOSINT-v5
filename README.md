# Instagram OSINT v5

Professional Instagram OSINT investigation suite by n5za.

## Features

- **Full account investigation** - profile, posts, engagement metrics, mutual friends, comments
- **Reverse image search** - 7 engines, plus automated similarity matching (>= 80%)
- **Image match tool** (`imgmatch.py`) - find Instagram accounts using the same picture
  - Perceptual hashing (pHash) similarity detection
  - Searches Bing, DuckDuckGo, Google + photo-ID text queries
  - Verifies every candidate account's profile pic against the source (>= 80% match)
  - Generates an HTML report with matched accounts + links + manual search shortcuts
- **Cross-platform username search** - 50+ platforms + Google dorks
- **Engagement analysis** - engagement rate, posting frequency, best hours, top hashtags

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Full investigation of an Instagram account
python3 main.py -u USERNAME

# Standalone reverse image search on any image URL
python3 main.py -i "https://example.com/image.jpg"

# Cross-platform username search only
python3 main.py -s USERNAME

# Find Instagram accounts using the same picture (>= 80% match)
python3 imgmatch.py -i "https://example.com/image.jpg"
```

### Cookies

Create `acc.txt` in the tool directory (one cookie per line, from browser devtools):

```
ds_user_id=123456789
sessionid=...
csrftoken=...
```

Without valid cookies, profile data access is limited (Instagram login wall + API rate limits).

## Output

Each investigation creates a timestamped folder:

- `report.html` - full HTML report
- `data.json` - raw investigation data
- `profile_pic.jpg` - downloaded profile picture
- `friends.txt`, `cross_platform.txt`, `dork_searches.txt` - link lists
- `reverse_image_search_urls.txt` - all engine search links

Image match runs create `imgmatch_<timestamp>/` with `report.html`, `matches.json`, `matches_links.txt`, `source.jpg`.

## Disclaimer

For educational and authorized security research only. Respect Instagram's ToS and privacy.
