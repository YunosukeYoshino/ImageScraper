from __future__ import annotations
import sys
from pathlib import Path
import time
from typing import Optional

import streamlit as st

# Ensure repository root is importable when run via Streamlit
_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.lib.image_scraper import scrape_images
from src.lib import image_scraper as scraper


st.set_page_config(page_title="image-saver | 画像スクレイパー", layout="centered")

st.title("URLを入れるだけ・画像スクレイパー")
st.caption("対象URLを入力してプレビュー → "
           "必要なら選択してダウンロード。 robots.txt を尊重します。")

url = st.text_input("対象URL", placeholder="https://example.com")
output_dir = st.text_input("保存先ディレクトリ", value="./images")
limit = st.number_input("最大枚数(任意)", min_value=0, max_value=500, value=0, help="0は上限なし")
respect_robots = st.toggle("robots.txt を尊重", value=True)

col_r1, col_r2, col_r3 = st.columns([1,1,2])
with col_r1:
    run_preview = st.button("画像を取得（プレビュー）")
with col_r2:
    clear_sel = st.button("選択をクリア")

if clear_sel:
    st.session_state.pop("preview_urls", None)
    st.session_state.pop("selected", None)

if run_preview:
    if not url.strip():
        st.error("URLを入力してください。")
    else:
        with st.spinner("画像URLを取得中..."):
            try:
                lim: Optional[int] = None if limit == 0 else int(limit)
                urls = scraper.list_images(url.strip(), limit=lim, respect_robots=respect_robots)
                st.session_state["preview_urls"] = urls
                st.session_state["selected"] = set()
                st.success(f"検出: {len(urls)} 枚の画像候補")
            except PermissionError as e:
                st.warning(f"robots.txt によりブロックされました: {e}")
            except Exception as e:
                st.error(f"失敗しました: {e}")

preview_urls = st.session_state.get("preview_urls", [])
selected: set[str] = st.session_state.get("selected", set())

if preview_urls:
    st.subheader("プレビュー（選択可能）")
    cols = st.columns(5)
    for idx, u in enumerate(preview_urls):
        col = cols[idx % 5]
        with col:
            st.image(u, caption=f"{idx+1}", use_container_width=True)
            checked = st.checkbox("選択", key=f"sel_{idx}", value=(u in selected))
            if checked:
                selected.add(u)
            else:
                selected.discard(u)
    st.session_state["selected"] = selected

    col_d1, col_d2 = st.columns([1,1])
    with col_d1:
        do_download_all = st.button("全てダウンロード")
    with col_d2:
        do_download_sel = st.button("選択をダウンロード")

    if do_download_all or do_download_sel:
        target = preview_urls if do_download_all else list(selected)
        if not target:
            st.info("選択された画像がありません。")
        else:
            with st.spinner("ダウンロード中..."):
                try:
                    paths = scraper.download_images(target, output_dir.strip(), respect_robots=respect_robots)
                    st.success(f"保存: {len(paths)} 枚")
                    if paths:
                        grid = st.columns(5)
                        for i, p in enumerate(paths):
                            with grid[i % 5]:
                                st.image(p, caption=Path(p).name, use_container_width=True)
                except Exception as e:
                    st.error(f"ダウンロードに失敗しました: {e}")
