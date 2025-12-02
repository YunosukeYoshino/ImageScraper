#!/usr/bin/env python3
"""CLI to scrape image URLs from a page and save them locally, with optional Drive upload.

Usage:
  python -m src.cli.scrape_images --url https://example.com --out downloads
  # With Google Drive (service account):
  export GDRIVE_SA_JSON=path/to/service_account.json
  python -m src.cli.scrape_images --url https://example.com --out downloads --drive-folder-id <folder_id>
"""
from __future__ import annotations
import argparse
import json
import os
from typing import Optional

from src.lib.image_scraper import scrape_images, _init_drive
from src.lib.topic_discovery import discover_topic


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape images from a web page and save locally and/or to Google Drive.")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Web page URL to scrape")
    group.add_argument("--topic", help="Topic keyword to discover images (preview only in MVP)")
    p.add_argument("--out", required=False, default="images", help="Local output directory for images (default: images)")
    p.add_argument("--limit", type=int, default=None, help="Optional limit on number of images to download")
    p.add_argument("--drive-folder-id", default=None, help="Optional Google Drive folder ID for upload")
    p.add_argument("--respect-robots", action="store_true", help="Enforce robots.txt (page + image URLs) and abort/skip when disallowed")
    p.add_argument("--drive-sa-json", default=os.getenv("GDRIVE_SA_JSON"), help="Path to service account JSON credentials (env GDRIVE_SA_JSON)")
    return p.parse_args()


def main() -> None:
    ns = parse_args()

    drive_service = None
    if ns.drive_folder_id:
        if not ns.drive_sa_json:
            raise SystemExit("--drive-folder-id requires credentials. Set --drive-sa-json or env GDRIVE_SA_JSON.")
        drive_service = _init_drive(ns.drive_sa_json)

    if ns.topic:
        preview = discover_topic(ns.topic, limit=ns.limit or 50)
        print(json.dumps({
            "mode": "topic_preview",
            "topic": ns.topic,
            "total_images": preview.total_images,
            "provider": preview.provider,
            "page_count": preview.query_log.page_count,
            "image_count": preview.query_log.image_count,
            "entries": [
                {
                    "image_url": e.image_url,
                    "source_page_url": e.source_page_url,
                    "discovery_method": e.discovery_method,
                } for e in preview.entries
            ],
        }, ensure_ascii=False))
    else:
        result = scrape_images(
            ns.url,
            ns.out,
            limit=ns.limit,
            drive_service=drive_service,
            drive_folder_id=ns.drive_folder_id,
            respect_robots=ns.respect_robots,
        )
        print(json.dumps({
            "mode": "direct_url",
            "page_url": result.page_url,
            "found": len(result.image_urls),
            "downloaded": len(result.saved_files),
            "drive_uploaded": len(result.drive_file_ids),
            "output_dir": os.path.abspath(ns.out),
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
