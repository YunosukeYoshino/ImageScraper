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


st.set_page_config(page_title="image-saver | 画像スクレイパー", layout="centered")

st.title("URLを入れるだけ・画像スクレイパー")
st.caption("対象URLを入力して実行すると、ページ内の画像をローカルに保存し、一覧表示します。 robots.txt を尊重します。")

url = st.text_input("対象URL", placeholder="https://example.com")
output_dir = st.text_input("保存先ディレクトリ", value="./images")
limit = st.number_input("最大枚数(任意)", min_value=0, max_value=500, value=0, help="0は上限なし")
respect_robots = st.toggle("robots.txt を尊重", value=True)

run = st.button("スクレイピング開始")

if run:
    if not url.strip():
        st.error("URLを入力してください。")
    else:
        with st.spinner("スクレイピング中..."):
            start = time.time()
            try:
                lim: Optional[int] = None if limit == 0 else int(limit)
                result = scrape_images(url.strip(), output_dir.strip(), limit=lim, respect_robots=respect_robots)
                duration = int((time.time() - start) * 1000)
                st.success(f"完了: 画像 {len(result.saved_files)} 枚保存 ({duration} ms)")

                if result.saved_files:
                    st.subheader("保存した画像")
                    cols = st.columns(5)
                    for idx, path in enumerate(result.saved_files):
                        col = cols[idx % 5]
                        with col:
                            st.image(path, caption=Path(path).name, use_container_width=True)
                else:
                    st.info("保存された画像はありません。フィルタやrobotsで除外された可能性があります。")
            except PermissionError as e:
                st.warning(f"robots.txt によりブロックされました: {e}")
            except Exception as e:
                st.error(f"失敗しました: {e}")
