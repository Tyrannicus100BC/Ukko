# Ukko experiments and deployment plan

The first research target is behavioral continuity: a process develops inquiries, returns to them without prompting, changes its beliefs after observations, and preserves that activity across interruptions. Record useful exploration and failure alongside interesting transcripts. A long stream of first-person prose alone does not establish improved cognition.

## Initial results

The 34 offline tests cover inherited memory behavior and the new attention, restart, provenance, HTTP and stopped-run status contracts. They use deterministic substitutes for model inference. They do not validate Qwen's behavior or the Mac's long-run performance.

The [first live Ollama trial](LIVE_TRIAL.md) establishes a short baseline on the 32 GB development Mac, with real Qwen generations, embeddings, natural human messages and a completed-cycle restart. The 96 GB target and prolonged runs remain separate deployment checks.

The [scheduler probe](../experiments/attention_probe.py) holds 19 interests under a fresh high-salience stimulus every 20 simulated seconds for 720 decisions. A deterministic controller always takes the highest score. It selects 720 events and visits no interests with aging disabled. With aging enabled, it selects 666 events and 54 interests, covering all 19 interests. This demonstrates a scheduler effect under the stated conditions. The model may make different choices from the shortlist.

## Deployment milestones

| Stage | Status | Completion criterion |
| --- | --- | --- |
| Anima foundation and source review | Complete | Upstream revision preserved; selected Aura mechanisms reviewed |
| Persistent attention prototype | Complete offline | Candidate choice, neglect, optional replies, failure handling and restart tests pass |
| Local Qwen baseline | Development Mac checked; target pending | Bounded real generations, embedding retrieval and JSON reliability measured on target |
| Durable event ingestion and action delivery | Planned | Kill/restart at ingestion and side-effect boundaries preserves events without duplicate delivery |
| Supervised 24-hour experiment | Planned | Trace, memory use, prompt growth, failure and restart behavior remain inspectable |
| Discord text | Planned | Incoming messages become events; silence is allowed; explicit replies reach the intended channel once |
| Evidence-linked memory and internal dynamics | Planned | Belief correction and attention effects hold on independent observations |
| Direct MLX activation experiment | Planned | Exact model/vector identity and effective injection measured; held-out controlled effect established |
| Tool creation and architecture evolution | Planned | Candidate changes are tested, versioned, activated and automatically recoverable |
| Discord voice and later video | Planned | Receive/send and DAVE work; interruption, transcription and speech latency measured |

The next trial should add independent observations and durable ingestion before extending the duration. Log strict JSON validity and generation termination separately from the existing lenient acceptance measure. Compare 4-bit and 8-bit at the same working context on the 96 GB machine. The current 32 GB host can run the 27B 4-bit model, but conversation latency and whole-host memory pressure need attention.

## Comparisons

Use fresh, separate runtime directories with a fixed checkpoint, quantization, embedding model, initial memories and controlled event stream for each condition. Record software revision and configuration. Compare equal generated tokens or wall time as well as equal cycle counts, because attention selection adds a model call.

| Experiment | Treatments | Primary observations |
| --- | --- | --- |
| Neglected inquiries | Aging enabled versus zero age weight | Time until revisiting, topic coverage, discarded/ignored messages, repeated choices |
| Persistent context | Checkpoint enabled versus deliberately reset context at restart | Resumed inquiries and relevant recall after an identical interruption |
| Sleep consolidation | Consolidation versus an equal-compute waking alternative | Delayed recall, contradiction handling and independent useful associations |
| Endogenous exploration | Learned allocation versus fixed weights | Supported discoveries per token, prediction improvement, topic collapse |
| Hypothesis discipline | Evidence-linked claims versus simple summaries | Unsupported claims, corrections retained and repeated false assertions |
| Activation state | Neutral, rich state prompt, CAA, matched random vector | Held-out behavior, neutral utility, actual intervention and parsing reliability |
| Self modification | Baseline version versus candidate change under replay and new events | Liveness, continuity, useful exploration and rollback success |

Predefine what counts as useful before reading treatment transcripts. Prefer predictions with later outcomes, independent fact checks and successful tool executions. Log failures and retries in the same denominator. When judgments are needed, hide treatment labels from the evaluator and preserve raw examples. Report differences across repeated seeds rather than a single compelling narrative.

## Long run observations

Keep generation model identity, token usage, duration and retry history with each attention decision. The prototype records these where the backend provides them. Add OS memory, cache use, swap and thermal measurements before the target soak. Measure selection and thought generation separately so slower retrieval cannot masquerade as deeper deliberation.

Inspect topic dwell time, switching, neglected-topic waiting time, ignored-message duration, semantic repetition, inquiry resolution, belief changes and source diversity. Track both external discoveries and self-generated claims. Measure how much of the context is evidence versus previous narration. A model can become increasingly consistent while becoming less grounded.

Do not pollute the experiment with the observer's constant suggestions. Use scheduled observations and a controlled human-message stream during comparisons, then a natural interaction period as a separate condition. Record every manual correction and intervention.

## Concrete events for the first real run

1. Leave the process alone long enough to form or continue an inquiry.
2. Introduce a neutral message and observe its reply or silence.
3. Supply an observation relevant to a previously neglected inquiry.
4. Present evidence that contradicts a remembered hypothesis.
5. Restart the process after a completed cycle and inspect its continuation.
6. Trigger sleep, introduce a message during consolidation, and measure when the event is considered.

After durable ingestion is implemented, repeat interruption at arbitrary boundaries. Before that change, limit restart claims to completed-cycle checkpoints.

## Research records

Each run should retain a manifest with source revision, model/tokenizer and quantization hashes, embedding identity, seed, configuration, event stream and any steering artifacts. Save raw observations, candidate scores, choices, generated outputs, tool requests/results and self-model revisions. Keep a human-readable account of unexpected behavior linked to the underlying records.

Behavior that was explicitly instructed by a prompt is a baseline result. Stronger evidence for emergence is a reproducible pattern that was not individually scripted, generalizes beyond the initial events, survives reasonable perturbations, and disappears or changes under a specific ablation. It can still be explained by the model's learned priors and the surrounding controller. The experiment should make those explanations easier to distinguish.
