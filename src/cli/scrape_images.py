#!/usr/bin/env python3
"""CLI to scrape image URLs from a page and save them locally, with optional Drive upload.

Usage:
  python -m src.cli.scrape_images --url https://example.com --out downloads
  # With Google Drive (service account):
  export GDRIVE_SA_JSON=path/to/service_account.json
  python -m src.cli.scrape_images --url https://example.com --out downloads --drive-folder-id <folder_id>

  # Topic-based discovery (US1: preview only):
  python -m src.cli.scrape_images --topic "富士山"

  # Topic-based discovery with download (US2):
  python -m src.cli.scrape_images --topic "富士山" --download --out images
  python -m src.cli.scrape_images --topic "富士山" --download --deny-domain "example.com,spam.net"
  python -m src.cli.scrape_images --topic "富士山" --download --allow-domain "pixabay.com,unsplash.com"
"""

from __future__ import annotations

import argparse
import json
import os
from typing import List, Optional

from src.lib.image_scraper import _init_drive, scrape_images
from src.lib.models_discovery import DownloadFilter
from src.lib.topic_discovery import discover_topic, download_selected


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape images from a web page and save locally and/or to Google Drive.")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Web page URL to scrape")
    group.add_argument("--topic", help="Topic keyword to discover images")
    p.add_argument(
        "--out", required=False, default="images", help="Local output directory for images (default: images)"
    )
    p.add_argument("--limit", type=int, default=None, help="Optional limit on number of images to download")
    p.add_argument("--drive-folder-id", default=None, help="Optional Google Drive folder ID for upload")
    p.add_argument(
        "--respect-robots",
        action="store_true",
        help="Enforce robots.txt (page + image URLs) and abort/skip when disallowed",
    )
    p.add_argument(
        "--drive-sa-json",
        default=os.getenv("GDRIVE_SA_JSON"),
        help="Path to service account JSON credentials (env GDRIVE_SA_JSON)",
    )

    # US2: Selective download options
    p.add_argument(
        "--download", action="store_true", help="Download images after topic discovery (default: preview only)"
    )
    p.add_argument("--min-width", type=int, default=None, help="Minimum image width in pixels (US2 filter)")
    p.add_argument("--min-height", type=int, default=None, help="Minimum image height in pixels (US2 filter)")
    p.add_argument("--allow-domain", type=str, default=None, help="Comma-separated whitelist of domains (US2 filter)")
    p.add_argument("--deny-domain", type=str, default=None, help="Comma-separated blacklist of domains (US2 filter)")

    return p.parse_args()


def _parse_domain_list(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated domain list."""
    if not value:
        return None
    return [d.strip() for d in value.split(",") if d.strip()]


def main() -> None:
    ns = parse_args()

    drive_service = None
    if ns.drive_folder_id:
        if not ns.drive_sa_json:
            raise SystemExit("--drive-folder-id requires credentials. Set --drive-sa-json or env GDRIVE_SA_JSON.")
        drive_service = _init_drive(ns.drive_sa_json)

    if ns.topic:
        # Topic-based discovery
        preview = discover_topic(ns.topic, limit=ns.limit or 50)

        if ns.download:
            # US2: Apply filters and download
            download_filter = DownloadFilter(
                min_width=ns.min_width,
                min_height=ns.min_height,
                allow_domains=_parse_domain_list(ns.allow_domain),
                deny_domains=_parse_domain_list(ns.deny_domain),
            )

            saved_files, index_path = download_selected(
                entries=preview.entries,
                output_dir=ns.out,
                download_filter=download_filter,
                respect_robots=True,
            )

            print(
                json.dumps(
                    {
                        "mode": "topic_download",
                        "topic": ns.topic,
                        "total_discovered": preview.total_images,
                        "downloaded": len(saved_files),
                        "output_dir": os.path.abspath(ns.out),
                        "provenance_index": index_path,
                        "filters": {
                            "min_width": ns.min_width,
                            "min_height": ns.min_height,
                            "allow_domains": _parse_domain_list(ns.allow_domain),
                            "deny_domains": _parse_domain_list(ns.deny_domain),
                        },
                    },
                    ensure_ascii=False,
                )
            )
        else:
            # US1: Preview only - プロベナンス情報を完全に出力
            print(
                json.dumps(
                    {
                        "mode": "topic_preview",
                        "topic": ns.topic,
                        "total_images": preview.total_images,
                        "provider": preview.provider,
                        "page_count": preview.query_log.page_count,
                        "image_count": preview.query_log.image_count,
                        "entries": [
                            {
                                "topic": e.topic,
                                "image_url": str(e.image_url),
                                "source_page_url": str(e.source_page_url),
                                "discovery_method": e.discovery_method,
                                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                            }
                            for e in preview.entries
                        ],
                    },
                    ensure_ascii=False,
                )
            )
    else:
        result = scrape_images(
            ns.url,
            ns.out,
            limit=ns.limit,
            drive_service=drive_service,
            drive_folder_id=ns.drive_folder_id,
            respect_robots=ns.respect_robots,
        )
        print(
            json.dumps(
                {
                    "mode": "direct_url",
                    "page_url": result.page_url,
                    "found": len(result.image_urls),
                    "downloaded": len(result.saved_files),
                    "drive_uploaded": len(result.drive_file_ids),
                    "output_dir": os.path.abspath(ns.out),
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
