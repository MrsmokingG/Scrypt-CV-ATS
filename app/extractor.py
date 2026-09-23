# app/extractor.py
# Módulo de extracción de texto desde PDF usando pdfplumber
# ---------------------------------------------------------------------------
# Estrategia:
#   - Recorta el PDF en dos regiones rectangulares (sidebar + main)
#   - Extrae cada región por separado para evitar entremezclar columnas
#   - Ordena los bloques por coordenada Y (top → bottom)
#   - Concatena primero columna izquierda y luego derecha
# ---------------------------------------------------------------------------

import logging
from pathlib import Path

import pdfplumber

log = logging.getLogger(__name__)

# Umbral X para separar sidebar (columna izquierda) del contenido principal.
# En la mayoría de CVs con diseño A4 (210mm ≈ 595pt), la sidebar suele
# ocupar hasta ~200pt.
SIDEBAR_X_THRESHOLD: float = 200.0


def extract_pdf_text(
    filepath: str,
    sidebar_threshold: float = SIDEBAR_X_THRESHOLD,
) -> str:
    """
    Extrae texto de un PDF respetando el orden semántico de doble columna.

    Args:
        filepath: Ruta absoluta o relativa al archivo PDF.
        sidebar_threshold: Coordenada X (en pt) que separa ambas columnas.

    Returns:
        Texto plano completo con orden de lectura preservado.

    Raises:
        FileNotFoundError: Si el PDF no existe.
        ValueError: Si el PDF está corrupto o sin páginas.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {filepath}")

    with pdfplumber.open(str(path)) as pdf:
        if not pdf.pages:
            raise ValueError("El PDF no contiene páginas.")

        full_text_parts = []

        for page_num, page in enumerate(pdf.pages, start=1):
            width = page.width
            height = page.height
            log.info(
                "Procesando página %d (%.0f x %.0f pt)", page_num, width, height
            )

            # --- Detección dinámica de umbral ---
            # Si la página es más angosta, ajustar el umbral automáticamente
            effective_threshold = min(sidebar_threshold, width * 0.35)

            # Región 1: Sidebar (x: 0 → threshold)
            sidebar_bbox = (0, 0, effective_threshold, height)
            sidebar_text = _extract_region_text(page, sidebar_bbox)

            # Región 2: Main content (x: threshold → ancho página)
            main_bbox = (effective_threshold, 0, width, height)
            main_text = _extract_region_text(page, main_bbox)

            # Orden semántico: primero sidebar, luego contenido principal
            page_text = f"{sidebar_text}\n\n{main_text}"
            full_text_parts.append(page_text.strip())

    result = "\n\n---\n\n".join(part for part in full_text_parts if part)
    log.info("Texto extraído: %d caracteres", len(result))
    return result


def _extract_region_text(page, bbox: tuple) -> str:
    """
    Extrae texto de una región rectangular de la página.

    Corta la página al Bounding Box dado, extrae palabras con sus coordenadas,
    las ordena por (top, x0) y reconstruye párrafos.

    Args:
        page: Objeto Page de pdfplumber.
        bbox: Tupla (x0, y0, x1, y1) en pt.

    Returns:
        Texto plano de la región.
    """
    try:
        cropped = page.within_bbox(bbox)
    except Exception:
        return ""

    words = cropped.extract_words(keep_blank_chars=True, x_tolerance=3)
    if not words:
        return ""

    # Ordenar por coordenada Y (top) y X (x0) para respetar lectura
    words_sorted = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))

    lines = []
    current_line_y = None
    current_line_text = []

    for w in words_sorted:
        y = round(w["top"], 1)
        # Si cambia la línea significativamente (> 5pt), cerramos la anterior
        if current_line_y is not None and abs(y - current_line_y) > 5:
            lines.append(" ".join(current_line_text))
            current_line_text = []
        current_line_y = y
        current_line_text.append(w["text"])

    if current_line_text:
        lines.append(" ".join(current_line_text))

    return "\n".join(lines)

