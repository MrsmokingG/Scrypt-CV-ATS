"""
app/mock_llm.py
---------------
Cliente LLM simulado (mock) para desarrollo/pruebas sin API key real.

Emula la interfaz de openai.OpenAI:
  - client.chat.completions.create()        → texto plano (para enhance)
  - client.beta.chat.completions.parse()    → CVData (para estructurar PDF)

El parser heurístico extrae: nombre, contacto, perfil, experiencias,
educación y habilidades del texto plano del PDF.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Type

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Estructuras de respuesta que emulan la API de OpenAI
# ---------------------------------------------------------------------------

@dataclass
class MockMessage:
    content: Optional[str] = None
    parsed: Any = None

@dataclass
class MockChoice:
    message: MockMessage = field(default_factory=MockMessage)

@dataclass
class MockCompletion:
    choices: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser heurístico de CV (sin IA)
# ---------------------------------------------------------------------------

def _parse_cv_heuristic(raw_text: str):
    """
    Extrae información estructurada de un CV en texto plano usando
    expresiones regulares y detección de secciones.
    Retorna un dict compatible con CVData.
    """
    from .models import CVData, ExperienciaItem, EducacionItem

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    # -- Contacto: primeras líneas + regex email/teléfono --
    email_pat = re.compile(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', re.I)
    phone_pat = re.compile(r'(\+?56\s?)?[\d\s\-\(\)]{8,15}')

    contact_parts = lines[:5] if len(lines) >= 5 else lines[:]
    email = next((m.group() for l in lines for m in [email_pat.search(l)] if m), "")
    phone = next((m.group().strip() for l in lines for m in [phone_pat.search(l)] if m), "")
    if email and email not in " ".join(contact_parts):
        contact_parts.append(email)
    if phone and phone not in " ".join(contact_parts):
        contact_parts.append(phone)
    datos_contacto = " | ".join(contact_parts)

    # -- Secciones del CV --
    SECTION_KEYS = {
        "perfil":       ["perfil", "resumen", "sobre mí", "objetivo", "summary", "profile"],
        "experiencia":  ["experiencia", "trayectoria", "historial", "experience", "trabajo"],
        "educacion":    ["educaci", "formaci", "estudios", "education", "certificaci", "cursos"],
        "habilidades":  ["habilidades", "competencias", "skills", "aptitudes", "tecnologías", "conocimientos"],
    }

    def detect_section(line: str) -> Optional[str]:
        low = line.lower()
        for sec, keys in SECTION_KEYS.items():
            if any(k in low for k in keys) and len(line) < 60:
                return sec
        return None

    sections: dict[str, list[str]] = {k: [] for k in SECTION_KEYS}
    current = None

    for line in lines:
        sec = detect_section(line)
        if sec:
            current = sec
            continue
        if current:
            sections[current].append(line)

    # -- Perfil --
    perfil = " ".join(sections["perfil"][:6]) if sections["perfil"] else (
        "Profesional con experiencia en el sector, orientado a resultados y trabajo en equipo."
    )

    # -- Experiencias --
    date_pat = re.compile(
        r'(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic|enero|febrero|marzo|'
        r'abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|'
        r'jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w.]*'
        r'\s*\.?\s*\d{2,4}',
        re.I
    )

    experiences = []
    exp_lines = sections["experiencia"]
    i = 0
    while i < len(exp_lines):
        line = exp_lines[i]
        # Detectar línea de puesto/empresa buscando patrones de fecha cercanos
        has_date_nearby = any(
            date_pat.search(exp_lines[j])
            for j in range(max(0, i-1), min(len(exp_lines), i+4))
        )
        if has_date_nearby and len(line) < 80 and not line.startswith(("-", "•", "·", "*")):
            puesto = line
            empresa = exp_lines[i+1] if i+1 < len(exp_lines) else "Empresa"
            fecha_line = ""
            logros = []
            j = i + 2
            while j < len(exp_lines):
                if date_pat.search(exp_lines[j]):
                    fecha_line = exp_lines[j]
                    j += 1
                    break
                j += 1
            # Recoger logros hasta próximo bloque
            while j < len(exp_lines):
                l = exp_lines[j]
                if detect_section(l):
                    break
                # Si parece encabezado de nueva experiencia, parar
                if (len(l) < 80 and not l.startswith(("-", "•", "·", "*"))
                        and any(date_pat.search(exp_lines[k]) for k in range(j, min(j+4, len(exp_lines))))):
                    break
                if l.startswith(("-", "•", "·", "*")):
                    logros.append(l.lstrip("-•·* "))
                elif l:
                    logros.append(l)
                j += 1

            if not fecha_line:
                fecha_line = "Fecha no especificada"
            experiences.append(ExperienciaItem(
                puesto=puesto,
                empresa=empresa,
                fechas=fecha_line,
                logros=logros[:8],
            ))
            i = j
        else:
            i += 1

    # Fallback si no se detectaron experiencias estructuradas
    if not experiences:
        block = []
        for line in exp_lines:
            if line.startswith(("-", "•", "·", "*")):
                block.append(line.lstrip("-•·* "))
        if block:
            experiences.append(ExperienciaItem(
                puesto="Cargo no especificado",
                empresa="Empresa no especificada",
                fechas="Fechas no especificadas",
                logros=block[:8],
            ))

    # -- Educación --
    from .models import EducacionItem
    educacion = []
    edu_lines = sections["educacion"]
    for idx, line in enumerate(edu_lines):
        if len(line) > 10 and not line.startswith(("-", "•")):
            institucion = edu_lines[idx+1] if idx+1 < len(edu_lines) else ""
            fecha = ""
            m = re.search(r'\d{4}', line)
            if not m and idx+1 < len(edu_lines):
                m = re.search(r'\d{4}', edu_lines[idx+1])
            if m:
                fecha = m.group()
            educacion.append(EducacionItem(
                titulo=line,
                institucion=institucion,
                fechas=fecha,
            ))
            if len(educacion) >= 5:
                break

    # -- Habilidades --
    skill_separators = re.compile(r'[,;|·•\n]')
    raw_skills = " | ".join(sections["habilidades"])
    habilidades = [
        s.strip().strip("-•·* ")
        for s in skill_separators.split(raw_skills)
        if len(s.strip()) > 2
    ][:25]

    if not habilidades:
        # Fallback: buscar palabras capitalizadas frecuentes como habilidades
        candidates = re.findall(r'\b[A-Z][a-záéíóúüñ]{2,}\b', raw_text)
        habilidades = list(dict.fromkeys(candidates))[:15]

    return CVData(
        datos_contacto=datos_contacto,
        perfil=perfil,
        experiencia_laboral=experiences,
        educacion=educacion,
        habilidades=habilidades,
    )


# ---------------------------------------------------------------------------
# Cliente mock principal
# ---------------------------------------------------------------------------

class _MockBetaCompletions:
    def parse(self, *, model: str, messages: list, response_format: Type, **kwargs) -> MockCompletion:
        """
        Emula client.beta.chat.completions.parse().
        Usa el texto del mensaje del usuario para hacer el parse heurístico.
        """
        log.info("[MOCK] beta.chat.completions.parse() — usando parser heurístico")
        user_content = next(
            (m["content"] for m in messages if m["role"] == "user"), ""
        )
        # Extraer el texto del CV del prompt (entre ```...```)
        match = re.search(r'```\n(.*?)```', user_content, re.DOTALL)
        raw_text = match.group(1) if match else user_content

        parsed = _parse_cv_heuristic(raw_text)
        return MockCompletion(choices=[MockChoice(message=MockMessage(parsed=parsed))])


class _MockCompletions:
    def create(self, *, model: str, messages: list, **kwargs) -> MockCompletion:
        """
        Emula client.chat.completions.create().
        Para mejoras: devuelve el contenido del prompt del usuario sin cambios.
        Si se pide JSON, devuelve un JSON mínimo válido.
        """
        log.info("[MOCK] chat.completions.create() — devolviendo respuesta simulada")
        user_content = next(
            (m["content"] for m in messages if m["role"] == "user"), ""
        )
        response_format = kwargs.get("response_format", {})

        if isinstance(response_format, dict) and response_format.get("type") == "json_object":
            # Detectar qué tipo de JSON se espera por el contenido del prompt
            if "logros_mejorados" in user_content:
                # Extraer logros originales del prompt para devolverlos
                logros = re.findall(r'^- (.+)$', user_content, re.MULTILINE)
                import json
                content = json.dumps({"logros_mejorados": logros or ["Logro no especificado"]}, ensure_ascii=False)
            elif "habilidades_organizadas" in user_content:
                import json
                content = json.dumps({
                    "habilidades_organizadas": [],
                    "palabras_clave_ats": [],
                }, ensure_ascii=False)
            else:
                content = "{}"
        else:
            # Respuesta texto: devolver el perfil original si está en el prompt
            match = re.search(r'"(.+?)"', user_content, re.DOTALL)
            content = match.group(1) if match else "Perfil profesional del candidato."

        return MockCompletion(choices=[MockChoice(message=MockMessage(content=content))])


class _MockBeta:
    def __init__(self):
        self.chat = type("obj", (), {"completions": _MockBetaCompletions()})()


class MockLLMClient:
    """
    Cliente LLM simulado que emula la interfaz de openai.OpenAI.

    Uso:
        client = MockLLMClient()
        # Igual que OpenAI — sin API key necesaria
    """
    def __init__(self, api_key: str = "mock-key"):
        self.chat = type("obj", (), {"completions": _MockCompletions()})()
        self.beta = _MockBeta()
        log.info("[MOCK] MockLLMClient inicializado — no se requiere API key real")

