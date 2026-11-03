# Ukko development

Ukko is a local persistent-agent research project, based on the MIT-licensed Anima checkout. Read `README.md`, `docs/UKKO_ARCHITECTURE.md` and `docs/EXPERIMENTS.md` before extending the runtime.

- Preserve Anima attribution and license. `.references/aura/` is review material with a restrictive license; do not import, copy or vendor its code.
- Keep mechanisms separable and config-driven. State whether a component runs in the real loop, an offline fixture or a proposed design.
- Record generation failures, controller fallbacks and tool failures explicitly. Generated self-reports are data, not proof of a subjective state.
- Preserve runtime databases, event records and self-model histories. Use distinct temporary runtimes for tests; do not reset an existing experimental subject casually.
- One mind process owns each runtime. One worker should own the primary resident model. Do not launch large additional models without checking available memory and active workloads.
- Run `python3 -m unittest discover -s tests -v` after changes to the runtime or store. Regression tests should target state integrity, restart boundaries and causal behavior.
- The scheduler ablation is `python3 -m experiments.attention_probe`. Its results measure the deterministic controller only.
- Do not launch an indefinite agent or install a background service as a side effect of a code edit. Use bounded live checks and preserve logs.
- No remote changes have been published; the current Git remote is the original Anima repository.
