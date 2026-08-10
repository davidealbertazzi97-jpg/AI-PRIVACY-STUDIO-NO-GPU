from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any


def _find_text_rects(
    text_page: Any, value: str
) -> list[tuple[float, float, float, float]]:
    text = text_page.get_text_range()
    if not text or not value:
        return []
    lowered = text.casefold()
    needle = value.casefold()
    rects: list[tuple[float, float, float, float]] = []
    cursor = 0
    while cursor < len(lowered):
        start = lowered.find(needle, cursor)
        if start < 0:
            break
        boxes = [
            text_page.get_charbox(index)
            for index in range(start, start + len(value))
            if not text[index].isspace()
        ]
        if boxes:
            rects.append(
                (
                    min(box[0] for box in boxes),
                    min(box[1] for box in boxes),
                    max(box[2] for box in boxes),
                    max(box[3] for box in boxes),
                )
            )
        cursor = start + max(1, len(value))
    return rects


def _requests(spans: list[dict[str, Any]]) -> dict[str, tuple[str, set[str]]]:
    requests: dict[str, tuple[str, set[str]]] = {}
    for span in spans:
        value = str(span.get("text") or "")
        if len(re.sub(r"\s+", "", value)) < 2:
            continue
        replacement = str(span.get("replacement") or span.get("placeholder") or "[PII]")
        if value in requests:
            requests[value][1].add(str(span.get("label") or "PII"))
        else:
            requests[value] = (replacement, {str(span.get("label") or "PII")})
    return requests


def _redact_pdf_editable(
    source: Path,
    target: Path,
    requests: dict[str, tuple[str, set[str]]],
) -> dict[str, Any]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PDF editabile non disponibile.") from exc

    document = fitz.open(source)
    found_values: set[str] = set()
    redaction_count = 0
    try:
        for page in document:
            for value, (replacement, _) in requests.items():
                rectangles = page.search_for(value)
                if not rectangles:
                    continue
                found_values.add(value)
                for rectangle in rectangles:
                    page.add_redact_annot(
                        rectangle,
                        text=replacement,
                        fontname="helv",
                        fontsize=max(6, min(11, rectangle.height * 0.65)),
                        fill=(1, 1, 1),
                        text_color=(0, 0, 0),
                        cross_out=False,
                    )
                    redaction_count += 1
            page.apply_redactions(images=0, graphics=0, text=0)
        document.scrub(
            attached_files=True,
            clean_pages=True,
            embedded_files=True,
            hidden_text=True,
            javascript=True,
            metadata=True,
            redactions=True,
            redact_images=0,
            remove_links=False,
            reset_fields=True,
            reset_responses=True,
            thumbnails=True,
            xml_metadata=True,
        )
        document.set_metadata({})
        target.parent.mkdir(parents=True, exist_ok=True)
        document.save(
            target,
            garbage=4,
            clean=True,
            deflate=True,
            deflate_fonts=True,
            preserve_metadata=False,
        )
    finally:
        document.close()

    skipped_labels: set[str] = set()
    for value, (_, labels) in requests.items():
        if value not in found_values:
            skipped_labels.update(labels)
    with fitz.open(target) as saved:
        pages = len(saved)
    return {
        "pages": pages,
        "redactions": redaction_count,
        "skipped_labels": sorted(skipped_labels),
        "warning": bool(skipped_labels),
        "format": "editable-text-preserving-pdf",
        "searchable": True,
    }


