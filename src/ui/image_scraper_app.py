from __future__ import annotations
import sys
from pathlib import Path
import time
from typing import Optional, List
import json

import streamlit as st

# Ensure repository root is importable when run via Streamlit
_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.lib.image_scraper import scrape_images
from src.lib.topic_discovery import discover_topic, download_selected, filter_entries
from src.lib.models_discovery import DownloadFilter, ProvenanceEntry
from src.lib import image_scraper as scraper


st.set_page_config(page_title="image-saver | 画像スクレイパー", layout="centered")

st.title("URL/トピックで画像スクレイパー")
st.caption("URLプレビュー → 選択ダウンロード、またはトピック（検索ワード）から自律探索プレビュー。robots.txt を尊重します。")

# --- Input Section ---
url = st.text_input("対象URL", placeholder="https://example.com")
topic = st.text_input("トピック（検索ワード）", placeholder="例: 富士山 紅葉", help="URLの代わりにトピックを入力してプレビュー")
output_dir = st.text_input("保存先ディレクトリ", value="./images")
limit = st.number_input("最大枚数(任意)", min_value=0, max_value=500, value=0, help="0は上限なし")
respect_robots = st.toggle("robots.txt を尊重", value=True)

# --- US2: Filter Section ---
with st.expander("🔍 フィルター設定 (US2)", expanded=False):
    st.caption("ダウンロード時に適用されるフィルター")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        min_width = st.number_input("最小幅 (px)", min_value=0, value=0, help="0で制限なし")
    with col_f2:
        min_height = st.number_input("最小高さ (px)", min_value=0, value=0, help="0で制限なし")
    allow_domains = st.text_input("許可ドメイン (カンマ区切り)", placeholder="pixabay.com, unsplash.com", help="空欄で全て許可")
    deny_domains = st.text_input("除外ドメイン (カンマ区切り)", placeholder="spam.com, ads.example.net", help="空欄で除外なし")

search_term = st.text_input("検索フィルタ (ファイル名/URL 部分一致)", value="")
page_size = st.selectbox("ページサイズ", [10, 25, 50, 100], index=1)
select_all_toggle = st.checkbox("全選択/全解除", value=False)

col_r1, col_r2, col_r3 = st.columns([1,1,2])
with col_r1:
    run_preview = st.button("URLプレビュー")
with col_r2:
    clear_sel = st.button("選択をクリア")
col_r4 = st.container()
with col_r4:
    run_topic = st.button("トピックでプレビュー")

if clear_sel:
    st.session_state.pop("preview_urls", None)
    st.session_state.pop("selected", None)
    st.session_state.pop("provenance_entries", None)

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
                st.session_state["provenance_entries"] = None  # URL mode has no provenance
                st.success(f"検出: {len(urls)} 枚の画像候補 (URL)")
            except PermissionError as e:
                st.warning(f"robots.txt によりブロックされました: {e}")
            except Exception as e:
                st.error(f"失敗しました: {e}")

if run_topic:
    if not topic.strip():
        st.error("トピックを入力してください。")
    else:
        with st.spinner("トピックから探索中..."):
            try:
                lim: Optional[int] = None if limit == 0 else int(limit)
                preview = discover_topic(topic.strip(), limit=lim or 50)
                st.session_state["preview_urls"] = [str(e.image_url) for e in preview.entries]
                st.session_state["selected"] = set()
                st.session_state["provenance_entries"] = preview.entries  # Store for US2
                st.success(f"検出: {preview.total_images} 枚の画像候補 (トピック: {topic})")
            except Exception as e:
                st.error(f"失敗しました: {e}")

preview_urls = st.session_state.get("preview_urls", [])
selected: set[str] = st.session_state.get("selected", set())
provenance_entries: Optional[List[ProvenanceEntry]] = st.session_state.get("provenance_entries", None)

# Apply search filter
if search_term.strip():
    filtered = [u for u in preview_urls if search_term.lower() in str(u).lower()]
else:
    filtered = preview_urls

