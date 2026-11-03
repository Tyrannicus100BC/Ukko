# Ukko

Ukko is an experiment in persistent, self-directed cognition on a local model. It starts from Anima and adds explicit attention competition: events and unanswered interests compete for consideration, neglect raises priority, and the model chooses its next topic. Human messages can receive a reply or silence.

The target is Qwen3.8-27B on an M3 Ultra with 96 GB unified memory. The initial implementation keeps Anima's small Python package and browser interface. The experiment concerns behavioral continuity, attention and learning over time; generated descriptions of inner experience are observations to study.

## Design and review

- [Architecture](docs/UKKO_ARCHITECTURE.md) describes the implemented loop and the proposed memory, inference, tools and Discord design.
- [Project review](docs/PROJECT_REVIEW.md) records the Anima findings and the Aura mechanisms worth investigating.
- [Experiment plan](docs/EXPERIMENTS.md) defines comparisons and deployment milestones.
- [Original Anima README](docs/ANIMA_UPSTREAM_README.md) and [design paper](docs/ANIMA_PAPER.md) preserve the starting project documentation.

## What runs now

With `experimental_attention` enabled, each cycle ingests percepts, ranks persistent candidates, asks the model to choose one, retrieves memories for that topic, and generates a thought and optional actions. It can add and resolve interests and request a consolidation sleep cycle. An invalid selection has a recorded controller fallback; failed thought generation leaves the candidate pending.

SQLite stores the attention candidates and decisions, memories with source and epistemic labels, and every subsequent self-model version. A checkpoint restores focus, working context and fatigue. The JSONL journal and existing web UI expose activity. Web reading and writing notes use Anima's existing capability settings.

Discord text, Discord voice/video, direct activation steering, executable tool creation and architecture changes are planned. The current HTTP adapter generates text through a local MLX-compatible server; it does not alter activations.

## Local baseline

Python 3.9+ is enough for the agent and offline checks. The inference server is a separate process.

For a small Ollama baseline, install the models explicitly:

```sh
ollama pull gemma:2b
ollama pull nomic-embed-text
python3 -m anima --config config/ukko.ollama.json run --max-ticks 10
```

Once the bounded run looks healthy, omit `--max-ticks` for continuous operation. The example configurations keep the wait between completed generations at 1–5 seconds. Actual cycle time also includes attention selection, retrieval and thought generation. Ollama uses `keep_alive=-1` to request residency. Sleep performs memory work using the resident model.

Use the same configuration for every interface:

```sh
python3 -m anima --config config/ukko.ollama.json ui
python3 -m anima --config config/ukko.ollama.json talk --thoughts
python3 -m anima --config config/ukko.ollama.json attention
python3 -m anima --config config/ukko.ollama.json status
python3 -m anima --config config/ukko.ollama.json control stop
```

The UI opens at `http://localhost:8765`. Under Settings, change the human name and grant web reading or a workspace for notes if desired. The existing browser camera route uses an Ollama vision model; the MLX text adapter does not extend that route.

## Qwen on Apple Silicon

For the installed Ollama model, use `config/ukko.qwen.ollama.json`. The first live trial used `qwen3.8:latest` (27.3B, Q4_K_M), `nomic-embed-text`, an 8192-token context and thinking disabled on the 32 GB development Mac:

```sh
python3 -m anima --config config/ukko.qwen.ollama.json run --max-ticks 10
```

The trial has its own preserved runtime under `runtime/trials/`; `runtime/latest-trial.json` identifies its configuration. Use that configuration for the UI and any restart to continue the same subject. The reusable configuration above starts or continues the default `runtime/` subject.

In an isolated Python environment with MLX LM installed, a text baseline can use:

```sh
mlx_lm.server --model mlx-community/Qwen3.8-27B-4bit --host 127.0.0.1 --port 8080
```

Keep Ollama running with `nomic-embed-text` installed for the separate embedding lane, then run:

```sh
python3 -m anima --config config/ukko.mlx.json run --max-ticks 10
```

The [MLX server documentation](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/SERVER.md) defines the API. The [4-bit model card](https://huggingface.co/mlx-community/Qwen3.8-27B-4bit) documents the converted checkpoint. The adapter sends `chat_template_kwargs.enable_thinking=false` for short JSON cycles; a recent server must support this field. HTTP JSON uses prompts and parsing, so measure parsing failures before longer runs. `context_tokens` controls Ollama only; the MLX deployment must configure its own cache and context limits.

The supplied configurations use the same default `runtime/` directory. Give each comparison a separate `ANIMA_RUNTIME_DIR` and `ANIMA_WATCH_DIR`. Keep one embedding model fixed within each runtime; changing its vectors requires reindexing. Run one mind process per runtime. `ANIMA_EXPERIMENTAL_ATTENTION=false` retains Anima's original reflex and contemplative loop for a comparison, while the memory correctness fixes apply to both modes.

## Verification

```sh
python3 -m unittest discover -s tests -v
python3 -m experiments.attention_probe --output experiments/results/attention_probe.json
```

The suite has 34 passing offline tests, including restart, discretionary replies, HTTP contracts, schema migration, forgetting consistency and stopped-run status. The scheduler probe uses synthetic stimuli and no model. With aging enabled, it visits 19 of 19 interests during 720 decisions; with aging disabled it visits 0. See [the result](experiments/results/attention_probe.json).

The first bounded Ollama trial is recorded in [the live trial report](docs/LIVE_TRIAL.md). Activation effects, prolonged behavior and performance on the 96 GB target remain unmeasured.

## Provenance

Anima was cloned into this folder at `ba215ce72bcaedd147d5d08de6e54555a62952c1`. Its MIT license and notices remain in [LICENSE](LICENSE). The Git remote still points to Anima; no remote changes have been published.

Aura was cloned only for review under the ignored `.references/aura/` directory at `f7fbfe4e17019fa28b0abca40dc9bd0001b853b0`. Its [license](https://github.com/youngbryan97/aura/blob/f7fbfe4e17019fa28b0abca40dc9bd0001b853b0/LICENSE) permits reading and learning but prohibits code reuse and derivative works. Ukko does not import or vendor Aura code. Activation-steering experiments will use an independent implementation of published methods.
