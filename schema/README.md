# Schema

AOF v1 schema definitions. The schema is the source of truth for what a valid agent ownership contract looks like.

---

## What's in v1/

```
schema/
└── v1/
    ├── agent-ownership-contract.schema.json   # JSON Schema draft-07 (used by validators and tooling)
    └── agent-ownership-contract.example.yaml  # Fully annotated example with comments on every field
```

The JSON Schema is the authoritative machine-readable definition. The example YAML demonstrates every field with realistic values and inline explanations.

---

## How to Reference the Schema

### In a YAML contract (IDE autocompletion)

Add this comment as the first line of your contract file:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/ajwork-art/agent-ownership-framework/main/schema/v1/agent-ownership-contract.schema.json
apiVersion: aof/v1
kind: AgentOwnershipContract
```

This enables inline validation, field autocompletion, and hover documentation in:
- VS Code (with the [YAML extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml))
- JetBrains IDEs (IntelliJ, PyCharm, etc.)
- Any editor with yaml-language-server support

### In Python

```python
import json
import yaml
import jsonschema

with open("schema/v1/agent-ownership-contract.schema.json") as f:
    schema = json.load(f)

with open("my-agent-contract.yaml") as f:
    contract = yaml.safe_load(f)

jsonschema.validate(instance=contract, schema=schema)
print("Contract is valid.")
```

### Using the AOF validator

```bash
# Python validator
python tools/validate-contract.py path/to/my-agent-contract.yaml

# Validate multiple files
python tools/validate-contract.py examples/*.yaml

# Node.js validator
node tools/validate-contract.js path/to/my-agent-contract.yaml
```

---

## IDE Setup

### VS Code

1. Install the [YAML extension by Red Hat](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
2. Add the `yaml-language-server` comment at the top of each contract file (see above)
3. Open any contract file — you will see inline validation and field completions

Optional: configure in `.vscode/settings.json` to apply schema to all files in `examples/`:

```json
{
  "yaml.schemas": {
    "./schema/v1/agent-ownership-contract.schema.json": [
      "examples/*.yaml",
      "templates/contract-template.yaml"
    ]
  }
}
```

### JetBrains IDEs

1. Go to Settings > Languages & Frameworks > Schemas and DTDs > JSON Schema Mappings
2. Add a new mapping pointing to `schema/v1/agent-ownership-contract.schema.json`
3. Set the file pattern to `examples/*.yaml`

---

## Validation

The schema uses **JSON Schema draft-07**, supported by:

| Language | Library |
|----------|---------|
| Python | `jsonschema >= 4.0` |
| Node.js | `ajv >= 8.0` |
| Go | `github.com/xeipuuv/gojsonschema` |
| Java | `com.networknt:json-schema-validator` |
| .NET | `JsonSchema.Net` |

---

## Versioning Policy

AOF schema versions follow the contract's `apiVersion` field:

| API Version | Schema Directory | Status |
|-------------|-----------------|--------|
| `aof/v1` | `schema/v1/` | Active |
| `aof/v2` | `schema/v2/` | Future |

**Breaking changes** (removed fields, changed types, new required fields) require a new schema directory and a new `apiVersion` value.

**Backward-compatible additions** (new optional fields) are made in-place within the current version. Existing contracts remain valid after such updates.

A contract's `apiVersion` field must always match the schema directory used to validate it. A contract written with `apiVersion: aof/v1` must be validated against `schema/v1/`.
