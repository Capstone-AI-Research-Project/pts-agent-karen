# Agent Karen

> Behavior-based log and PCAP analysis agent for the Project Twilight Synapse platform.

## Project Overview

`pts-agent-karen` is a research agent that runs on top of the [Project-Twilight-Synapse](https://github.com/Capstone-AI-Research-Project/Project-Twilight-Synapse) cybersecurity AI platform. It uses [n8n](https://n8n.io/) for orchestration, [Weaviate](https://weaviate.io/) as a vector store, and [Ollama](https://ollama.com/) for local embedding (`nomic-embed-text`) and reasoning (`qwen2.5:7b`).

Karen ingests two reference knowledge bases, the official MITRE ATT&CK enterprise matrix and a curated set of behavior patterns, then uses semantic search against those collections to surface MITRE-mapped detections in either:

- Windows / Linux event logs, or
- Network packet captures (`.pcap` → CSV → JSON pipeline).

The agent's two analysis workflows enrich detections with MITRE technique context and have a local LLM draft a structured analyst-style report.

## Prerequisites

This repo is **not standalone**. You need the backend stack from Project-Twilight-Synapse running first.

1. **Project-Twilight-Synapse stack** up and running. Follow the [installation steps in that repo](https://github.com/Capstone-AI-Research-Project/Project-Twilight-Synapse#installation). Verify you can reach:
   - Open-WebUI at `http://localhost:3000`
   - n8n at `http://localhost:5678`
   - Weaviate at `http://localhost:8080` (from the host)
2. **Ollama models pulled** (easiest is via Open-WebUI → *Models*):
   - `nomic-embed-text:latest` — embedding model used by both ingestion workflows.
   - `qwen2.5:7b` — reasoning model used by both analysis agents.
3. **For PCAP analysis only**, on whichever host runs the prep step:
   - `tshark` and `editcap` (Wireshark CLI tools)
   - Python 3 (the prep script uses standard library only)

## Repository contents

```
pts-agent-karen/
├── workflows/                     # n8n workflows (import these into n8n)
│   ├── Create_and_Embed_v2_0_Mitre_Attack.json
│   ├── Create_and_Embed_v3_0_Behavior.json
│   ├── Simple_Log_Analysis_Agent_Weaviate_Behavior_v_2_14b.json
│   └── PCAP_Simple_Log_Analysis_Agent_PCAP_Weaviate_Behavior_v2_18.json
├── scripts/
│   ├── cutfields.sh               # tshark → CSV field extraction
│   └── cleandata.py               # CSV → JSON normalization
├── data/
│   └── behavior.json              # 46 MITRE-mapped behavior patterns
├── docs/
│   └── README.pdf                 # Original install / config guide
├── README.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/Capstone-AI-Research-Project/pts-agent-karen.git
cd pts-agent-karen
```

### 2. Place files where n8n can read them

The two ingestion workflows read from disk **inside the n8n container**. With the current Project-Twilight-Synapse compose file, the container has read access to both the backend's `output/` and `assets/` directories.

`data/behavior.json` is referenced by the v3.0 Behavior workflow at `/home/node/output/behavior.json`. Either:

- Copy it into the backend's `output/` directory:
  ```bash
  cp data/behavior.json /path/to/Project-Twilight-Synapse/output/behavior.json
  ```
- Or, if you prefer keeping reference data with `assets/`, copy it there and update the workflow's **Read/Write Files from Disk** node path to `/home/node/assets/behavior.json`.

`scripts/cutfields.sh` and `scripts/cleandata.py` run on your **host**, not inside a container. Keep them wherever convenient.

### 3. Import the workflows into n8n

In the n8n UI (`http://localhost:5678`):

1. Click **Create New Workflow**.
2. Click the **`...`** menu (right of "Publish" / "Version History") → **Import from File**.
3. Import each of the four files in `workflows/`. Repeat for all four.

### 4. Configure credentials

Each workflow that talks to Ollama or Weaviate needs n8n credentials wired in. You only need to do this once per credential, n8n reuses them across workflows.

**Ollama (Embeddings + Chat Model nodes):**

1. Open the node → create a new Ollama credential.
2. **Base URL:** `http://ollama:11434/`
3. Save. You should see *"Connection tested successfully"* at the top of the node.

**Weaviate (Vector Store nodes):**

The bundled credential reference is named `Weaviate Credentials account`. Either reuse the equivalent credential you already created in Project-Twilight-Synapse, or create a new one pointing at `http://weaviate:8080`.

### 5. Build the vector stores

Run these once to populate Weaviate. Both ingestion workflows are **destructive**, they `DELETE` the existing schema first, then recreate and embed.

1. Open **Create and Embed v2.0 Mitre Attack** → **Execute Workflow**. This pulls the latest STIX bundle from MITRE and embeds the `attack-pattern` objects into the `MitreAttackNomic` collection. Expect **~3 hours** on modest hardware.
2. Open **Create and Embed v3.0 Behavior** → confirm the **Read/Write Files from Disk** node's path matches where you actually placed `behavior.json` in step 2 → **Execute Workflow**. This embeds the 46 behavior patterns into the `MitreBehavior` collection. Expect **~30 minutes**.

> **Note:** The original guide in `docs/README.pdf` recommends deleting the trailing `Debug` node before running production ingestion. The `Create and Embed v3.0 Behavior` workflow shipped here still has it. Either remove the node in the n8n UI before executing, or leave it (harmless, just adds a small amount of time per batch).

### 6. Verify the schema

From your host:

```bash
curl http://localhost:8080/v1/schema | jq '.classes[].class'
```

You should see `"MitreAttackNomic"` and `"MitreBehavior"` listed (alongside anything else already present).

## Usage

Both analysis agents are exposed as **n8n form triggers**. Open the workflow in n8n and either click the form trigger node to grab its public URL, or use **Execute Workflow** to fire the form interactively.

### Log analysis (Windows / Linux)

1. Open **Simple Log Analysis Agent Weaviate Behavior v2.14b**.
2. Activate the workflow (toggle in the top right) so the form trigger goes live.
3. Submit a JSON log file via the form. The workflow will:
   - parse and chunk the logs,
   - extract event metadata,
   - query both Weaviate collections semantically,
   - run a detection engine over the matches,
   - have the local LLM (`qwen2.5:7b` via Ollama) draft a structured analyst report,
   - write the report to disk via the Read/Write Files node.

### PCAP analysis

PCAPs need to be flattened to JSON first. The prep pipeline:

```
.pcap → editcap (slice/trim) → tshark (cutfields.sh) → CSV → cleandata.py → .json
```

Step by step:

1. **Slice to a time window** (optional but recommended for large captures):
   ```bash
   editcap -A "YYYY-MM-DD HH:MM:SS" -B "YYYY-MM-DD HH:MM:SS" input.pcap sliced.pcap
   ```
2. **Cap packet count** (optional):
   ```bash
   editcap -c 50000 sliced.pcap trimmed.pcap
   ```
3. **Extract fields to CSV.** Edit `scripts/cutfields.sh` and replace `<filename>` with your input PCAP and the desired output CSV name, then:
   ```bash
   bash scripts/cutfields.sh
   ```
4. **Normalize to JSON.** Edit `INPUT_CSV` and `OUTPUT_JSON` at the top of `scripts/cleandata.py`, then:
   ```bash
   python3 scripts/cleandata.py
   ```
   The resulting JSON contains per-packet protocol stacks, transport / application layer detection, and a `protocol.anomaly` flag for unusually deep or duplicated chains.
5. **Submit the JSON** to the form trigger of **PCAP Simple Log Analysis Agent PCAP Weaviate Behavior v2.18**.

## Authors

| Name | GitHub Profile |
|------|----------------|
| Karen Langdon | [![GitHub](https://img.shields.io/badge/GitHub-cybersec--blonde-181717?style=for-the-badge&logo=github)](https://github.com/cybersec-blonde) |
| David Poehlman | [![GitHub](https://img.shields.io/badge/GitHub-davidpoehlman-181717?style=for-the-badge&logo=github)](https://github.com/davidpoehlman) |

## Related projects

- [Project-Twilight-Synapse](https://github.com/Capstone-AI-Research-Project/Project-Twilight-Synapse) — backend Docker / n8n / Weaviate / Ollama platform this agent depends on.
- [pts-casa (a.k.a. pts-agent-kyle)](https://github.com/ktalons/pts-casa) — sibling research agent under the same naming convention; multi-agent investigation system that maps findings across MITRE ATT&CK, MITRE CAR, NIST CSF 2.0, and CIS Controls v8.1.2.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
