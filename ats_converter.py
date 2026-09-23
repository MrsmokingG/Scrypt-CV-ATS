#!/usr/bin/env python3
"""
Scrypt CV ATS v2.0 — Intelligent CV Enhancement Suite
======================================================
Convierte y mejora currículums en PDF a formato ATS-optimizado
con inyección inteligente de texto mediante IA.

Arquitectura Modular:
  app/
    extractor.py   → Extracción de texto desde PDF con pdfplumber
    models.py      → Modelos Pydantic para datos estructurados
    enhancer.py    → Motor de mejora con IA (blackbox AI Structured Outputs)
    generator.py   → Generación de .docx y .html ATS-friendly

Uso:
  # Pipeline básico (extraer + estructurar)
  python ats_converter.py -i curriculum.pdf -o curriculum_ats.docx

  # Pipeline completo con mejora IA para puesto objetivo
  python ats_converter.py -i curriculum.pdf -o curriculum_ats.docx \\
      -j "Jefe de Operaciones Mineras" --industry "Minería" --enhance

  # Generar también HTML visual ATS
  python ats_converter.py -i curriculum.pdf -f both --enhance

  # Ver ayuda
  python ats_converter.py --help
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from app import (
    extract_pdf_text,
    CVData,
    JobTarget,
    CVEnhancer,
    generate_ats_docx,
    generate_ats_html,
)

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ============================================================================
# Procesamiento del CV original (sin mejora)
# ============================================================================

def process_cv_basic(input_path: str, output_path: str, threshold: float):
    """
    Pipeline básico: Extracción → Estructuración (mock) → Generación DOCX.
    """
    from app.extractor import extract_pdf_text
    from app.models import CVData
    from app.mock_llm import MockLLMClient

    raw_text = extract_pdf_text(input_path, sidebar_threshold=threshold)

    if not raw_text.strip():
        log.error("El PDF no contiene texto extraíble.")
        sys.exit(1)

    log.info(f"  → {len(raw_text)} caracteres extraídos")

    # --- Estructurar con mock (parser heurístico) ---
    client = MockLLMClient()

    SYSTEM_PROMPT = (
        "Eres un asistente experto en recursos humanos y procesamiento de currículums. "
        "Tu tarea es extraer y estructurar la información de un CV en texto plano."
    )
    USER_PROMPT = (
        "Procesa el siguiente texto extraído de un currículum en PDF y devuélvelo "
        "estructurado en formato JSON con los campos especificados.\n\n"
        "Texto del CV:\n```\n{raw_text}\n```"
    )

    log.info("Estructurando CV (modo mock — sin API key)...")
    completion = client.beta.chat.completions.parse(
        model="mock",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT.format(raw_text=raw_text)},
        ],
        response_format=CVData,
        temperature=0.1,
    )
    cv_data: CVData = completion.choices[0].message.parsed
    if cv_data is None:
        log.error("El mock retornó None inesperadamente.")
        sys.exit(1)

    log.info(f"  → Experiencias: {len(cv_data.experiencia_laboral)}")
    log.info(f"  → Educación: {len(cv_data.educacion)}")
    log.info(f"  → Habilidades: {len(cv_data.habilidades)}")

    # --- Generar .docx ---
    log.info("Generando documento .docx...")
    generate_ats_docx(cv_data, output_path)
    log.info(f"Documento guardado: {output_path}")

    return cv_data


# ============================================================================
# Procesamiento completo con mejora IA
# ============================================================================

def process_cv_enhanced(
    input_path: str,
    output_docx: Optional[str],
    output_html: Optional[str],
    target: JobTarget,
    threshold: float,
    provider: str = "opencode",
    model: str = "ling-3.0-flash-fin-free",
):
    """
    Pipeline completo: Extracción → Estructuración → Mejora IA → Generación.
    """
    from dotenv import load_dotenv
    load_dotenv()

    # --- Paso 1: Extraer texto del PDF ---
    log.info("[1/5] Extrayendo texto del PDF...")
    raw_text = extract_pdf_text(input_path, sidebar_threshold=threshold)

    if not raw_text.strip():
        log.error("El PDF no contiene texto extraíble.")
        sys.exit(1)

    log.info(f"  → {len(raw_text)} caracteres extraídos")

    # --- Paso 2: Estructurar con mock ---
    log.info("[2/5] Estructurando CV (modo mock — sin API key)...")
    from app.mock_llm import MockLLMClient

    client = MockLLMClient()

    SYSTEM_PROMPT = (
        "Eres un asistente experto en recursos humanos y procesamiento de currículums. "
        "Tu tarea es extraer y estructurar la información de un CV en texto plano."
    )
    USER_PROMPT = (
        "Procesa el siguiente texto extraído de un currículum en PDF y devuélvelo "
        "estructurado en formato JSON con los campos especificados.\n\n"
        "Texto del CV:\n```\n{raw_text}\n```"
    )

    completion = client.beta.chat.completions.parse(
        model="mock",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT.format(raw_text=raw_text)},
        ],
        response_format=CVData,
        temperature=0.1,
    )
    cv_data: CVData = completion.choices[0].message.parsed
    if cv_data is None:
        log.error("El mock retornó None inesperadamente.")
        sys.exit(1)
    log.info(f"  → Experiencias: {len(cv_data.experiencia_laboral)}")
    log.info(f"  → Educación: {len(cv_data.educacion)}")
    log.info(f"  → Habilidades: {len(cv_data.habilidades)}")


    # --- Paso 3: Mejorar con IA ---
    log.info("[3/5] Mejorando contenido con IA para puesto: %s...", target.titulo)

    def progress(msg):
        log.info("  ⏳ %s", msg)

    enhancer = CVEnhancer(provider=provider, model=model)
    cv_mejorado = enhancer.enhance(cv_data, target, progress_callback=progress)

    log.info("  → Perfil mejorado: %s", "✓" if cv_mejorado.perfil_mejorado else "✗")
    log.info("  → Experiencias mejoradas: %d/%d",
             sum(1 for e in cv_mejorado.experiencia_laboral if e.logros_mejorados),
             len(cv_mejorado.experiencia_laboral))
    log.info("  → Keywords ATS generadas: %d", len(cv_mejorado.palabras_clave_ats))

    # --- Paso 4: Generar .docx (opcional) ---
    if output_docx:
        log.info("[4/5] Generando documento .docx...")
        generate_ats_docx(cv_mejorado, output_docx, target=target, use_enhanced=True)
        log.info(f"  → Guardado: {output_docx}")
    else:
        log.info("[4/5] .docx no solicitado (omitido)")

    # --- Paso 5: Generar .html (opcional) ---
    if output_html:
        log.info("[5/5] Generando página HTML...")
        generate_ats_html(cv_mejorado, output_html, target=target, use_enhanced=True)
        log.info(f"  → Guardado: {output_html}")
    else:
        log.info("[5/5] HTML no solicitado (omitido)")

    return cv_mejorado


# ============================================================================
# CLI
# ============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scrypt CV ATS v2 — Convierte y mejora currículums PDF "
            "a formato ATS-optimizado con IA."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  # Pipeline básico\n"
            "  python ats_converter.py -i curriculum.pdf -o curriculum_ats.docx\n\n"
            "  # Pipeline completo con mejora para puesto objetivo\n"
            "  python ats_converter.py -i curriculum.pdf -j \"Jefe de Operaciones\" "
            "--enhance -f both\n\n"
            "  # Especificar industria y tono\n"
            "  python ats_converter.py -i curriculum.pdf -j \"Analista\" "
            "--industry \"Minería\" --tone tecnico --enhance\n"
        ),
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Ruta al archivo PDF de entrada.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Ruta de salida para el archivo .docx (default: {input}_ats.docx).",
    )
    parser.add_argument(
        "--output-html",
        default=None,
        help="Ruta de salida para el archivo .html (default: {input}_ats.html si --format=both).",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["docx", "html", "both"],
        default="docx",
        help="Formato de salida (default: docx).",
    )
    parser.add_argument(
        "--enhance", "-e",
        action="store_true",
        help="Activar mejora de contenido con IA (requiere --job-target).",
    )
    parser.add_argument(
        "--job-target", "-j",
        default=None,
        help="Título del puesto objetivo para personalizar el CV (ej: 'Jefe de Operaciones').",
    )
    parser.add_argument(
        "--industry",
        default=None,
        help="Industria o sector (ej: 'Minería', 'Construcción', 'Logística').",
    )
    parser.add_argument(
        "--seniority",
        default="Sin especificar",
        help="Nivel: Entry, Junior, Mid, Senior, Lead, Manager (default: Sin especificar).",
    )
    parser.add_argument(
        "--tone",
        default="profesional",
        choices=["profesional", "ejecutivo", "técnico", "creativo", "minero-industrial"],
        help="Tono del CV (default: profesional).",
    )
    parser.add_argument(
        "--keywords",
        default=None,
        help="Palabras clave adicionales separadas por coma (ej: 'Lean Six Sigma,ISO 9001,SAP').",
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=200.0,
        help="Umbral X (en pt) para separar columnas en PDF (default: 200).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Activar logging detallado.",
    )
    parser.add_argument(
        "--provider",
        default="opencode",
        choices=["mock", "opencode"],
        help="Proveedor de IA para mejora: 'mock' (sin API) o 'opencode' (gratis).",
    )
    parser.add_argument(
        "--model",
        default="ling-3.0-flash-fin-free",
        help="Modelo OpenCode a usar (default: ling-3.0-flash-fin-free).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # === Configurar rutas ===
    input_path = args.input
    stem = Path(input_path).stem
    parent = Path(input_path).parent

    output_docx = None
    output_html = None

    if args.format == "docx":
        output_docx = args.output or str(parent / f"{stem}_ats.docx")
    elif args.format == "html":
        output_html = args.output or str(parent / f"{stem}_ats.html")
    elif args.format == "both":
        output_docx = args.output or str(parent / f"{stem}_ats.docx")
        output_html = args.output_html or str(parent / f"{stem}_ats.html")

    # === Configurar puesto objetivo ===
    job_target = None
    if args.job_target:
        keywords_list = []
        if args.keywords:
            keywords_list = [k.strip() for k in args.keywords.split(",")]

        job_target = JobTarget(
            titulo=args.job_target,
            industria=args.industry,
            seniority=args.seniority,
            tono=args.tone,
            keywords_adicionales=keywords_list,
        )

    # === Banner ===
    log.info("=" * 55)
    log.info("  Scrypt CV ATS v2 — Intelligent CV Enhancement Suite")
    log.info("=" * 55)
    log.info("  Input : %s", input_path)
    log.info("  Output: %s", output_docx or output_html or "N/A")
    if job_target:
        log.info("  Target: %s (%s)", job_target.titulo, job_target.industria or "N/E")
        log.info("  Tonos : %s", job_target.tono)
        log.info("  Mejora: %s", "ACTIVADA" if args.enhance else "SÓLO ESTRUCTURA")
    log.info("  Format: %s", args.format)
    if args.enhance and job_target:
        log.info("  Proveedor: %s", args.provider)
        log.info("  Modelo: %s", args.model)
    log.info("=" * 55)

    # === Ejecutar pipeline ===
    if args.enhance and job_target:
        process_cv_enhanced(
            input_path=input_path,
            output_docx=output_docx,
            output_html=output_html,
            target=job_target,
            threshold=args.threshold,
            provider=args.provider,
            model=args.model,
        )
    elif args.job_target and not args.enhance:
        log.warning(
            "Se especificó --job-target pero no --enhance. "
            "El CV se procesará sin mejora IA. "
            "Agrega --enhance para activar la personalización."
        )
        if output_docx:
            process_cv_basic(input_path, output_docx, args.threshold)
    else:
        if output_docx:
            process_cv_basic(input_path, output_docx, args.threshold)

    log.info("¡Procesamiento completado exitosamente!")
    return 0


if __name__ == "__main__":
    exit(main())
