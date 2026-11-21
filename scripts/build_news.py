import datetime as dt
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEEDS = {
    "AIニュース": [
        ("OpenAI", "https://openai.com/news/rss.xml"),
        ("Google Research", "https://blog.research.google/feeds/posts/default?alt=rss"),
    ],
    "ITニュース": [
        ("GitHub", "https://github.blog/feed/"),
        ("Cloudflare", "https://blog.cloudflare.com/rss/"),
        ("Microsoft", "https://blogs.microsoft.com/feed/"),
    ],
}
CRYPTO_WORDS = re.compile(
    r"\b(crypto(?:currency)?|bitcoin|btc|ethereum|\beth\b|nft|"
    r"blockchain|token price|cryptocurrency|defi|web3)\b",
    re.IGNORECASE,
)

def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return html.unescape(re.sub(r"\s+", " ", value)).strip()

def parse_date(value):
    if not value:
        return dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed
    except (TypeError, ValueError):
        return dt.datetime.min.replace(tzinfo=dt.timezone.utc)

def read_feed(source, url):
    request = urllib.request.Request(url, headers={"User-Agent": "DailyTechNews/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            root = ET.fromstring(response.read())
        entries = []
        for item in root.findall(".//item"):
            title = clean_text(item.findtext("title"))
            link = (item.findtext("link") or "").strip()
            description = clean_text(item.findtext("description"))
            pub_date = item.findtext("pubDate")
            if not title or not link or CRYPTO_WORDS.search(title + " " + description):
                continue
            entries.append({
                "source": source,
                "title": title,
                "link": link,
                "summary": description[:260],
                "date": parse_date(pub_date),
            })
        # Atom feeds
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for item in root.findall(".//a:entry", ns):
            title = clean_text(item.findtext("a:title", default="", namespaces=ns))
            link_node = item.find("a:link", ns)
            link = link_node.get("href", "") if link_node is not None else ""
            summary = clean_text(item.findtext("a:summary", default="", namespaces=ns))
            updated = item.findtext("a:updated", default="", namespaces=ns)
            if title and link and not CRYPTO_WORDS.search(title + " " + summary):
                try:
                    date = dt.datetime.fromisoformat(updated.replace("Z", "+00:00"))
                except ValueError:
                    date = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
                entries.append({
                    "source": source, "title": title, "link": link,
                    "summary": summary[:260], "date": date,
                })
        return entries
    except Exception as exc:
        print(f"[WARN] {source}: {exc}")
        return []

def render(items):
    today = dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y年%m月%d日")
    sections = []
    for category in FEEDS:
        cards = []
        for item in items.get(category, []):
            title = html.escape(item["title"])
            summary = html.escape(item["summary"] or "概要は配信元の記事をご確認ください。")
            source = html.escape(item["source"])
            link = html.escape(item["link"], quote=True)
            date = item["date"].astimezone().strftime("%Y/%m/%d") if item["date"].year > 1 else ""
            cards.append(f"""
            <article class="item">
              <div class="meta">{source}　{date}</div>
              <h3><a href="{link}" target="_blank" rel="noopener">{title}</a></h3>
              <p>{summary}</p>
            </article>""")
        content = "".join(cards) or '<p class="empty">現在、掲載できるニュースはありません。</p>'
        sections.append(f'<section><h2>{category}</h2><div class="items">{content}</div></section>')

    page = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="AIとITの最新ニュースを毎日チェック">
<title>Daily Tech News</title>
<style>
:root{{--bg:#f5f7fb;--card:#fff;--text:#172033;--muted:#687386;--accent:#3457d5}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,""Segoe UI"",sans-serif;line-height:1.65}}
header{{background:#111a32;color:white;padding:42px 20px}}.wrap{{max-width:900px;margin:auto}}
h1{{font-size:clamp(28px,5vw,42px);margin:0}}header p{{color:#c9d2e7;margin:8px 0 0}}
main{{padding:24px 16px 60px}}section{{margin:24px 0 36px}}h2{{font-size:23px;border-left:5px solid var(--accent);padding-left:12px}}
.items{{display:grid;gap:14px}}.item{{background:var(--card);padding:18px 20px;border-radius:14px;box-shadow:0 3px 14px #18264a0b}}
.item h3{{font-size:18px;line-height:1.45;margin:6px 0}}a{{color:var(--accent);text-decoration:none}}a:hover{{text-decoration:underline}}
.item p{{color:#465166;margin:8px 0 0}}.meta,.empty,footer{{color:var(--muted);font-size:13px}}
footer{{text-align:center;padding:24px}}
</style></head><body>
<header><div class="wrap"><h1>Daily Tech News</h1><p>AIとITの動きを、毎日わかりやすく。</p><p>更新日：{today}</p></div></header>
<main class="wrap">{''.join(sections)}</main>
<footer>Sources:各ニュース配信元 / 自動収集したRSSを掲載しています。</footer>
</body></html>"""
    with open("index.html", "w", encoding="utf-8") as file:
        file.write(page)

def main():
    collected = {}
    for category, feeds in FEEDS.items():
        entries = []
        for source, url in feeds:
            entries.extend(read_feed(source, url))
        # Sort newest first and remove duplicate links
        unique = {entry["link"]: entry for entry in entries}
        collected[category] = sorted(
            unique.values(), key=lambda entry: entry["date"], reverse=True
        )[:12]
    render(collected)
    print("index.html generated")

if __name__ == "__main__":
    main()
