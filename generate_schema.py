#!/usr/bin/env python3
"""
Genera archivo api_schema.json con esquemas autónomos (sin $ref)
listos para pegar en blackbox AI > response_format > json_schema > strict: true.

Usa pydantic.TypeAdapter para generar el schema a partir de dataclasses.
"""
import json
import sys
sys.path.insert(0, '.')
from app.models import CVData, JobTarget, EnhancedCVData
from pydantic import TypeAdapter


def resolve_schema(model):
    """Schema completamente autocontenido, sin $ref, con additionalProperties:false."""
    # TypeAdapter genera el json_schema a partir de cualquier tipo Pydantic-compatible
    ta = TypeAdapter(model)
    raw = ta.json_schema()
    
    defs = raw.get('$defs', {})

    def resolve(obj, depth=0):
        if depth > 20:
            return obj
        if isinstance(obj, dict):
            if '$ref' in obj:
                key = obj['$ref'].split('/')[-1]
                if key in defs:
                    return resolve(json.loads(json.dumps(defs[key])), depth + 1)
                return obj
            return {k: resolve(v, depth + 1) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve(item, depth + 1) for item in obj]
        return obj

    schema = resolve(raw)

    def add_strict(obj):
        if isinstance(obj, dict):
            if obj.get('type') == 'object':
                obj['additionalProperties'] = False
            for v in obj.values():
                add_strict(v)
        elif isinstance(obj, list):
            for item in obj:
                add_strict(item)
        return obj

    schema = add_strict(schema)

    def clean(obj):
        if isinstance(obj, dict):
            obj.pop('title', None)
            obj.pop('$defs', None)
            if '$ref' in obj:
                key = obj.pop('$ref').split('/')[-1]
                return {"type": "string", "description": f"Reference to {key}"}
            for v in obj.values():
                clean(v)
        elif isinstance(obj, list):
            for item in obj:
                clean(item)
        return obj

    schema = clean(schema)
    return schema


# Generate all schemas
schemas = {}
for name, model in [("CVData", CVData), ("JobTarget", JobTarget), ("EnhancedCVData", EnhancedCVData)]:
    schemas[name] = resolve_schema(model)

# Write to file
output_path = sys.argv[1] if len(sys.argv) > 1 else "api_schema.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(schemas, f, indent=2, ensure_ascii=False)

print("Schema saved to " + output_path)
print("Models: " + ', '.join(schemas.keys()))
