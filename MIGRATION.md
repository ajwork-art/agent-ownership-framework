# Migration Guide: AOF v1 → v2

AOF v2 is **fully backward compatible**. Every valid v1 contract remains valid under v2,
and v2 adds **no required fields**. You can adopt v2 tooling immediately and opt into v2
contract fields whenever you are ready — there is no forced migration.

> **Scope reminder.** AOF validates contracts at **deployment time** and can generate
> policy *inputs* (for example an OPA/Rego stub). It does **not** enforce policy at
> runtime. Nothing in v2 changes that boundary.

---

## 1. Your v1 contracts stay valid

No action is required for existing contracts. When you validate a v1 contract with the v2
tooling, it passes and you get one informational notice:

```
✓ my-agent.yaml
    · schema_version not declared — assuming 1.0 (v1). All v2 fields are optional; this contract is valid.
```

This notice is **never an error** and never fails CI — even under `--strict`. The five
original examples in [`examples/`](examples/) remain v1 contracts precisely to demonstrate
this.

---

## 2. Migrate the tooling (recommended first step)

The validator is now an installable package that exposes a single `aof` command. The old
standalone scripts still work but print a deprecation notice.

```bash
# Python — from source today; `pip install aof-validate` once published
pip install ./tools

# Node.js — from source today; `npm install -g aof-validate` once published
npm install -g ./tools

aof --version
aof validate my-agent.yaml
```

| Old (deprecated) | New |
|------------------|-----|
| `python tools/validate-contract.py <file>` | `aof validate <file>` |
| `node tools/validate-contract.js <file>` | `aof validate <file>` |
| `python tools/aof check <file>` | `aof check <file>` |

The deprecated scripts continue to function for backward compatibility; migrate CI and
local workflows to `aof validate` at your convenience. `aof validate` also now accepts a
**directory** (searched recursively) or a **glob**, not just individual files.

---

## 3. Opt into v2 fields (optional)

### 3a. Declare `schema_version`

Add the optional top-level field to silence the informational notice and signal intent:

```yaml
apiVersion: aof/v1
kind: AgentOwnershipContract
schema_version: "2.0"     # optional, additive; absent means "1.0"
```

`schema_version` is independent of `apiVersion` and matches the pattern `^\d+\.\d+$`.

### 3b. Use lifecycle dates and enable lifecycle enforcement

v2 does not add new lifecycle fields — it puts the **existing** date fields to work.
`aof validate` now warns when any of these dates has passed:

- `governance.next_review`
- `lifecycle.retirement_date`
- `lifecycle.retirement.sunset_date`
- `lifecycle.retirement.planned_review_date`

```yaml
governance:
  review_cadence: quarterly
  last_reviewed: "2026-06-15"
  next_review: "2026-09-15"      # a past date → warning (fails under --strict)

lifecycle:
  status: active
  retirement:
    sunset_date: "2027-12-31"
    planned_review_date: "2027-06-30"
```

These are **warnings** by default. Turn them into CI-blocking failures with `--strict`:

```bash
aof validate --strict contracts   # non-zero exit if any contract is stale
```

See [`examples/retention-sweeper-agent.yaml`](examples/retention-sweeper-agent.yaml) for a
fully worked v2 contract with lifecycle dates and a complete four-role sign-off.

### 3c. Inventory and diff your fleet

```bash
aof scan contracts                 # which agents are unsigned, expired, or unowned?
aof diff old.yaml new.yaml --require-reapproval   # gate material changes on re-sign-off
```

`aof diff` classifies a change as **material** if it touches `authority`, `data`,
`ownership.escalation_path`, or `signoff`. With `--require-reapproval`, a material change
whose `signoff` block is unchanged exits non-zero — a natural CI gate for "this needs a new
sign-off."

---

## 4. Adopt signing (optional)

Signing is **entirely optional**. AOF ships no PKI, never generates or stores private keys,
and does not require signatures to validate a contract. `aof verify` is a defense-in-depth
option that checks a **detached** signature produced out of band.

```bash
# The owner signs the contract file with their own key (AOF never sees the private key)
gpg --armor --detach-sign my-agent.yaml        # -> my-agent.yaml.asc

# A verifier imports the signer's PUBLIC key, then verifies
gpg --import signer-public-key.asc
aof verify my-agent.yaml                        # finds my-agent.yaml.asc automatically
```

`aof verify` exits `0` on a good signature and non-zero otherwise. A Sigstore/cosign
(keyless) recipe is documented in [docs/INTEGRATION.md](docs/INTEGRATION.md). Key
distribution and trust remain the operator's responsibility.

---

## 5. Generate artifacts (optional)

From any validated contract:

```bash
aof export --format markdown my-agent.yaml -o ownership-card.md   # wiki/runbook card
aof export --format opa       my-agent.yaml -o policy.rego        # Rego policy STUB
aof export --format a2a-card  my-agent.yaml -o agent-card.json    # experimental
```

- The **OPA/Rego** output is a stub full of `TODO` markers. AOF generates policy *inputs*;
  a runtime policy layer that you own must complete, test, and enforce it.
- The **A2A Agent Card** output is an **experimental draft mapping**, not a publish-ready
  A2A document. Fill in `url`, `capabilities`, and `securitySchemes`, validate it against
  the [A2A schema](https://a2a-protocol.org/latest/specification/), and review it before
  serving it at `/.well-known/agent-card.json`.

---

## Migration checklist

- [ ] Install the `aof` command; point CI at `aof validate`.
- [ ] (Optional) Add `schema_version: "2.0"` to contracts you actively maintain.
- [ ] (Optional) Populate `next_review` / retirement dates and adopt `aof validate --strict`.
- [ ] (Optional) Run `aof scan` across your contract directory to find unsigned/expired/unowned agents.
- [ ] (Optional) Adopt detached signatures and `aof verify` where you want approval provenance.

Nothing here is required to keep an existing v1 contract valid.
