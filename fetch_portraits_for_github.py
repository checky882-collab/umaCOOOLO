#!/usr/bin/env python3
"""
特雷森学园 · GitHub 立绘仓库素材一键准备脚本（默认对接 https://github.com/checky882-collab/umaCOOOLO）
1. 默认先从本地目录 (C:\\Users\\a1025\\Documents\\uma\\public\\assets\\characters) 复制已有 54 张高清 .webp 到 characters/；
2. 可选启用 --fetch-gametora，礼貌并发 + 断点续传从 GameTora 拉取其余实装角色的 racewear / uniform / thumb 立绘。

用法示例：
  python fetch_portraits_for_github.py
  python fetch_portraits_for_github.py --dry-run
  python fetch_portraits_for_github.py --fetch-gametora --workers 8 --delay 0.15 --max-seconds 55
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = SCRIPT_DIR / "manifest_172.json"
DEFAULT_LOCAL_SRC = Path(r"C:\Users\a1025\Documents\uma\public\assets\characters")
DEFAULT_OUT_DIR = SCRIPT_DIR / "characters"
DEFAULT_TARGET_REPO = "https://github.com/checky882-collab/umaCOOOLO"
VALID_VARIANTS = ("racewear", "uniform", "thumb")
USER_AGENT = "Mozilla/5.0 (compatible; UmaTracenPortraitHelper/1.1)"


def load_manifest(manifest_path: Path) -> List[dict]:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"未找到角色清单文件：{manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    chars = data.get("characters")
    if not isinstance(chars, list) or not chars:
        raise ValueError(f"manifest 格式异常，缺少 characters 列表：{manifest_path}")
    return chars


def copy_local_portraits(
    local_src: Path,
    out_dir: Path,
    dry_run: bool = False,
) -> Tuple[int, int, int]:
    """复制本地已有高清 .webp/.png 立绘，返回 (copied, skipped, total_found)。"""
    if not local_src.is_dir():
        print(f"[提示] 本地立绘目录不存在，已跳过本地复制：{local_src}")
        return 0, 0, 0

    files = sorted(
        p for p in local_src.iterdir()
        if p.is_file() and p.suffix.lower() in (".webp", ".png")
    )
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0
    for src_file in files:
        dst_file = out_dir / src_file.name
        if dst_file.is_file() and dst_file.stat().st_size == src_file.stat().st_size:
            skipped += 1
            continue
        if dry_run:
            copied += 1
            continue
        shutil.copy2(src_file, dst_file)
        copied += 1

    return copied, skipped, len(files)


def has_existing_variant(out_dir: Path, uma_id: int, variant: str) -> Optional[Path]:
    for ext in (".webp", ".png"):
        cand = out_dir / f"{uma_id}_{variant}{ext}"
        if cand.is_file() and cand.stat().st_size > 0:
            return cand
    return None


def fetch_url_bytes(url: str, timeout: float) -> Tuple[Optional[bytes], str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            if status != 200:
                return None, f"HTTP {status}"
            payload = resp.read()
            if not payload or len(payload) < 256:
                return None, "空文件或体积过小"
            return payload, f"{len(payload)} bytes"
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except Exception as exc:
        return None, str(exc)


def write_bytes_atomic(dst: Path, payload: bytes) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dst.with_suffix(dst.suffix + f".{threading.get_ident()}.part")
    try:
        with tmp_path.open("wb") as fh:
            fh.write(payload)
        os.replace(tmp_path, dst)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def fetch_one_character(
    row: dict,
    out_dir: Path,
    variants: List[str],
    delay_sec: float,
    timeout_sec: float,
    deadline: Optional[float],
    dry_run: bool,
) -> Tuple[int, int, int, int, str]:
    """
    拉取单个实装角色的缺失变体，返回 (downloaded, skipped, failed, timed_out, summary_msg)。
    自动复用同一角色的 chr_icon 字节给 uniform/thumb（以及 racewear 404 兜底），请求量减半。
    """
    uma_id = int(row.get("uma_id") or 0)
    outfit_id = str(row.get("outfit_id") or f"{uma_id}01")
    name_zh = str(row.get("name_zh") or uma_id)

    missing = [v for v in variants if has_existing_variant(out_dir, uma_id, v) is None]
    skipped = len(variants) - len(missing)
    if not missing:
        return 0, skipped, 0, 0, ""

    if deadline is not None and time.monotonic() >= deadline:
        return 0, skipped, 0, len(missing), ""

    if dry_run:
        return len(missing), skipped, 0, 0, f"[预演] {name_zh} ({uma_id}): {','.join(missing)}"

    stand_url = f"https://gametora.com/images/umamusume/characters/chara_stand_{uma_id}_{outfit_id}.png"
    icon_url = f"https://gametora.com/images/umamusume/characters/icons/chr_icon_{uma_id}.png"

    downloaded = 0
    failed = 0
    timed_out = 0
    notes: List[str] = []

    icon_bytes: Optional[bytes] = None
    icon_fetched = False

    def ensure_icon() -> Optional[bytes]:
        nonlocal icon_bytes, icon_fetched
        if icon_fetched:
            return icon_bytes
        icon_fetched = True
        if deadline is not None and time.monotonic() >= deadline:
            return None
        rem = timeout_sec if deadline is None else max(1.5, min(timeout_sec, deadline - time.monotonic()))
        data, _ = fetch_url_bytes(icon_url, timeout=rem)
        icon_bytes = data
        if delay_sec > 0:
            time.sleep(delay_sec)
        return icon_bytes

    for variant in missing:
        if deadline is not None and time.monotonic() >= deadline:
            timed_out += 1
            continue

        dst = out_dir / f"{uma_id}_{variant}.png"
        if variant == "racewear":
            rem = timeout_sec if deadline is None else max(1.5, min(timeout_sec, deadline - time.monotonic()))
            stand_data, err = fetch_url_bytes(stand_url, timeout=rem)
            if delay_sec > 0:
                time.sleep(delay_sec)
            if stand_data is not None:
                write_bytes_atomic(dst, stand_data)
                downloaded += 1
                notes.append("racewear")
            else:
                fb = ensure_icon()
                if fb is not None:
                    write_bytes_atomic(dst, fb)
                    downloaded += 1
                    notes.append("racewear(icon兜底)")
                else:
                    failed += 1
                    notes.append(f"racewear失败({err})")
        else:
            data = ensure_icon()
            if data is not None:
                write_bytes_atomic(dst, data)
                downloaded += 1
                notes.append(variant)
            else:
                if deadline is not None and time.monotonic() >= deadline:
                    timed_out += 1
                else:
                    failed += 1
                    notes.append(f"{variant}失败")

    msg = f"[拉取] {name_zh} ({uma_id}): {', '.join(notes)}" if notes else ""
    return downloaded, skipped, failed, timed_out, msg


def fetch_from_gametora(
    characters: Iterable[dict],
    out_dir: Path,
    variants: List[str],
    delay_sec: float,
    timeout_sec: float,
    workers: int = 8,
    max_seconds: float = 0.0,
    limit: int = 0,
    only_ids: Optional[Set[int]] = None,
    dry_run: bool = False,
) -> Dict[str, int]:
    """礼貌并发 + 断点续传拉取 GameTora 实装角色立绘。"""
    targets: List[dict] = []
    for row in characters:
        uma_id = int(row.get("uma_id") or 0)
        if not (1001 <= uma_id < 10000):
            continue
        if only_ids and uma_id not in only_ids:
            continue
        targets.append(row)
        if limit > 0 and len(targets) >= limit:
            break

    deadline = (time.monotonic() + max_seconds) if max_seconds > 0 else None
    stats = {"downloaded": 0, "skipped": 0, "failed": 0, "timed_out": 0, "targets": len(targets)}
    worker_cnt = max(1, min(int(workers) or 1, 12))

    if worker_cnt == 1 or dry_run:
        for row in targets:
            dl, sk, fl, to, msg = fetch_one_character(
                row, out_dir, variants, delay_sec, timeout_sec, deadline, dry_run
            )
            stats["downloaded"] += dl
            stats["skipped"] += sk
            stats["failed"] += fl
            stats["timed_out"] += to
            if msg:
                print(msg)
        return stats

    with ThreadPoolExecutor(max_workers=worker_cnt) as pool:
        futs = [
            pool.submit(
                fetch_one_character,
                row,
                out_dir,
                variants,
                delay_sec,
                timeout_sec,
                deadline,
                dry_run,
            )
            for row in targets
        ]
        for fut in as_completed(futs):
            dl, sk, fl, to, msg = fut.result()
            stats["downloaded"] += dl
            stats["skipped"] += sk
            stats["failed"] += fl
            stats["timed_out"] += to
            if msg:
                print(msg)

    return stats


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="特雷森学园 GitHub 立绘外链仓库素材准备工具（本地 54 张复制 + 可选 GameTora 礼貌并发拉取）"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="manifest_172.json 路径（默认同目录）",
    )
    parser.add_argument(
        "--local-src",
        type=Path,
        default=DEFAULT_LOCAL_SRC,
        help="本地已有高清立绘目录（默认 C:\\Users\\a1025\\Documents\\uma\\public\\assets\\characters）",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="输出立绘目录（默认 ./characters）",
    )
    parser.add_argument(
        "--skip-local",
        action="store_true",
        help="跳过本地 54 张高清立绘复制",
    )
    parser.add_argument(
        "--fetch-gametora",
        action="store_true",
        help="开启从 GameTora 礼貌并发拉取其余实装角色立绘（默认关闭）",
    )
    parser.add_argument(
        "--variants",
        type=str,
        default="racewear,uniform,thumb",
        help="要拉取的变体列表，逗号分隔（可选：racewear,uniform,thumb）",
    )
    parser.add_argument(
        "--ids",
        type=str,
        default="",
        help="仅处理指定 uma_id（逗号分隔，例如 1004,1024）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="最多拉取多少名角色（0 表示不限制）",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="并发拉取线程数（默认 8，最大 12）",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.15,
        help="单线程每次网络请求后的礼貌限速间隔秒数（默认 0.15 秒）",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="单次 HTTP 请求超时秒数（默认 10 秒）",
    )
    parser.add_argument(
        "--max-seconds",
        type=float,
        default=0.0,
        help="总耗时软上限秒数（0 表示不限制；超限时优雅保存已下载内容并退出，可断点续传）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预演模式：仅输出统计结果，不写入或下载任何文件",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    t0 = time.monotonic()
    characters = load_manifest(args.manifest)

    variants = [v.strip().lower() for v in args.variants.split(",") if v.strip()]
    variants = [v for v in variants if v in VALID_VARIANTS] or list(VALID_VARIANTS)

    only_ids: Optional[Set[int]] = None
    if args.ids.strip():
        only_ids = {int(tok.strip()) for tok in args.ids.split(",") if tok.strip().isdigit()}

    print(f"=== 特雷森学园 GitHub 立绘素材准备工具 (清单共 {len(characters)} 名角色) ===")
    print(f"目标默认仓库：{DEFAULT_TARGET_REPO}")
    print(f"输出目录：{args.out_dir}" + (" [预演模式]" if args.dry_run else ""))

    if not args.skip_local:
        copied, skipped, found = copy_local_portraits(args.local_src, args.out_dir, dry_run=args.dry_run)
        print(f"[本地复制] 扫描到 {found} 张本地立绘 -> 新复制 {copied} 张，已存在跳过 {skipped} 张")

    if args.fetch_gametora:
        print(
            f"[GameTora 并发拉取] 变体={','.join(variants)}，并发={args.workers}，限速={args.delay}s"
            + (f"，耗时上限={args.max_seconds}s" if args.max_seconds > 0 else "")
            + (f"，上限={args.limit}人" if args.limit else "")
        )
        st = fetch_from_gametora(
            characters=characters,
            out_dir=args.out_dir,
            variants=variants,
            delay_sec=max(0.0, args.delay),
            timeout_sec=max(2.0, args.timeout),
            workers=args.workers,
            max_seconds=max(0.0, args.max_seconds),
            limit=max(0, args.limit),
            only_ids=only_ids,
            dry_run=args.dry_run,
        )
        elapsed = time.monotonic() - t0
        print(
            f"[GameTora 完成] 扫描实装角色 {st['targets']} 名 -> 新下载 {st['downloaded']} 张，"
            f"断点续传跳过 {st['skipped']} 张，缺失/404 {st['failed']} 张，"
            f"超预算留待续传 {st['timed_out']} 张（总耗时 {elapsed:.1f}s）"
        )
    else:
        print("[提示] 当前未启用 --fetch-gametora，未发起任何网络下载；如需批量补全其余角色，请附加 --fetch-gametora 参数。")

    print(f"[下一步] 将 {args.out_dir.name}/ 目录上传至 {DEFAULT_TARGET_REPO} 即可即刻生效！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
