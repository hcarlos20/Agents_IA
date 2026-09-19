"""
Agent 1 - Collecteur
Récupère les items des dernières 24h depuis des sources RSS + APIs gratuites.
Sortie : liste de dicts {title, link, source, published, excerpt}
"""
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from time import mktime

# --- Sources RSS (IA + cybersécurité) ---
RSS_SOURCES = {
    "Anthropic Blog": "https://www.anthropic.com/rss.xml",
    "Google DeepMind Blog": "https://deepmind.google/blog/rss.xml",
    "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
    "ArXiv cs.AI": "http://export.arxiv.org/rss/cs.AI",
    "ArXiv cs.CR": "http://export.arxiv.org/rss/cs.CR",
}

HOURS_WINDOW = 24  # ne garder que les items des dernières 24h


def _parse_entry_date(entry):
    """Retourne un datetime timezone-aware, ou None si non trouvé."""
    for field in ("published_parsed", "updated_parsed"):
        struct = getattr(entry, field, None)
        if struct:
            return datetime.fromtimestamp(mktime(struct), tz=timezone.utc)
    return None


def fetch_rss(source_name, url, cutoff):
    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            published = _parse_entry_date(entry)
            if published and published < cutoff:
                continue
            items.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
                "source": source_name,
                "published": published.isoformat() if published else None,
                "excerpt": (entry.get("summary", "") or "")[:400],
            })
    except Exception as e:
        print(f"[collector] Erreur sur la source '{source_name}': {e}")
    return items


def fetch_hackernews_ai_security(cutoff, keywords=None):
    """Récupère les top stories HN et filtre par mots-clés IA/cybersec."""
    keywords = keywords or [
        "ai", "llm", "gpt", "claude", "gemini", "model", "cyber", "security",
        "vulnerability", "exploit", "breach", "cve", "hacking", "ransomware",
    ]
    items = []
    try:
        # On limite à 25 stories (au lieu de 60) et on réduit le timeout par requête :
        # avec 60 requêtes séquentielles à 10s de timeout chacune, un run pouvait
        # traîner jusqu'à 10 minutes si plusieurs requêtes étaient lentes.
        top_ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=8
        ).json()[:25]
        session = requests.Session()
        for story_id in top_ids:
            try:
                story = session.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=4
                ).json()
            except requests.exceptions.RequestException:
                continue
            if not story or "title" not in story:
                continue
            title_lower = story["title"].lower()
            if not any(k in title_lower for k in keywords):
                continue
            published = datetime.fromtimestamp(story.get("time", 0), tz=timezone.utc)
            if published < cutoff:
                continue
            items.append({
                "title": story["title"],
                "link": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                "source": "Hacker News",
                "published": published.isoformat(),
                "excerpt": "",
            })
    except Exception as e:
        print(f"[collector] Erreur sur Hacker News: {e}")
    return items


def collect_all():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)
    all_items = []

    for name, url in RSS_SOURCES.items():
        all_items.extend(fetch_rss(name, url, cutoff))

    all_items.extend(fetch_hackernews_ai_security(cutoff))

    print(f"[collector] {len(all_items)} items bruts récupérés depuis {len(RSS_SOURCES) + 1} sources.")
    return all_items


if __name__ == "__main__":
    import json
    results = collect_all()
    print(json.dumps(results, indent=2, ensure_ascii=False))
