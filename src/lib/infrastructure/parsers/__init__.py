"""HTML parsing infrastructure."""
from .html_parser import parse_html, extract_images, ImageMetadata

__all__ = [
    "parse_html",
    "extract_images",
    "ImageMetadata",
]
