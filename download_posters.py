"""
Download movie/show poster images using TMDB's public API (no API key needed for find-by-imdb-id
via the /find endpoint, but we do need a key for full use). We'll use the public TMDB
image CDN with a known working approach: find by IMDB ID using the TMDB find endpoint
with the public guest API key pattern, or fall back to scraping TMDB's own title page.

Strategy:
1. Use TMDB /find/{imdb_id}?external_source=imdb_id to get the TMDB poster path
   (TMDB requires an API key — we'll use the well-known public read-access token approach
    by requesting without auth and parsing their open meta tags instead)
2. Fetch https://www.themoviedb.org/movie/{tmdb_id} or /tv/{tmdb_id} and extract og:image
3. Fall back to fetching TMDB search page directly

Actually simplest approach: TMDB pages have og:image in their HTML without bot protection.
We fetch https://www.themoviedb.org/find/{imdb_id}?language=en-US&external_source=imdb_id
or just https://www.themoviedb.org/title pages directly.

Let's use the TMDB "find" redirect: GET https://www.themoviedb.org/{imdb_id} sometimes redirects.
Better: use their public /find API page which returns an HTML page, or use the image.tmdb.org
CDN with known patterns.

Cleanest free approach: scrape og:image from https://www.themoviedb.org/movie/...
after first finding the TMDB ID via their search HTML page.

Even cleaner: TMDB has a public API with a free key — let's register-free approach:
GET https://api.themoviedb.org/3/find/{imdb_id}?api_key=&external_source=imdb_id
doesn't work without a key.

Best approach without a key: fetch the TMDB browse page for the IMDB ID.
TMDB redirects https://www.themoviedb.org/title/{imdb_id} to the correct page.
"""

import os
import re
import time
import urllib.request
import urllib.parse
import gzip
from html.parser import HTMLParser

ASSETS_DIR = r"C:\Users\Lindsay\FA_website\assets"

