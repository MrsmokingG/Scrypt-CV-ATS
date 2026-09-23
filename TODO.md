# TODO: Scrypt CV ATS - Modernización y Escalabilidad

## Fase 1: Análisis y Estructura
- [x] Leer todos los archivos del proyecto
- [x] Identificar problemas y oportunidades

## Fase 2: Modularización del Backend
- [x] Crear estructura de paquetes Python (app/)
- [x] Refactorizar `ats_converter.py` en módulos:
  - [x] `app/extractor.py` - Extracción de PDF (mejorado)
  - [x] `app/models.py` - Modelos Pydantic (CVData + JobTarget)
  - [x] `app/enhancer.py` - Sistema de mejora con IA (NUEVO)
  - [x] `app/generator.py` - Generación DOCX + HTML ATS (mejorado)
  - [x] `app/__init__.py` - Inicialización del paquete

## Fase 3: Sistema de Mejora con IA (Enhancer)
- [x] Implementar prompts para enriquecer descripciones laborales
- [x] Implementar generación de perfil profesional orientado al puesto
- [x] Implementar optimización de palabras clave ATS
- [x] Implementar inyección de logros cuantificables (método STAR)

## Fase 4: Mejora del index.html (Referencia ATS)
- [x] Agregar meta tags (viewport, description, Open Graph)
- [x] Mejorar semántica HTML5 (main, section, article)
- [x] Agregar microdatos JSON-LD para schema.org/Person
- [x] Mejorar accesibilidad (aria-labels, roles, skip-link)
- [x] Optimizar para mobile responsive (768px, 480px)
- [x] Mejorar focus-visible y prefers-reduced-motion
- [x] Mantener diseño original intacto (solo mejoras añadidas)

## Fase 5: CLI Mejorado
- [x] Actualizar `ats_converter.py` con argumentos:
  - `--job-target` / `-j` : Puesto objetivo para personalización
  - `--tone` : Tono (profesional, ejecutivo, técnico, creativo, minero-industrial)
  - `--enhance` : Flag para activar mejora con IA
  - `--format` : Formato de salida (docx, html, both)
  - `--industry` : Industria objetivo
  - `--seniority` : Nivel de seniority
  - `--keywords` : Palabras clave adicionales

## Fase 6: Documentación
- [x] Crear README.md completo con instrucciones y ejemplos
- [x] Crear .env.example para configuración
- [x] Actualizar TODO.md con progreso

## Fase 7: Instalación
- [x] Crear entorno virtual (venv)
- [x] Dependencias listas en requirements.txt
- [ ] Ejecutar `pip install -r requirements.txt` (pendiente de confirmación)

## Próximos pasos (post-MVP)
- [ ] Interfaz Web con Flask/FastAPI
- [ ] Soporte multidioma (EN, PT)
- [ ] Análisis de compatibilidad ATS (%)

