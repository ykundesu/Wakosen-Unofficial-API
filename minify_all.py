#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指定フォルダ以下の .json を再帰ミニファイし、結果で完全に置き換える
使い方:
  python minify_json_inplace.py /path/to/dir
"""

import sys
import os
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
import shutil

def minify_inplace(path: Path) -> tuple[bool, str]:
    try:
        # BOM付きUTF-8も許容
        raw = path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)  # コメント/末尾カンマ等は非対応
    except Exception as e:
        return False, f"解析失敗: {e}"

    try:
        minified = json.dumps(
            data,
            ensure_ascii=False,      # 日本語などはそのまま
            separators=(",", ":"),   # 余計なスペースを除去
            allow_nan=False          # NaN/InfinityはJSON規格外
        )

        # 同じディレクトリに一時ファイルを作る（同一FS上で原子的置換するため）
        with NamedTemporaryFile("w", delete=False, dir=str(path.parent),
                                encoding="utf-8", newline="\n") as tmp:
            tmp.write(minified)
            tmp_path = Path(tmp.name)

        # 元のパーミッションを引き継ぐ
        shutil.copymode(path, tmp_path)

        # 原子的に置換
        os.replace(tmp_path, path)

        return True, ""
    except Exception as e:
        # 失敗時に一時ファイルが残ってたら掃除
        try:
            if 'tmp_path' in locals() and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False, f"書き込み失敗: {e}"

def main(root: Path, ext: str = ".json"):
    if not root.is_dir():
        print(f"[ERROR] ディレクトリが見つからない: {root}", file=sys.stderr)
        sys.exit(1)

    targets = sorted(p for p in root.rglob(f"*{ext}") if p.is_file())
    if not targets:
        print("[INFO] 対象ファイルなし")
        return

    ok = ng = 0
    for p in targets:
        success, msg = minify_inplace(p)
        if success:
            ok += 1
            print(f"[OK ] {p}")
        else:
            ng += 1
            print(f"[NG ] {p} -> {msg}", file=sys.stderr)

    print(f"\n完了: 成功 {ok} / 失敗 {ng} / 合計 {len(targets)}")

if __name__ == "__main__":
    root_path = Path("v1")
    main(root_path)
