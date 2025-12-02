from __future__ import annotations

"""Topic-based image discovery orchestrator (skeleton for Phase 1).

Future responsibilities (subsequent tasks):
- Query search provider(s)
- Parse result pages and extract image URLs
- Respect robots.txt for pages (Phase 2+)
- Write deterministic query logs (US1 T013)
- Produce provenance entries
"""

from typing import List, Tuple
import logging
import json
import os
import re
from datetime import datetime

from .models_discovery import ProvenanceEntry, PreviewResult, QueryLogEntry
from .image_scraper import robots_allowed, list_images
from . import search_provider

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "duckduckgo"

_DISCOVERY_LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "discovery_logs"))


def _slugify_topic(topic: str) -> str:
    s = topic.strip().lower()
    s = re.sub(r"[^a-z0-9\-\_\sぁ-んァ-ヶ一-龥]", " ", s)
    s = re.sub(r"\s+", "_", s)
    return s[:60] if s else "topic"


def discover_topic(topic: str, limit: int = 50) -> PreviewResult:
    """Discover images for a topic using a search provider and return a preview.

    - Queries provider for candidate pages
    - Respects robots.txt for pages and images (via list_images)
    - Builds ProvenanceEntry list up to `limit`
    - Writes deterministic query log to discovery_logs
    """
    logger.info("discover_topic.start topic=%s limit=%d provider=%s", topic, limit, DEFAULT_PROVIDER)
    # 1) Search pages via provider (mockable)
    try:
        page_urls = search_provider.search_pages(topic, provider=DEFAULT_PROVIDER, max_pages=20)
    except Exception as e:
        logger.warning("search_provider.error topic=%s err=%s", topic, e)
        page_urls = []

    images_collected: List[ProvenanceEntry] = []
    pages_considered = 0
    for page in page_urls:
        if limit and len(images_collected) >= limit:
            break
        pages_considered += 1
        if not robots_allowed(page):
            logger.warning("robots page disallow: %s", page)
            continue
        try:
            remaining = None if not limit else max(0, limit - len(images_collected))
            # Reuse existing listing logic which also respects robots for images when requested
            urls = list_images(page, limit=None, respect_robots=True)
        except Exception as e:
            logger.warning("list_images.failed page=%s err=%s", page, e)
            continue
        for u in urls:
            if limit and len(images_collected) >= limit:
                break
            images_collected.append(
                ProvenanceEntry(
                    topic=topic,
                    source_page_url=page,
                    image_url=u,
                    discovery_method="SERP",
                )
            )

    query_log = QueryLogEntry(
        topic=topic,
        provider=DEFAULT_PROVIDER,
        query=topic,
        page_count=pages_considered,
        image_count=len(images_collected),
    )

    # 2) Write deterministic query log
    try:
        os.makedirs(_DISCOVERY_LOG_DIR, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d")
        fn = f"{ts}_{_slugify_topic(topic)}.json"
        path = os.path.join(_DISCOVERY_LOG_DIR, fn)
        payload = {
            "topic": topic,
            "provider": DEFAULT_PROVIDER,
            "query": topic,
            "timestamp": query_log.timestamp.isoformat(),
            "page_count": pages_considered,
            "image_count": len(images_collected),
            "pages": page_urls,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.info("query_log.written path=%s", path)
    except Exception as e:
        logger.warning("query_log.write_failed topic=%s err=%s", topic, e)

    result = PreviewResult(
        topic=topic,
        entries=images_collected,
        total_images=len(images_collected),
        provider=DEFAULT_PROVIDER,
        query_log=query_log,
    )
    logger.info("discover_topic.end topic=%s count=%d", topic, result.total_images)
    return result
