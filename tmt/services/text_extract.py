from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pptx import Presentation

try:
    import jieba
except Exception:  # pragma: no cover
    jieba = None

EN_STOPWORDS = set("""
a an and are as at be but by for if in into is it no not of on or such that the their then there these they this to was will with you your from we our us
can may should could would page slide report presentation figure table data source copyright
""".split())
ZH_STOPWORDS = set("的 了 是 在 與 及 和 或 為 於 有 之 中 上 下 這 那 一 個 我們 你們 他們 可以 進行 相關 使用 以及 透過 主要 目前 內容 資料 報告 簡報 圖表 頁面".split())


@dataclass
class NativeSlide:
    page_number: int
    title: str
    text: str
    has_visual: bool


def _iter_shape_text(shape) -> Iterable[str]:
    # Group shapes: recurse when possible.
    if hasattr(shape, "shapes"):
        for child in shape.shapes:
            yield from _iter_shape_text(child)

    if getattr(shape, "has_text_frame", False):
        for paragraph in shape.text_frame.paragraphs:
            text = "".join(run.text for run in paragraph.runs) if paragraph.runs else paragraph.text
            if text and text.strip():
                yield text.strip()

    if getattr(shape, "has_table", False):
        for row in shape.table.rows:
            for cell in row.cells:
                if cell.text and cell.text.strip():
                    yield cell.text.strip()

    # Chart title is often accessible even when other chart labels are not.
    if getattr(shape, "has_chart", False):
        chart = shape.chart
        try:
            if chart.has_title and chart.chart_title.has_text_frame:
                title = chart.chart_title.text_frame.text
                if title and title.strip():
                    yield title.strip()
        except Exception:
            pass


def _visual_shape(shape) -> bool:
    # Picture=13, chart=3, group=6, diagram/graphic variants vary by Office version.
    shape_type = int(getattr(shape, "shape_type", 0) or 0)
    return shape_type in {3, 6, 13, 19} or bool(getattr(shape, "has_chart", False))


def extract_native_slides(path: Path) -> list[NativeSlide]:
    if path.suffix.lower() != ".pptx":
        return []
    prs = Presentation(str(path))
    results: list[NativeSlide] = []
    for page_number, slide in enumerate(prs.slides, start=1):
        ordered = sorted(slide.shapes, key=lambda s: (int(getattr(s, "top", 0) or 0), int(getattr(s, "left", 0) or 0)))
        parts: list[str] = []
        has_visual = False
        for shape in ordered:
            has_visual = has_visual or _visual_shape(shape)
            try:
                parts.extend(_iter_shape_text(shape))
            except Exception:
                continue

        # Notes are useful internal search context but are not rendered onto the slide.
        try:
            if slide.has_notes_slide:
                notes_frame = slide.notes_slide.notes_text_frame
                if notes_frame:
                    for p in notes_frame.paragraphs:
                        if p.text and p.text.strip():
                            parts.append(p.text.strip())
        except Exception:
            pass

        title = ""
        try:
            if slide.shapes.title and slide.shapes.title.text:
                title = slide.shapes.title.text.strip()
        except Exception:
            pass
        text = "\n".join(dict.fromkeys(p for p in parts if p.strip()))
        results.append(NativeSlide(page_number, title, text, has_visual))
    return results


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def summarize_text(text: str, max_chars: int = 260) -> str:
    clean = normalize_text(text)
    if not clean:
        return ""
    # Prefer complete lines/sentences while staying deterministic and offline.
    chunks = [x.strip() for x in re.split(r"[\n。！？!?]+", clean) if x.strip()]
    out = ""
    for chunk in chunks:
        candidate = (out + "；" + chunk).strip("；")
        if len(candidate) > max_chars:
            break
        out = candidate
    return out or clean[:max_chars].rstrip() + ("…" if len(clean) > max_chars else "")


def extract_keywords(text: str, topk: int = 8) -> list[str]:
    text = normalize_text(text)
    tokens: list[str] = []

    # English / acronym tokens.
    for token in re.findall(r"[A-Za-z][A-Za-z0-9+._/-]{1,39}", text):
        low = token.lower().strip("._/-")
        if low not in EN_STOPWORDS and len(low) >= 2:
            tokens.append(token.strip("._/-"))

    # Traditional Chinese / CJK segmentation.
    cjk_runs = re.findall(r"[\u3400-\u9fff]{2,}", text)
    for run in cjk_runs:
        if jieba:
            words = jieba.cut(run, cut_all=False)
        else:
            words = (run[i:i + 2] for i in range(max(0, len(run) - 1)))
        for word in words:
            word = word.strip()
            if 2 <= len(word) <= 12 and word not in ZH_STOPWORDS:
                tokens.append(word)

    if not tokens:
        return []
    counts = Counter(t.lower() for t in tokens)
    representative: dict[str, str] = {}
    for t in tokens:
        representative.setdefault(t.lower(), t)
    ranked = sorted(counts.items(), key=lambda kv: (kv[1], len(kv[0])), reverse=True)
    return [representative[key] for key, _ in ranked[:topk]]
