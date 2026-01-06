from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.api.schemas import ScrapeRequest, ScrapeSummary
from src.lib.image_scraper import _init_drive, scrape_images

app = FastAPI(title="image-saver API", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/scrape", response_model=ScrapeSummary)
def scrape(req: ScrapeRequest, request: Request):
    logging.info(f"/scrape start url={req.url}")

    drive_service = None
    if req.upload_to_drive:
        sa_json = os.environ.get("GDRIVE_SA_JSON")
        if not sa_json:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": 400,
                    "message": "upload_to_drive=true requires GDRIVE_SA_JSON env set to service account JSON path",
                },
            )
        try:
            drive_service = _init_drive(sa_json)
        except Exception as e:
            raise HTTPException(status_code=500, detail={"code": 500, "message": f"Drive init failed: {e}"}) from e

    try:
        res = scrape_images(
            url=str(req.url),
            output_dir=req.output_dir,
            limit=None,
            drive_service=drive_service,
            drive_folder_id=req.drive_folder_id,
            respect_robots=req.respect_robots,
        )
    except PermissionError as e:
        logging.warning(f"robots disallow: {e}")
        raise HTTPException(status_code=403, detail={"code": 403, "message": str(e)}) from e
    except ValueError as e:
        logging.warning(f"bad request: {e}")
        raise HTTPException(status_code=400, detail={"code": 400, "message": str(e)}) from e
    except Exception as e:
        logging.error(f"scrape failed: {e}")
        raise HTTPException(status_code=500, detail={"code": 500, "message": "internal error"}) from e

    saved = len(res.saved_files)
    failed = max(0, len(res.image_urls) - saved)

    # treat images not saved due to mock or skip as failure
    summary = ScrapeSummary(
        saved=saved,
        failed=failed,
        output_dir=req.output_dir,
        uploaded=len(res.drive_file_ids) if res.drive_file_ids is not None else None,
        files=res.saved_files or None,
    )
    logging.info(f"/scrape done url={req.url} saved={saved} failed={failed}")
    return summary


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):  # noqa: D401
    # Normalize HTTPException detail into ErrorResponse shape
    if isinstance(exc.detail, dict):
        payload = exc.detail
    else:
        payload = {"code": exc.status_code, "message": str(exc.detail)}
    payload.setdefault("code", exc.status_code)
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # noqa: D401
    logging.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"code": 500, "message": "internal error"})
