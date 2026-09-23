# app/enhancer.py
# Módulo de mejora inteligente de currículums con IA
# ---------------------------------------------------------------------------
# Este módulo toma los datos extraídos del PDF y:
#   1. Enriquece las descripciones laborales con logros cuantificables
#   2. Optimiza el perfil profesional para el puesto objetivo
#   3. Categoriza y prioriza habilidades
#   4. Sugiere palabras clave ATS relevantes
#   5. Adapta el tono según la industria y seniority
#
# Proveedores soportados:
#   - "mock"     → MockLLMClient (sin API key, para testing)
#   - "opencode" → OpenCode Zen API (gratis, https://opencode.ai/zen)
# ---------------------------------------------------------------------------

import json
import logging
import os
from typing import Callable, Optional

from dotenv import load_dotenv
from openai import OpenAI

from .models import (
    CVData,
    ExperienciaItem,
    JobTarget,
)

load_dotenv()
log = logging.getLogger(__name__)


# ============================================================================
# Prompts del sistema
# ============================================================================

SYSTEM_PROMPT_BASE = (
    "Eres un Asistente Experto en RRHH y Optimización de Currículums para ATS "
    "(Applicant Tracking Systems). Tienes 15+ años de experiencia en reclutamiento "
    "y conoces exactamente cómo los sistemas ATS parsean, puntúan y filtran CVs.\n\n"
    "Tus capacidades:\n"
    "1. Mejorar descripciones laborales inyectando métricas cuantificables, "
    "verbos de acción potentes y logros con impacto medible.\n"
    "2. Optimizar perfiles profesionales con palabras clave del sector y del "
    "puesto objetivo.\n"
    "3. Identificar y sugerir habilidades críticas faltantes.\n"
    "4. Mantener la veracidad: nunca inventes experiencia que no exista, "
    "solo mejora la redacción de lo existente.\n"
    "5. Cuantificar logros usando el método STAR (Situación, Tarea, Acción, Resultado).\n\n"
    "REGLAS ESTRICTAS:\n"
    "- NO agregues experiencia laboral falsa.\n"
    "- NO cambies fechas, nombres de empresas ni títulos de puesto.\n"
    "- SIEMPRE usa español profesional claro y conciso.\n"
    "- Prioriza verbos de acción: 'Lideré', 'Implementé', 'Optimicé', "
    "'Coordiné', 'Desarrollé', 'Gestioné', 'Ejecuté'.\n"
    "- Incluye métricas cuando sea posible (%, montos, plazos, equipos, volúmenes)."
)

SYSTEM_PROMPT_SHORT = (
    "Eres un experto en RRHH y optimización ATS. Mejora descripciones "
    "laborales con métricas y verbos de acción sin inventar experiencia."
)


# ============================================================================
# Cliente OpenCode Zen (gratis, OpenAI-compatible)
# ============================================================================

def create_opencode_client() -> OpenAI:
    """
    Crea un cliente OpenAI conectado a OpenCode Zen.
    Usa el API_KEY de OPENCODE_API_KEY (o OPENAI_API_KEY como fallback).
    """
    api_key = os.getenv("OPENCODE_API_KEY") or os.getenv("OPENAI_API_KEY") or "dummy-key"
    base_url = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    log.info("OpenCode Zen client creado: base_url=%s", base_url)
    return client


# ============================================================================
# Mejorador Principal
# ============================================================================

