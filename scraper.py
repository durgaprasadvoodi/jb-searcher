#!/usr/bin/env python3
"""
Headless scraper for offcampusjobdrives.com - designed to run in GitHub Actions.
No GUI dependencies (no tkinter) so it runs fine on a headless runner.

Scrapes the homepage + Fresher Jobs category, checks each post for 0-2 year
experience phrasing, and merges results into data/jobs.json (deduplicated,
keeping the earliest "first_seen" date for jobs already known).

Usage:
    python3 scraper.py --pages 2
"""

import argparse
import json
import os
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://offcampusjobdrives.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobScraperBot/1.0)"}
DATA_PATH = os.path.join(os.path.dirname(__file__), "docs", "data", "jobs.json")

EXPERIENCE_PATTERNS = [
    r"\b0\s*(?:-|to)\s*2\s*years?\b",
    r"\b0\s*(?:-|to)\s*1\s*years?\b",
    r"\bfresher[s']?\b",
    r"\bentry[\s-]?level\b",
    r"\b0\s*years?\s*(?:of\s*)?experience\b",
    r"\bno\s*experience\s*(?:required|needed)?\b",
    r"\b1\s*(?:-|to)\s*2\s*years?\b",
    r"\bless\s*than\s*2\s*years?\b",
    r"\bup\s*to\s*2\s*years?\b",
]
EXPERIENCE_RE = re.compile("|".join(EXPERIENCE_PATTERNS), re.IGNORECASE)


def get_soup(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:
            print(f"  Retry {attempt+1}/{retries} for {url}: {e}")
            time.sleep(delay)
    return None


def collect_listing_links(pages=1, category=None):
    links = []
    base = f"{BASE_URL}/category/{category}/" if category else f"{BASE_URL}/"
    for page in range(1, pages + 1):
        url = base if page == 1 else f"{base}page/{page}/"
        print(f"Fetching listing page: {url}")
        soup = get_soup(url)
        if soup is None:
            continue
        for h2 in soup.select("h2 a[href]"):
            href = h2.get("href")
            title = h2.get_text(strip=True)
            if href and href.startswith(BASE_URL) and "/category/" not in href:
                links.append((title, href))
        time.sleep(1)
    seen, unique = set(), []
    for title, href in links:
        if href not in seen:
            seen.add(href)
            unique.append((title, href))
    return unique


def check_experience(title, link):
    soup = get_soup(link)
    if soup is None:
        return None
    article = soup.find("article") or soup
    text = article.get_text(" ", strip=True)
    match = EXPERIENCE_RE.search(text)
    return {
        "title": title,
        "link": link,
        "first_seen": datetime.now().strftime("%Y-%m-%d"),
        "experience_match": match.group(0) if match else "",
        "matched": bool(match),
        "snippet": text[:300],
    }


def load_existing():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=2)
    args = parser.parse_args()

    existing = load_existing()  # keyed by link
    print(f"Loaded {len(existing)} existing job(s) from {DATA_PATH}")

    homepage_links = collect_listing_links(pages=args.pages)
    fresher_links = collect_listing_links(pages=args.pages, category="fresher-jobs")
    all_links = homepage_links + fresher_links
    seen, unique_links = set(), []
    for title, href in all_links:
        if href not in seen:
            seen.add(href)
            unique_links.append((title, href))

    print(f"Found {len(unique_links)} unique job posts. Checking each...")
    new_count = 0
    for i, (title, link) in enumerate(unique_links):
        if link in existing:
            continue  # already have it, don't re-fetch or overwrite first_seen
        print(f"  [{i+1}/{len(unique_links)}] {title}")
        info = check_experience(title, link)
        if info:
            existing[link] = info
            new_count += 1
        time.sleep(1)

    save_data(existing)
    matched_total = sum(1 for v in existing.values() if v["matched"])
    print(f"\nDone. {new_count} new job(s) added this run.")
    print(f"Total jobs stored: {len(existing)} ({matched_total} matching 0-2 yr experience).")


if __name__ == "__main__":
    main()
