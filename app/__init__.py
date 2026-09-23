# Scrypt CV ATS - Intelligent CV Enhancement Suite
# Paquete principal de la aplicación modular

__version__ = "2.0.0"
__author__ = "Scrypt CV ATS Team"

from .extractor import extract_pdf_text
from .models import (
    CVData,
    ExperienciaItem,
    EducacionItem,
    LogroItem,
    JobTarget,
    EnhancedCVData,
)
from .enhancer import CVEnhancer
from .generator import generate_ats_docx, generate_ats_html

__all__ = [
    "extract_pdf_text",
    "CVData",
    "ExperienciaItem",
    "EducacionItem",
    "LogroItem",
    "JobTarget",
    "EnhancedCVData",
    "CVEnhancer",
    "generate_ats_docx",
    "generate_ats_html",
]

