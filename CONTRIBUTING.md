# Contributing to the Agent Ownership Framework

Thank you for your interest in contributing. AOF is most valuable when it reflects the realities of production AI deployment — and that requires contributions from practitioners who have built and governed real agents.

---

## Types of Contributions

### 1. Examples

The most valuable contribution is a realistic, anonymized agent contract from a domain you know well.

**How to contribute an example:**

1. Copy `templates/contract-template.yaml` as a starting point
2. Name your file descriptively: `[domain]-[function]-agent.yaml`
3. Place it directly in `examples/` (flat structure, no subdirectories)
4. Validate it: `python tools/validate-contract.py examples/your-agent.yaml`
5. Add a row to the table in `examples/README.md`
6. Submit a pull request

**What makes a good example:**

- **Realistic, not hypothetical** — Based on a pattern you have actually seen in production
- **Fully filled out** — Every required field has a real value; no `TODO` placeholders
- **Anonymized** — No real company names, internal system names, or identifying details
- **Shows the hard decisions** — Escalation paths when owners are unavailable, blast radius in plain language, retirement criteria
- **Explains the reasoning** — YAML comments at key fields explaining why you made each choice
- **Includes the uncomfortable fields** — `risk.blast_radius`, `lifecycle.retirement_date`, `authority.scope_limits` should be specific and honest

**What we reject:**

- Examples with generic placeholder text ("Your company name here")
- Examples that skip optional-but-important fields like `accountability.runbook_url`
- Examples where `risk.blast_radius` is vague ("could affect some users")
- Examples that don't pass schema validation

### 2. Tools

Validation tools, integrations with CI/CD systems, contract generators, and registry implementations.

**How to contribute a tool:**

1. Place your tool in `tools/`
2. Include a docstring or JSDoc explaining what it does and how to run it
3. Add usage instructions to `tools/README.md`
4. Include example input and expected output in comments
5. Test on both passing and failing contracts

**Tool quality bar:**

- Must handle missing files gracefully (not crash)
- Exit code 0 on success, 1 on failure
- Clear, human-readable error messages
- Python tools target 3.8+, Node.js tools target 18+

### 3. Documentation

Improvements to framework docs, schema references, integration guides, and compliance mappings.

**How to contribute documentation:**

- Edit the relevant file in `docs/`
- Keep prose direct and concrete — every concept should have an example
- Avoid abstract governance language that does not translate to action
- For compliance mappings, show exactly which schema fields satisfy which regulatory requirements

### 4. Compliance Mappings

The `docs/COMPLIANCE.md` file maps AOF fields to regulatory frameworks. If you work in a regulated industry and know which schema fields satisfy which specific requirements, your contribution is valuable.

---

## Process: Fork, Branch, Commit, PR

```bash
# 1. Fork the repository on GitHub, then:
git clone https://github.com/ajwork-art/agent-ownership-framework.git
cd agent-ownership-framework

# 2. Create a branch
git checkout -b feat/add-healthcare-triage-example

# 3. Make your changes and validate
python tools/validate-contract.py examples/healthcare-triage-agent.yaml

# 4. Commit with conventional commits
git commit -m "feat(examples): add healthcare patient triage agent example"

# 5. Push and open a PR
git push origin feat/add-healthcare-triage-example
```

**Conventional commit types:**

| Type | When to use |
|------|-------------|
| `feat` | New example, new tool, new doc |
| `fix` | Fix validation error, fix broken link |
| `docs` | Documentation improvement |
| `chore` | Dependency updates, CI/CD changes |
| `refactor` | Restructuring without behavior change |

---

## PR Description Format

```markdown
## What This PR Does
Brief description of the contribution and its value.

## Type of Change
- [ ] New example
- [ ] Tool addition or improvement
- [ ] Documentation update
- [ ] Compliance mapping
- [ ] Schema change (requires discussion — open an issue first)

## Validation
- [ ] All examples in `examples/` pass validation
- [ ] New example added to `examples/README.md`
- [ ] Tool tested on both passing and failing contracts
- [ ] No placeholder text remains in example files
```

---

## Code of Conduct

Be respectful, professional, and constructive. Disagreements about framework design are welcome; personal criticism is not. This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

---

## Development Setup

```bash
# Python validator
cd tools
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python validate-contract.py ../examples/support-agent.yaml

# Node.js validator
cd tools
npm install
node validate-contract.js ../examples/support-agent.yaml

# Validate all examples at once
python tools/validate-contract.py examples/*.yaml
```

---

## Recognition

All contributors are credited in:

- The GitHub contributors list
- PR merge commit messages

If your contribution meaningfully improves the framework, the maintainer may feature it in the Enterprise Data AI Realities newsletter with credit.

---

## Questions Before You Start

Open an issue to discuss direction before investing time. Especially for:

- New top-level schema sections (these require discussion)
- New compliance mappings (we want to ensure accuracy)
- Major documentation restructuring

We respond to issues within a few business days.

---

*Built by [Anitha Jagadeesh](https://enterprisedataairealities.substack.com/) — Enterprise Data AI Realities on Substack.*
