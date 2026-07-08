# Roadmap

> **Placeholder.** This roadmap is maintained by the project author and will be filled in
> with the planned direction. The section below only records concrete future-work items
> already referenced elsewhere in the repository, so that those cross-links resolve. It is
> not a commitment, timeline, or statement of adoption.

## Known future work (candidate items)

- **First-class multi-agent / orchestration modeling.** The current schema describes one
  agent per contract. Orchestrators are modeled today as a single agent that routes work,
  with coordinated agents declared under `dependencies.services` (type: `agent`) — see
  [`examples/orchestrator-agent.yaml`](examples/orchestrator-agent.yaml). A first-class way
  to express an orchestration graph and per-edge authority is future work.
- **`aof verify` beyond GPG.** GPG detached-signature verification ships today. Wrapping
  Sigstore/cosign keyless verification in the CLI (currently a documented recipe in
  [docs/INTEGRATION.md](docs/INTEGRATION.md)) is a candidate.
- **A2A Agent Card export maturity.** The `a2a-card` exporter is an experimental draft
  mapping. Aligning it fully with the published A2A schema and validating output against it
  is future work.

_Additional roadmap content to be supplied._
