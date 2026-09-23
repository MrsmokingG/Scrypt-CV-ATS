# app/models.py
# Modelos de datos del currículum — usando Pydantic dataclasses
# Compatible con json_schema() para generación de esquemas ATS.
# ---------------------------------------------------------------------------

from dataclasses import field
from typing import Optional, List
from pydantic.dataclasses import dataclass


# ============================================================================
# Modelos Base (estructura ATS)
# ============================================================================

@dataclass
class LogroItem:
    """Un logro o responsabilidad dentro de un puesto laboral."""
    descripcion: str = ""
    mejorado: Optional[str] = None


@dataclass
class ExperienciaItem:
    """Experiencia laboral individual."""
    puesto: str = ""
    empresa: str = ""
    fechas: str = ""
    logros: List[str] = field(default_factory=list)
    logros_mejorados: List[str] = field(default_factory=list)


@dataclass
class EducacionItem:
    """Registro educativo o formación."""
    titulo: str = ""
    institucion: str = ""
    fechas: str = ""


@dataclass
class CVData:
    """Estructura completa del currículum procesado (base)."""
    datos_contacto: str = ""
    perfil: str = ""
    perfil_mejorado: Optional[str] = None
    experiencia_laboral: List[ExperienciaItem] = field(default_factory=list)
    educacion: List[EducacionItem] = field(default_factory=list)
    habilidades: List[str] = field(default_factory=list)
    habilidades_mejoradas: List[str] = field(default_factory=list)
    palabras_clave_ats: List[str] = field(default_factory=list)


# ============================================================================
# Modelo de Configuración de Mejora
# ============================================================================

@dataclass
class JobTarget:
    """Configuración del puesto objetivo para personalización del CV."""
    titulo: str = ""
    industria: Optional[str] = None
    seniority: Optional[str] = "Sin especificar"
    keywords_adicionales: List[str] = field(default_factory=list)
    tono: str = "profesional"
    idioma: str = "es"


# ============================================================================
# Modelo Extendido (con metadatos de mejora)
# ============================================================================

@dataclass
class EnhancedCVData:
    """Contenedor final: CV original + metadatos + contenido mejorado."""
    cv_original: Optional[CVData] = None
    job_target: Optional[JobTarget] = None
    cv_mejorado: Optional[CVData] = None
    score_ats: Optional[float] = None
    sugerencias: List[str] = field(default_factory=list)
