"""Collect official RSS feeds without third-party services or dependencies."""
import concurrent.futures
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
CATEGORIES = [
    ("房地合一／不動產", r"房地合一|房屋稅|地價稅|土地增值稅|契稅"),
    ("遺產及贈與稅", r"遺產|贈與"),
    ("營利事業所得稅", r"營利事業所得稅|營所稅|未分配盈餘|營利事業"),
    ("綜合所得稅", r"綜合所得稅|綜所稅|個人所得|扣除額|扣繳"),
    ("營業稅", r"營業稅|發票|稅籍"),
    ("其他稅務", r"稅|租稅|稽徵"),
]

def clean(value):
    value = re.sub(r"<script\b[^>]*>.*?</script>", "", value or "", flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def canonical(url):
    parts = urllib.parse.urlsplit(html.unescape(url.strip()))
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("Invalid article URL")
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not k.lower().startswith("utm_")]
    return urllib.parse.urlunsplit(("https", parts.netloc.lower(), parts.path, urllib.parse.urlencode(sorted(query)), ""))

def date_string(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (ValueError, TypeError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            match = re.match(r"^(\d{3,4})[/-](\d{1,2})[/-](\d{1,2})$", value)
            if not match:
                return None
            year, month, day = map(int, match.groups())
            try:
                dt = datetime(year + 1911 if year < 1911 else year, month, day)
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ).date().isoformat()

def parse_feed(raw, source, now):
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("Unsupported XML declarations")
    root = ET.fromstring(raw)
    if root.tag != "rss":
        raise ValueError("Response is not an RSS feed")
    nodes = root.findall("./channel/item")
    if not nodes:
        raise ValueError("RSS feed unexpectedly contains no items")
    articles = []
    for item in nodes:
        title = clean(item.findtext("title"))
        body = clean(item.findtext("description"))
        link = item.findtext("link")
        if not title or not link:
            continue
        try:
            url = canonical(link)
        except ValueError:
            continue
        if source.get("taxOnly") and not re.search(r"稅|發票|稽徵", title + body):
            continue
        category = next((name for name, pattern in CATEGORIES if re.search(pattern, title)), None)
        if not category:
            category = next((name for name, pattern in CATEGORIES if re.search(pattern, body)), "其他稅務")
        excerpt = body[:200] + ("…" if len(body) > 200 else "")
        articles.append({"id": hashlib.sha256(url.encode()).hexdigest()[:20], "url": url,
            "title": title, "date": date_string(item.findtext("pubDate")),
            "source": source["name"], "sourceId": source["id"], "category": category,
            "summary": excerpt, "summaryType": "官方摘要節錄" if excerpt else "僅提供原文連結",
            "firstSeen": now, "contentHash": hashlib.sha256((title + body).encode()).hexdigest()})
    return articles

def fetch_source(source, now):
    for attempt in range(3):
        try:
            request = urllib.request.Request(source["url"], headers={"User-Agent": "TaiwanTaxDaily/1.0 RSS reader"})
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(5_000_001)
            if len(raw) > 5_000_000:
                raise ValueError("RSS feed too large")
            return parse_feed(raw, source, now)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def merge_articles(existing, incoming):
    # URL identity preserves old entries even after they disappear from the feed.
    merged = {a["url"]: a for a in existing}
    for article in incoming:
        old = merged.get(article["url"])
        if old:
            article = {**article, "firstSeen": old["firstSeen"]}
        merged[article["url"]] = article
    return sorted(merged.values(), key=lambda a: (a["date"] or "", a["url"]), reverse=True)

def main():
    path = ROOT / "data/articles.json"
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"articles": [], "sources": []}
    sources = json.loads((ROOT / "config/sources.json").read_text(encoding="utf-8"))
    now = datetime.now(TZ).isoformat(timespec="seconds")
    incoming, states = [], []
    previous = {s["id"]: s for s in existing.get("sources", [])}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch_source, s, now): s for s in sources}
        for future in concurrent.futures.as_completed(futures):
            s = futures[future]
            try:
                items = future.result()
                incoming.extend(items)
                states.append({**s, "status": "ok", "count": len(items), "lastSuccess": now})
                print(f'{s["id"]}: {len(items)} articles')
            except Exception as error:
                states.append({**s, "status": "error", "lastSuccess": previous.get(s["id"], {}).get("lastSuccess")})
                print(f'::warning::{s["id"]}: {type(error).__name__}: {error}')
    if all(s["status"] == "error" for s in states):
        raise RuntimeError("All sources failed. Existing archive and published site preserved.")
    articles = merge_articles(existing["articles"], incoming)
    result = {"updatedAt": now, "sources": sorted(states, key=lambda s: s["id"]), "articles": articles}
    path.parent.mkdir(exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    print(f"Archive: {len(articles)} articles; {len(articles) - len(existing['articles'])} new")

if __name__ == "__main__":
    main()