class CVEnhancer:
    """
    Mejorador inteligente de currículums.
    
    Soporta dos modos:
    - "mock"     → Cliente simulado (sin API key)
    - "opencode" → OpenCode Zen API (gratis, modelos de IA)
    
    Uso:
        # Modo mock (por defecto)
        enhancer = CVEnhancer(provider="mock")
        
        # Modo OpenCode Zen (gratis)
        enhancer = CVEnhancer(provider="opencode", model="ling-3.0-flash-fin-free")
    """

    def __init__(self, provider: str = "mock", model: str = "mock"):
        """
        Args:
            provider: "mock" o "opencode"
            model: Modelo a usar (mock o opencode model ID)
        """
        self.provider = provider
        self.model = model
        self.client = None
        
        if provider == "opencode":
            self.client = create_opencode_client()
            log.info("CVEnhancer inicializado con OpenCode Zen — modelo: %s", model)
        else:
            from .mock_llm import MockLLMClient
            self.client = MockLLMClient()
            log.info("CVEnhancer inicializado con MockLLMClient — sin API key")

    # ------------------------------------------------------------------
    # 1. Mejora del perfil profesional
    # ------------------------------------------------------------------

    def _build_profile_prompt(self, cv: CVData, target: JobTarget) -> str:
        return f"""
 Tengo un currículum con el siguiente perfil profesional ORIGINAL:

 "{cv.perfil}"

 El candidato postula al puesto de: **{target.titulo}**
 Industria: {target.industria or "No especificada"}
 Seniority: {target.seniority}
 Tono deseado: {target.tono}
 Idioma: {target.idioma}

 Experiencia del candidato:
 {self._format_experience_summary(cv)}

 Habilidades del candidato:
 {', '.join(cv.habilidades)}

 INSTRUCCIONES:
 Genera un perfil profesional MEJORADO que:
 1. Mantenga la esencia y veracidad del perfil original
 2. Esté optimizado con palabras clave relevantes para "{target.titulo}"
 3. Use el tono "{target.tono}" apropiado
 4. Destaque los logros más relevantes para el puesto objetivo
 5. Tenga entre 3-5 líneas de extensión
 6. Esté escrito en {"español" if target.idioma == "es" else "inglés" if target.idioma == "en" else "mixto español/inglés"}

 Responde SOLO con el texto del perfil mejorado, sin explicaciones adicionales.
 """

    # ------------------------------------------------------------------
    # 2. Mejora de logros laborales
    # ------------------------------------------------------------------

    def _build_experience_prompt(
        self, exp: ExperienciaItem, target: JobTarget, idx: int
    ) -> str:
        logros_text = "\n".join(f"- {l}" for l in exp.logros)
        return f"""
 Experiencia laboral #{idx + 1}:
 - Puesto: {exp.puesto}
 - Empresa: {exp.empresa}
 - Fechas: {exp.fechas}
 - Logros originales:
 {logros_text}

 Puesto objetivo del candidato: {target.titulo}
 Industria: {target.industria or "No especificada"}
 Tono: {target.tono}

 INSTRUCCIONES:
 Reescribe cada logro para que sea más impactante usando:
 1. Verbos de acción fuertes
 2. Métricas cuantificables cuando sea posible (inferirlas del contexto)
 3. Palabras clave relevantes para {target.titulo}
 4. Estructura: [Acción] + [Qué] + [Resultado/Impacto] + [Métrica si aplica]

 Ejemplo de mejora:
 ❌ "Atendí público a bordo"
 ✅ "Brindé atención personalizada a más de 500 pasajeros semanales en rutas interurbanas, "
    "logrando un 95% de satisfacción en encuestas de servicio al cliente"

 IMPORTANTE: Mantén la veracidad. No inventes tecnologías, certificaciones o responsabilidades
 que no existan en el original. Solo mejora la redacción y añade métricas contextuales razonables.

 Responde en formato JSON:
 {{"logros_mejorados": ["logro1", "logro2", ...]}}
 """

    # ------------------------------------------------------------------
    # 3. Mejora de habilidades
    # ------------------------------------------------------------------

    def _build_skills_prompt(self, cv: CVData, target: JobTarget) -> str:
        return f"""
 Habilidades actuales del candidato:
 {json.dumps(cv.habilidades, ensure_ascii=False, indent=2)}

 Puesto objetivo: {target.titulo}
 Industria: {target.industria or "No especificada"}
 Seniority: {target.seniority}
 Keywords adicionales: {', '.join(target.keywords_adicionales) if target.keywords_adicionales else "Ninguna"}

 INSTRUCCIONES:
 1. Categoriza las habilidades en grupos lógicos (Técnicas, Blandas, Idiomas, etc.)
 2. Prioriza las habilidades más relevantes para el puesto objetivo al inicio
 3. Sugiere hasta 5 palabras clave ATS adicionales relevantes para {target.titulo} en {target.industria or "la industria"}
    que sean coherentes con la experiencia del candidato
 4. NO agregues habilidades que el candidato claramente no posee

 Responde en formato JSON:
 {{
     "habilidades_organizadas": ["hab1", "hab2", ...],
     "palabras_clave_ats": ["keyword1", "keyword2", ...]
 }}
 """

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------

    def _format_experience_summary(self, cv: CVData) -> str:
        parts = []
        for exp in cv.experiencia_laboral:
            parts.append(f"- {exp.puesto} en {exp.empresa} ({exp.fechas})")
        return "\n".join(parts) if parts else "Sin experiencia registrada"

    # ------------------------------------------------------------------
    # Pipeline principal de mejora
    # ------------------------------------------------------------------

    def enhance(
        self,
        cv: CVData,
        target: JobTarget,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> CVData:
        """
        Ejecuta el pipeline completo de mejora sobre un CV.

        Args:
            cv: Datos originales del CV.
            target: Configuración del puesto objetivo.
            progress_callback: Función opcional para reportar progreso.

        Returns:
            CVData con todos los campos mejorados poblados.
        """
        if progress_callback:
            progress_callback("Mejorando perfil profesional...")

        # 1. Mejorar perfil profesional
        try:
            cv.perfil_mejorado = self._call_llm_simple(
                self._build_profile_prompt(cv, target),
                system=SYSTEM_PROMPT_BASE,
                max_tokens=300,
            )
            log.info("Perfil profesional mejorado exitosamente")
        except Exception as e:
            log.warning("Error mejorando perfil: %s. Usando original.", e)
            cv.perfil_mejorado = cv.perfil

        # 2. Mejorar cada experiencia laboral
        for i, exp in enumerate(cv.experiencia_laboral):
            if progress_callback:
                progress_callback(f"Mejorando experiencia: {exp.puesto} en {exp.empresa}...")

            if not exp.logros:
                exp.logros_mejorados = exp.logros
                continue

            try:
                result_json = self._call_llm_json(
                    self._build_experience_prompt(exp, target, i),
                    system=SYSTEM_PROMPT_BASE,
                    max_tokens=500,
                )
                exp.logros_mejorados = result_json.get("logros_mejorados", exp.logros)
                log.info("  → Experiencia #%d mejorada: %s", i + 1, exp.puesto)
            except Exception as e:
                log.warning("  → Error en experiencia #%d: %s. Usando original.", i + 1, e)
                exp.logros_mejorados = exp.logros

        # 3. Mejorar habilidades
        if progress_callback:
            progress_callback("Optimizando habilidades y palabras clave ATS...")

        try:
            skills_result = self._call_llm_json(
                self._build_skills_prompt(cv, target),
                system=SYSTEM_PROMPT_BASE,
                max_tokens=400,
            )
            cv.habilidades_mejoradas = skills_result.get(
                "habilidades_organizadas", cv.habilidades
            )
            cv.palabras_clave_ats = skills_result.get(
                "palabras_clave_ats", []
            )
            log.info("Habilidades organizadas y keywords ATS generadas")
        except Exception as e:
            log.warning("Error optimizando habilidades: %s", e)
            cv.habilidades_mejoradas = cv.habilidades

        return cv

    # ------------------------------------------------------------------
    # LLM interaction helpers
    # ------------------------------------------------------------------

    def _call_llm_simple(
        self,
        prompt: str,
        system: str = SYSTEM_PROMPT_SHORT,
        max_tokens: int = 300,
    ) -> str:
        """Llama al LLM (mock o OpenCode) y devuelve texto plano."""
        if self.provider == "opencode" and self.client:
            return self._call_opencode_simple(prompt, system, max_tokens)
        return self._call_mock_simple(prompt, system, max_tokens)

    def _call_llm_json(
        self,
        prompt: str,
        system: str = SYSTEM_PROMPT_SHORT,
        max_tokens: int = 500,
    ) -> dict:
        """Llama al LLM (mock o OpenCode) y parsea la respuesta como JSON."""
        if self.provider == "opencode" and self.client:
            return self._call_opencode_json(prompt, system, max_tokens)
        return self._call_mock_json(prompt, system, max_tokens)

    # --- OpenCode Zen methods ---

    def _call_opencode_simple(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
    ) -> str:
        """Llama a OpenCode Zen y devuelve texto plano."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""

    def _call_opencode_json(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
    ) -> dict:
        """Llama a OpenCode Zen y parsea la respuesta como JSON."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        if not content:
            return {}
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            log.warning("Respuesta JSON inválida de OpenCode: %s", content[:200])
            return {}

    # --- Mock methods (fallback) ---

    def _call_mock_simple(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
    ) -> str:
        """Llama al MockLLMClient y devuelve texto plano."""
        from .mock_llm import MockLLMClient
        client = MockLLMClient()
        response = client.chat.completions.create(
            model="mock",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""

    def _call_mock_json(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
    ) -> dict:
        """Llama al MockLLMClient y parsea la respuesta como JSON."""
        from .mock_llm import MockLLMClient
        client = MockLLMClient()
        response = client.chat.completions.create(
            model="mock",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            return {}
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {}
