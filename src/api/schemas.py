from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ScrapeRequest(BaseModel):
    url: HttpUrl
    output_dir: str = Field(default="./images")
    respect_robots: bool = Field(default=True)
    upload_to_drive: bool = Field(default=False)
    drive_folder_id: Optional[str] = None


class ScrapeSummary(BaseModel):
    saved: int
    failed: int
    output_dir: str
    uploaded: Optional[int] = None
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    files: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    code: int
    message: str
    details: Optional[dict] = None
