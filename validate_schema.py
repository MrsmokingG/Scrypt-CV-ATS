import json
with open("api_schema.json", "r", encoding="utf-8") as f:
    d = json.load(f)
print("Valid JSON ✓")
print("Models:", list(d.keys()))

# Check no $ref remains
for name, schema in d.items():
    has_ref = "$ref" in json.dumps(schema)
    print(f"  {name}: $ref={has_ref}")

# Print size of each schema
for name, schema in d.items():
    s = json.dumps(schema)
    print(f"  {name}: {len(s)} chars")

