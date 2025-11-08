from __future__ import annotations
import json
import time
from typing import Dict, Optional, Tuple

import requests
import streamlit as st

from src.lib.ui_helpers import (
    validate_json_text,
    mask_headers,
    build_full_url,
    load_config,
    save_config,
    summarize_response,
)

st.set_page_config(page_title="image-saver API UI", layout="wide")

st.title("image-saver API リクエストUI")

# Load persisted config
cfg = load_config() or {}
base_url = st.text_input("ベースURL", value=cfg.get("base_url", "http://localhost:8000"))
common_headers_text = st.text_area("共通ヘッダー(JSON)", value=json.dumps(cfg.get("common_headers", {}), ensure_ascii=False))
timeout = st.number_input("タイムアウト(秒)", min_value=1, max_value=120, value=int(cfg.get("timeout", 30)))

col1, col2 = st.columns(2)
with col1:
    method = st.selectbox("メソッド", ["GET", "POST", "PUT", "PATCH", "DELETE"], index=0)
    path = st.text_input("パス", value="/healthz")
with col2:
    query_text = st.text_area("クエリ(JSON)", value="{}")
    headers_text = st.text_area("追加ヘッダー(JSON)", value="{}")

body_text = st.text_area("本文(JSON)", value="", height=160)

# Validate JSON inputs
ok_body, err_body = validate_json_text(body_text)
ok_q, err_q = validate_json_text(query_text)
ok_h, err_h = validate_json_text(headers_text)
ok_ch, err_ch = validate_json_text(common_headers_text)

errors = []
if not ok_body: errors.append(f"本文が不正なJSONです: {err_body}")
if not ok_q: errors.append(f"クエリが不正なJSONです: {err_q}")
if not ok_h: errors.append(f"追加ヘッダーが不正なJSONです: {err_h}")
if not ok_ch: errors.append(f"共通ヘッダーが不正なJSONです: {err_ch}")

if errors:
    st.error("\n".join(errors))

colA, colB = st.columns([1,1])
with colA:
    if st.button("送信", disabled=bool(errors)):
        try:
            query = json.loads(query_text) if query_text.strip() else {}
            headers = json.loads(headers_text) if headers_text.strip() else {}
            common_headers = json.loads(common_headers_text) if common_headers_text.strip() else {}
            all_headers = {**common_headers, **headers}

            url = build_full_url(base_url, path, query)
            data = json.loads(body_text) if body_text.strip() else None
            start = time.time()
            resp = requests.request(method=method, url=url, headers=all_headers or None, json=data, timeout=timeout)
            duration_ms = int((time.time() - start) * 1000)

            summary = summarize_response(resp.status_code, duration_ms, resp.text, resp.headers.get("Content-Type"))

            st.subheader("結果")
            st.json(summary)

            # Pretty JSON if possible
            try:
                st.subheader("レスポンス本文")
                st.json(resp.json())
            except Exception:
                st.text_area("レスポンス本文", value=resp.text, height=300)
        except Exception as e:
            st.error(f"送信に失敗しました: {e}")

with colB:
    if st.button("設定保存"):
        try:
            cfg = {
                "base_url": base_url,
                "common_headers": json.loads(common_headers_text) if common_headers_text.strip() else {},
                "timeout": int(timeout),
            }
            save_config(cfg)
            st.success("設定を保存しました")
        except Exception as e:
            st.error(f"設定保存に失敗しました: {e}")

# Show masked preview of headers
try:
    masked = mask_headers(json.loads(common_headers_text) if common_headers_text.strip() else {})
    st.caption(f"共通ヘッダー（マスク表示）: {masked}")
except Exception:
    pass
