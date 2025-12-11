# tools/arxiv_tools.py
import feedparser
from datetime import datetime, timezone
from typing import List, Dict

ARXIV_BASE_RSS = "http://export.arxiv.org/rss/"

def fetch_category_rss(category_tag: str, max_items: int = 50) -> List[Dict]:
    """Fetch and parse arXiv RSS for a category like 'cs.AI'."""
    feed_url = ARXIV_BASE_RSS + category_tag
    d = feedparser.parse(feed_url)
    items = []
    for entry in d.entries[:max_items]:
        # entry.published_parsed may be None in edge cases
        pub = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
        items.append({
            'id': entry.get('id'),
            'title': entry.get('title'),
            'link': entry.get('link'),
            'summary': entry.get('summary'),
            'published': pub,
            'tags': [t.term for t in entry.get('tags', [])] if 'tags' in entry else [],
        })
    return items

def todays_papers_for_categories(categories: List[str]) -> Dict[str, List[Dict]]:
    """Return dict: category -> list of entries (filtering to 'today' optional)."""
    result = {}
    for cat in categories:
        result[cat] = fetch_category_rss(cat)
    return result