# (filename, title, imdb_id)
FILMS = [
    ("prisoner-of-war.jpg",            "Prisoner of War",              "tt33057137"),
    ("states-of-mind.jpg",             "States of Mind",               "tt23745590"),
    ("heat.jpg",                       "Heat (2023 AU mini-series)",   "tt23396642"),
    ("shayda.jpg",                     "Shayda",                       "tt13200006"),
    ("the-convert.jpg",                "The Convert",                  "tt20113412"),
    ("true-lies.jpg",                  "True Lies (2023 CBS series)",  "tt7380366"),
    ("under-the-banner-of-heaven.jpg", "Under the Banner of Heaven",   "tt1998372"),
    ("being-the-ricardos.jpg",         "Being the Ricardos",           "tt4995540"),
    ("fires.jpg",                      "Fires (2021 ABC Australia)",   "tt14418052"),
    ("why-women-kill-s2.jpg",          "Why Women Kill Season 2",      "tt9054904"),
    ("sonic-the-hedgehog.jpg",         "Sonic the Hedgehog",           "tt3794354"),
    ("the-thing-about-harry.jpg",      "The Thing About Harry",        "tt11324534"),
    ("glitch-s3.jpg",                  "Glitch Season 3",              "tt4192782"),
    ("reef-break.jpg",                 "Reef Break",                   "tt8892926"),
    ("the-fix.jpg",                    "The Fix",                      "tt7942774"),
    ("the-whistleblower.jpg",          "The Whistleblower",            "tt8971476"),
    ("why-women-kill-s1.jpg",          "Why Women Kill Season 1",      "tt9054904"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


class OGImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.og_image = None

    def handle_starttag(self, tag, attrs):
        if self.og_image:
            return
        if tag == "meta":
            attrs_dict = dict(attrs)
            prop = attrs_dict.get("property", "") or attrs_dict.get("name", "")
            if prop == "og:image":
                self.og_image = attrs_dict.get("content")


def fetch_html(url, extra_headers=None):
    headers = dict(HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            final_url = resp.geturl()
            enc = resp.headers.get("Content-Encoding", "")
            if enc == "gzip":
                raw = gzip.decompress(raw)
            return raw.decode("utf-8", errors="replace"), final_url, None
    except urllib.error.HTTPError as e:
        return None, None, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return None, None, str(e)


def extract_og_image(html):
    parser = OGImageParser()
    parser.feed(html)
    return parser.og_image


def get_poster_via_tmdb_page(imdb_id):
    """
    Fetch https://www.themoviedb.org/title/{imdb_id} which redirects to the correct
    movie or TV show page. Then extract og:image.
    """
    url = f"https://www.themoviedb.org/title/{imdb_id}"
    html, final_url, err = fetch_html(url)
    if err:
        return None, f"TMDB title page error: {err}"
    if not html:
        return None, "TMDB title page: empty response"

    og_image = extract_og_image(html)
    if og_image:
        # TMDB og:image is typically the poster — upgrade to higher res
        # Pattern: https://media.themoviedb.org/t/p/w600_and_h900_bestv2/...
        # Upgrade to original
        og_image = re.sub(r'/t/p/w\d+_and_h\d+[^/]*/', '/t/p/original/', og_image)
        og_image = re.sub(r'/t/p/w\d+/', '/t/p/original/', og_image)
        return og_image, None

    return None, f"og:image not found on TMDB page (landed at: {final_url})"


def get_poster_via_tmdb_search(title, year_hint=None):
    """
    Fall back: search TMDB and grab first result's poster.
    """
    query = urllib.parse.quote(title)
    url = f"https://www.themoviedb.org/search?query={query}"
    html, final_url, err = fetch_html(url)
    if err:
        return None, f"TMDB search error: {err}"
    if not html:
        return None, "TMDB search: empty response"

    # Look for poster image in search results — find first poster URL
    # Pattern in TMDB search HTML: src="https://media.themoviedb.org/t/p/w.../.jpg"
    patterns = [
        r'src="(https://media\.themoviedb\.org/t/p/[^"]+\.jpg)"',
        r'src="(https://www\.themoviedb\.org/t/p/[^"]+\.jpg)"',
        r'content="(https://(?:media|www)\.themoviedb\.org/t/p/[^"]+\.jpg)"',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            url = m.group(1)
            url = re.sub(r'/t/p/w\d+_and_h\d+[^/]*/', '/t/p/original/', url)
            url = re.sub(r'/t/p/w\d+/', '/t/p/original/', url)
            return url, None

    return None, "No poster found in TMDB search results"


def download_image(image_url, dest_path):
    headers = dict(HEADERS)
    headers["Referer"] = "https://www.themoviedb.org/"
    req = urllib.request.Request(image_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        # Validate it's actually an image (check magic bytes)
        if len(data) < 100:
            return None, f"Response too small ({len(data)} bytes) — probably not an image"
        if not (data[:3] == b'\xff\xd8\xff' or  # JPEG
                data[:8] == b'\x89PNG\r\n\x1a\n' or  # PNG
                data[:4] == b'RIFF'):  # WebP (RIFF header)
            # Try to decode as text to see what we got
            snippet = data[:200].decode('utf-8', errors='replace')
            return None, f"Not a valid image file. Got: {snippet[:100]}"
        with open(dest_path, "wb") as f:
            f.write(data)
        return len(data) // 1024, None
    except Exception as e:
        return None, f"Download error: {e}"


def main():
    succeeded = []
    failed = []

    for filename, title, imdb_id in FILMS:
        dest_path = os.path.join(ASSETS_DIR, filename)

        if os.path.exists(dest_path):
            print(f"[SKIP]    {title} — {filename} already exists")
            succeeded.append((filename, title, "already existed"))
            continue

        print(f"\n[FETCH]   {title} (IMDB: {imdb_id})")

        # Try 1: TMDB title redirect
        image_url, err = get_poster_via_tmdb_page(imdb_id)
        if err:
            print(f"  TMDB title page failed: {err}")
            # Try 2: TMDB search
            image_url, err2 = get_poster_via_tmdb_search(title)
            if err2:
                print(f"  TMDB search also failed: {err2}")
                failed.append((filename, title, f"TMDB title: {err} | Search: {err2}"))
                time.sleep(1)
                continue
            else:
                print(f"  Found via TMDB search: {image_url[:80]}...")
        else:
            print(f"  Found via TMDB title: {image_url[:80]}...")

        size_kb, err = download_image(image_url, dest_path)
        if err:
            print(f"  Download FAILED: {err}")
            # Try non-original resolution as fallback
            fallback_url = image_url.replace('/t/p/original/', '/t/p/w500/')
            if fallback_url != image_url:
                print(f"  Trying fallback resolution: {fallback_url[:80]}...")
                size_kb, err2 = download_image(fallback_url, dest_path)
                if err2:
                    print(f"  Fallback also failed: {err2}")
                    failed.append((filename, title, err))
                    time.sleep(1)
                    continue
                else:
                    print(f"  OK (fallback): saved {filename} ({size_kb} KB)")
                    succeeded.append((filename, title, f"{size_kb} KB (fallback res)"))
            else:
                failed.append((filename, title, err))
        else:
            print(f"  OK: saved {filename} ({size_kb} KB)")
            succeeded.append((filename, title, f"{size_kb} KB"))

        time.sleep(1.2)  # polite delay

    print("\n" + "=" * 65)
    print(f"SUCCEEDED ({len(succeeded)}):")
    for f, t, note in succeeded:
        print(f"  {f:45s} {note}")

    print(f"\nFAILED ({len(failed)}):")
    for f, t, reason in failed:
        print(f"  {f:45s} {reason[:80]}")


if __name__ == "__main__":
    main()
