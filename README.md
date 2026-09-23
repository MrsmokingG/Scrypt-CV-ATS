# Scrypt CV ATS v2.0 — Intelligent CV Enhancement Suite

> **Convierte y mejora currículums en PDF a formato ATS-optimizado con inyección inteligente de texto mediante IA.**

## 🚀 Novedades v2.0

### 🧠 Inyección Inteligente de Texto con IA
El sistema no solo extrae y estructura tu CV — **lo mejora activamente**:
- **Perfil profesional potenciado**: Reescribe tu resumen alineándolo al puesto objetivo
- **Logros cuantificables**: Convierte descripciones genéricas en logros con métricas (método STAR)
- **Keywords ATS**: Genera palabras clave específicas de la industria y el puesto
- **Tono adaptable**: Profesional, ejecutivo, técnico, creativo, o minero-industrial

### 🎯 Personalización por Puesto Objetivo
- Define el **título del puesto** al que postulas
- Selecciona la **industria** (Minería, Construcción, Logística, etc.)
- Ajusta el **seniority** (Entry, Junior, Mid, Senior, Lead, Manager)
- Agrega **palabras clave adicionales** del sector

### 📄 Formatos de Salida
- **DOCX** — Documento Word lineal, ATS-friendly (python-docx)
- **HTML** — Página web con diseño ATS, microdatos Schema.org, responsive
- **Both** — Ambos formatos simultáneamente

## 📦 Arquitectura Modular

```
scrypt-cv-ats/
├── app/                    # Paquete principal
│   ├── __init__.py         # Inicialización y exports
│   ├── extractor.py        # Extracción de texto desde PDF (pdfplumber)
│   ├── models.py           # Modelos Pydantic (CVData, JobTarget, EnhancedCVData)
│   ├── enhancer.py         # Motor de mejora con IA (OpenCode Zen / Mock)
│   ├── generator.py        # Generación .docx y .html ATS-friendly
│   └── mock_llm.py         # Cliente LLM simulado (funciona sin API key)
├── ats_converter.py        # CLI entry point
├── pyproject.toml          # Configuración del proyecto
├── requirements.txt        # Dependencias Python
├── .env.example            # Template de configuración
├── api_schema.json         # Esquemas Pydantic para validación
└── README.md               # Este archivo
```

## 🔧 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/scrypt-cv-ats.git
cd scrypt-cv-ats

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
# O alternativamente:
pip install -e .
```

### Modo Mock (funciona sin API key) ✅
El proyecto incluye un **cliente LLM simulado** (`mock_llm.py`) que funciona sin ninguna API key. Perfecto para:
- Probar el pipeline completo de extracción y estructuración
- Generar DOCX y HTML desde un PDF
- Desarrollo y pruebas locales

### Modo IA con OpenCode Zen (GRATIS) 🆓
El proyecto se conecta a **OpenCode Zen**, que ofrece modelos de IA gratuitos con API OpenAI-compatible:
- **Endpoint**: `https://opencode.ai/zen/v1`
- **Modelos gratuitos**: `ling-3.0-flash-fin-free`, `space-bunny-free`, `mimo-v2.6-flash-free`, `nemotron-3.5-lightning-free`
- **Costo**: $0

```bash
# 1. Obtén tu API Key en https://opencode.ai/zen
# 2. Copia el archivo .env.example
cp .env.example .env
# 3. Edita .env con tu OPENCODE_API_KEY

# 4. Ejecuta con mejora IA
python ats_converter.py -i curriculum.pdf -j "Jefe de Operaciones" \
    --industry "Minería" --enhance -f both

# O especifica el modelo
python ats_converter.py -i curriculum.pdf -j "Analista" \
    --provider opencode --model space-bunny-free --enhance -f both
```

## 🎯 Uso

### Pipeline Básico (Sin API — Modo Mock) ✅
```bash
python ats_converter.py -i curriculum.pdf -o curriculum_ats.docx
```

### Pipeline Completo con Mejora IA (OpenCode Zen - GRATIS)
```bash
python ats_converter.py -i curriculum.pdf -j "Jefe de Operaciones" \
    --industry "Minería" --tone minero-industrial --enhance -f both

# Especificar proveedor y modelo
python ats_converter.py -i curriculum.pdf -j "Analista" \
    --provider opencode --model space-bunny-free --enhance -f both
```

### Opciones Disponibles

| Argumento | Corto | Descripción |
|-----------|-------|-------------|
| `--input` | `-i` | Ruta al PDF de entrada (requerido) |
| `--output` | `-o` | Ruta de salida .docx |
| `--format` | `-f` | `docx`, `html`, o `both` |
| `--enhance` | `-e` | Activar mejora con IA |
| `--job-target` | `-j` | Título del puesto objetivo |
| `--industry` | | Industria (Minería, Construcción, etc.) |
| `--seniority` | | Entry, Junior, Mid, Senior, Lead, Manager |
| `--tone` | | profesional, ejecutivo, técnico, creativo, minero-industrial |
| `--keywords` | | Palabras clave extra (separadas por coma) |
| `--provider` | | `mock` o `opencode` (default: opencode) |
| `--model` | | Modelo OpenCode (default: ling-3.0-flash-fin-free) |
| `--threshold` | `-t` | Umbral X para separar columnas del PDF |
| `--verbose` | `-v` | Logging detallado |

## 🧪 Ejemplos

```bash
# Pipeline básico — solo estructurar PDF a DOCX (funciona sin API)
python ats_converter.py -i curriculum.pdf -o mi_cv.docx

# Pipeline completo con mejora IA para Minería
python ats_converter.py -i curriculum.pdf \
    -j "Supervisor de Operaciones Mineras" \
    --industry "Minería" --seniority "Senior" \
    --tone minero-industrial --enhance -f both

# Exportar solo HTML con mejora para Analista de Datos
python ats_converter.py -i curriculum.pdf \
    -j "Analista de Datos" --industry "Tecnología" \
    --tone tecnico --enhance -f html
```

## 🔮 Próximos Pasos (Roadmap)

- [ ] Interfaz Web con Flask/FastAPI
- [ ] Soporte multilenguaje (inglés, portugués)
- [ ] Análisis de compatibilidad ATS (puntuación 0-100)
- [ ] Modo batch para múltiples CVs
- [ ] Integración con LinkedIn API
- [ ] Plugins para Chrome/Firefox

## 📋 Licencia

MIT License — Ver archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama con tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request