# Pagination state
total = len(filtered)
page_count = max(1, (total + page_size - 1) // page_size)
page_index = st.session_state.get("page_index", 0)
col_p1, col_p2, col_p3 = st.columns([1,1,3])
with col_p1:
    if st.button("前へ", disabled=page_index <= 0):
        page_index = max(0, page_index - 1)
with col_p2:
    if st.button("次へ", disabled=page_index >= page_count - 1):
        page_index = min(page_count - 1, page_index + 1)
st.session_state["page_index"] = page_index
start = page_index * page_size
end = start + page_size
page_slice = filtered[start:end]

if preview_urls:
    st.subheader("プレビュー（選択可能）")
    # Select all toggle
    if select_all_toggle:
        for u in page_slice:
            selected.add(str(u))
    else:
        # If toggled off, remove only those in page_slice (do not clear global manual selections on other pages)
        for u in page_slice:
            u_str = str(u)
            if u_str in selected and f"sel_{preview_urls.index(u)}" not in st.session_state:
                # keep manual boxes; rely on user unchecking for removal
                pass
    cols = st.columns(5)
    for idx_global, u in enumerate(page_slice):
        col = cols[idx_global % 5]
        u_str = str(u)
        with col:
            st.image(u_str, caption=Path(u_str).name, width="stretch")
            key = f"sel_{preview_urls.index(u)}"
            checked = st.checkbox("選択", key=key, value=(u_str in selected))
            if checked:
                selected.add(u_str)
            else:
                selected.discard(u_str)
    st.session_state["selected"] = selected

    col_d1, col_d2 = st.columns([1,1])
    with col_d1:
        do_download_all = st.button("全てダウンロード")
    with col_d2:
        do_download_sel = st.button("選択をダウンロード")

    if do_download_all or do_download_sel:
        target_urls = [str(u) for u in preview_urls] if do_download_all else list(selected)
        if not target_urls:
            st.info("選択された画像がありません。")
        else:
            with st.spinner("ダウンロード中..."):
                try:
                    progress = st.progress(0)
                    def cb(done, total):
                        progress.progress(int(done / total * 100))

                    # Build filter
                    download_filter = DownloadFilter(
                        min_width=min_width if min_width > 0 else None,
                        min_height=min_height if min_height > 0 else None,
                        allow_domains=[d.strip() for d in allow_domains.split(",") if d.strip()] if allow_domains.strip() else None,
                        deny_domains=[d.strip() for d in deny_domains.split(",") if d.strip()] if deny_domains.strip() else None,
                    )

                    # US2: If we have provenance entries (topic mode), use download_selected
                    if provenance_entries:
                        # Filter entries to only selected URLs
                        selected_entries = [e for e in provenance_entries if str(e.image_url) in target_urls]

                        paths, index_path = download_selected(
                            entries=selected_entries,
                            output_dir=output_dir.strip(),
                            download_filter=download_filter,
                            respect_robots=respect_robots,
                            progress_cb=cb,
                        )

                        st.success(f"保存: {len(paths)} 枚 | Provenance Index: {index_path}")
                    else:
                        # URL mode: apply domain filter manually then download
                        filtered_target = target_urls
                        if download_filter.allow_domains or download_filter.deny_domains:
                            from urllib.parse import urlparse
                            def _domain_check(u: str) -> bool:
                                domain = urlparse(u).netloc.lower()
                                if download_filter.allow_domains:
                                    if not any(domain == d.lower() or domain.endswith("." + d.lower()) for d in download_filter.allow_domains):
                                        return False
                                if download_filter.deny_domains:
                                    if any(domain == d.lower() or domain.endswith("." + d.lower()) for d in download_filter.deny_domains):
                                        return False
                                return True
                            filtered_target = [u for u in target_urls if _domain_check(u)]

                        paths = scraper.download_images_parallel(filtered_target, output_dir.strip(), respect_robots=respect_robots, progress_cb=cb)
                        st.success(f"保存: {len(paths)} 枚")

                    if paths:
                        grid = st.columns(5)
                        for i, p in enumerate(paths[:20]):  # Show max 20 thumbnails
                            with grid[i % 5]:
                                st.image(p, caption="✅ " + Path(p).name, width="stretch")

                        # Offer ZIP download to user
                        import io, zipfile
                        mem = io.BytesIO()
                        with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                            for p in paths:
                                with open(p, "rb") as f:
                                    zf.writestr(Path(p).name, f.read())
                        mem.seek(0)
                        dl_filename = "images_download.zip"
                        st.download_button(
                            label="ZIPをダウンロード",
                            data=mem.getvalue(),
                            file_name=dl_filename,
                            mime="application/zip"
                        )
                except Exception as e:
                    st.error(f"ダウンロードに失敗しました: {e}")