def _redact_pdf_raster(
    source: Path,
    target: Path,
    requests: dict[str, tuple[str, set[str]]],
) -> dict[str, Any]:
    """Create an image-only PDF with the original text pixels removed.

    PDFium supplies text coordinates and page rendering; Pillow paints over
    matching glyphs and writes a new PDF. The output cannot retain the source
    PDF content stream, annotations, attachments, or searchable metadata.
    """
    try:
        import pypdfium2 as pdfium
        from PIL import ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError(
            "La redazione PDF richiede pypdfium2 e Pillow. "
            "Riesegui l’installer aggiornato di Privacy Studio."
        ) from exc

    document = pdfium.PdfDocument(source)
    rendered = []
    skipped_labels: set[str] = set()
    found_values: set[str] = set()
    redaction_count = 0
    try:
        for page_index in range(len(document)):
            page = document[page_index]
            try:
                text_page = page.get_textpage()
                bitmap = page.render(scale=2.0)
                image = bitmap.to_pil().convert("RGB")
                bitmap.close()
                draw = ImageDraw.Draw(image)
                scale_x = image.width / page.get_width()
                scale_y = image.height / page.get_height()
                try:
                    font = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
                    )
                except OSError:
                    font = ImageFont.load_default()
                for value, (replacement, _labels) in requests.items():
                    rects = _find_text_rects(text_page, value)
                    if not rects:
                        continue
                    found_values.add(value)
                    for x0, y0, x1, y1 in rects:
                        left = max(0, int(x0 * scale_x) - 3)
                        top = max(0, int((page.get_height() - y1) * scale_y) - 3)
                        right = min(image.width, int(x1 * scale_x) + 3)
                        bottom = min(
                            image.height,
                            int((page.get_height() - y0) * scale_y) + 3,
                        )
                        box = (left, top, right, bottom)
                        draw.rectangle(box, fill="white")
                        draw.text(
                            (left + 3, top + 2),
                            replacement,
                            fill="black",
                            font=font,
                        )
                        redaction_count += 1
                rendered.append(image)
            finally:
                page.close()
        if not rendered:
            raise RuntimeError("Il PDF non contiene pagine renderizzabili.")
        target.parent.mkdir(parents=True, exist_ok=True)
        rendered[0].save(
            target,
            "PDF",
            resolution=144.0,
            save_all=True,
            append_images=rendered[1:],
        )
    finally:
        for image in rendered:
            image.close()
        document.close()

    for value, (_, labels) in requests.items():
        if value not in found_values:
            skipped_labels.update(labels)

    return {
        "pages": len(rendered),
        "redactions": redaction_count,
        "skipped_labels": sorted(skipped_labels),
        "warning": bool(skipped_labels),
        "format": "rasterized-redacted-pdf",
        "searchable": False,
    }


def redact_pdf(
    source: Path,
    target: Path,
    spans: list[dict[str, Any]],
) -> dict[str, Any]:
    requests = _requests(spans)
    if not requests:
        shutil.copy2(source, target)
        try:
            import fitz
        except ImportError:
            try:
                import pypdfium2 as pdfium

                pages = len(pdfium.PdfDocument(source))
            except ImportError:
                pages = 0
        else:
            with fitz.open(source) as document:
                pages = len(document)
        return {
            "pages": pages,
            "redactions": 0,
            "skipped_labels": [],
            "warning": False,
            "format": "original-pdf-no-redactions",
            "searchable": True,
        }
    try:
        import fitz  # noqa: F401
    except ImportError:
        result = _redact_pdf_raster(source, target, requests)
        if result["warning"]:
            target.unlink(missing_ok=True)
            labels = ", ".join(result["skipped_labels"])
            raise RuntimeError(
                "La redazione PDF non ha localizzato tutte le rilevazioni "
                f"({labels}). Il PDF non è stato prodotto per sicurezza."
            ) from None
        return result
    result = _redact_pdf_editable(source, target, requests)
    if result["warning"]:
        target.unlink(missing_ok=True)
        result = _redact_pdf_raster(source, target, requests)
        if result["warning"]:
            target.unlink(missing_ok=True)
            labels = ", ".join(result["skipped_labels"])
            raise RuntimeError(
                "La redazione PDF non ha localizzato tutte le rilevazioni "
                f"({labels}). Il PDF non è stato prodotto per sicurezza."
            ) from None
    return result
