"""HTML parsing infrastructure."""

from .html_parser import ImageMetadata, extract_images, parse_html

__all__ = [
    "parse_html",
    "extract_images",
    "ImageMetadata",
]
