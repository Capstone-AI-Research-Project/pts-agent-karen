# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-04-29

### Added
- Initial public release.
- n8n ingestion workflows under `workflows/`:
  - **Create and Embed v2.0 Mitre Attack** — pulls the latest MITRE ATT&CK enterprise STIX bundle and embeds `attack-pattern` objects into the `MitreAttackNomic` Weaviate collection.
  - **Create and Embed v3.0 Behavior** — embeds the curated behavior patterns in `data/behavior.json` into the `MitreBehavior` Weaviate collection.
- n8n analysis agents under `workflows/`:
  - **Simple Log Analysis Agent Weaviate Behavior v2.14b** — Windows / Linux log analysis pipeline, 27 nodes.
  - **PCAP Simple Log Analysis Agent PCAP Weaviate Behavior v2.18** — PCAP analysis pipeline (consumes the JSON produced by the prep scripts), 27 nodes.
- PCAP preparation scripts under `scripts/`:
  - `cutfields.sh` — extracts IP-based packet fields from a `.pcap` to CSV using `tshark`.
  - `cleandata.py` — converts the CSV to structured JSON, normalizes protocol stacks, and flags anomalous nesting.
- Seed data:
  - `data/behavior.json` — 46 MITRE-mapped behavior patterns covering brute-force, credential access, lateral movement, command and control, exfiltration, ransomware impact, and persistence techniques.
- Documentation: `README.md`, `LICENSE` (MIT), this `CHANGELOG.md`, and the original install / configuration guide preserved in `docs/README.pdf`.

[Unreleased]: https://github.com/Capstone-AI-Research-Project/pts-agent-karen/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Capstone-AI-Research-Project/pts-agent-karen/releases/tag/v1.0.0
