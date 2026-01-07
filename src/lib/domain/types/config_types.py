"""Type definitions for configuration data.

Provides TypedDict definitions for UI configuration and related structures.
"""

from __future__ import annotations

from typing import TypedDict


class UIConfig(TypedDict, total=False):
    """Streamlit UI configuration structure.

    All fields are optional (total=False) since config may be partially defined.
    """

    base_url: str
    common_headers: dict[str, str]
    timeout: int


class GDriveHistoryData(TypedDict):
    """Google Drive path history structure."""

    paths: list[str]
