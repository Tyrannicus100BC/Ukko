# Anima and Aura review for Ukko

Anima is the better codebase for the first Ukko experiment because its complete recurrent loop is small enough to understand and vary. Aura supplies useful mechanisms to investigate, especially activation steering and explicit inference ownership. Ukko should build those mechanisms independently and test their contributions one at a time.

The review covers Anima's runtime, cognition, sensors, capabilities, memory, sleep and tests, and selected Aura inference, attention, steering, evaluation and voice modules. It is a source review, not a successful deployment or a reproduction of either project's behavioral claims.

## Revisions and reuse

| Project | Reviewed revision | Role |
| --- | --- | --- |
| [Anima](https://github.com/huodebing-alt/anima/tree/ba215ce72bcaedd147d5d08de6e54555a62952c1) | `ba215ce72bcaedd147d5d08de6e54555a62952c1` | Cloned into the project root as the starting codebase |
| [Aura](https://github.com/youngbryan97/aura/tree/f7fbfe4e17019fa28b0abca40dc9bd0001b853b0) | `f7fbfe4e17019fa28b0abca40dc9bd0001b853b0` | Local reference checkout for review |

Anima's [MIT license](https://github.com/huodebing-alt/anima/blob/ba215ce72bcaedd147d5d08de6e54555a62952c1/LICENSE) permits modification with its notices retained. Aura's [license](https://github.com/youngbryan97/aura/blob/f7fbfe4e17019fa28b0abca40dc9bd0001b853b0/LICENSE) permits viewing and learning but explicitly prohibits use in another project and derivative works. The Aura checkout is ignored by Ukko's Git repository. No Aura modules are imported or copied into Ukko.

## Anima strengths

The [mind loop](https://github.com/huodebing-alt/anima/blob/ba215ce72bcaedd147d5d08de6e54555a62952c1/anima/agent.py) already performs unattended cycles and switches into consolidation sleep. A compact state machine makes causality inspectable: percepts enter a situation, a model emits a structured continuation, and actions feed later experience. Its configurable timescales are useful for experiments.

The [memory store](https://github.com/huodebing-alt/anima/blob/ba215ce72bcaedd147d5d08de6e54555a62952c1/anima/store.py) provides persistent memories, source links, reinforcement, archive and purge behavior in SQLite. The [sleep module](https://github.com/huodebing-alt/anima/blob/ba215ce72bcaedd147d5d08de6e54555a62952c1/anima/sleep.py) separates consolidation, reflection, dreaming and self-model rewriting. That gives Ukko mechanisms it can switch off for matched comparisons. The original 17 deterministic memory tests pass on this machine.

The journal and browser UI are useful observation tools. Their simplicity matters: an experiment becomes hard to interpret when model output is repaired or replaced by several invisible layers. The original bounded web-reading and note-writing actions are enough for a first action–perception cycle.

## Anima gaps and initial changes

| Finding from source | Consequence for this experiment | Initial Ukko change |
| --- | --- | --- |
| Incoming human text invokes a dedicated reply generation, then suppresses speech in the contemplative result | Replying is not an attention decision | Experimental mode removes that reflex and allows optional speech |
| Attention is primarily a focus string; active goals are supplied as prompt context | Neglected questions do not have an explicit route back into competition | A persisted candidate pool, aging, cooldown and separate topic choice |
| Focus, working context, fatigue and most timing fields start fresh on process construction | A restart changes the active cognitive situation | A completed-cycle checkpoint restores these fields |
| Decay multiplies current strength by a factor based on the entire time since recall on every sleep | More sleep passes cause more forgetting for identical elapsed time | A decay watermark makes passes incremental |
| The self-model table keeps only the current text and a version counter | Earlier identity revisions cannot be inspected | A history table retains subsequent revisions |
| Generated statements and dream-derived insights can enter retrieval without explicit evidence status | Repeated speculation can look like knowledge | Epistemic labels and exclusion of labeled fiction from ordinary recall |
| Similarity deduplication compares memories within a kind without preserving distinct provenance | Independent claims can collapse into one record | Deduplication also requires matching source and epistemic class |

The [cognition contract](https://github.com/huodebing-alt/anima/blob/ba215ce72bcaedd147d5d08de6e54555a62952c1/anima/cognition.py) is also oriented toward a companion learning about one named human. Ukko's experimental contract centers on inquiries and choices, with a human as an interlocutor. The three initial inquiries are documented starting conditions, not discovered interests.

Remaining gaps matter before a soak. Inbox files are removed during polling, embedding calls block the mind, and journal writes are separate from memory writes. A message or side effect can cross a crash boundary without durable acknowledgement. Memory retrieval scans all stored vectors, the event backlog can grow, and construction of a prompt reinforces the retrieved memories whether the thought uses them or not. These are priorities for a durable event layer and exposure/use distinction.

Anima's dreaming is symbolic recombination. It does not train model weights, and memory consolidation does not create learned neural parameters. Claims about improved behavior require testing downstream recall, reasoning or action at equal compute. The biological analogy suggests experiments; it does not validate their results.

## Aura mechanisms worth investigating

### Activation steering

Aura's [affective steering module](https://github.com/youngbryan97/aura/blob/f7fbfe4e17019fa28b0abca40dc9bd0001b853b0/core/consciousness/affective_steering.py) contains actual MLX forward-pass hooks that add direction vectors to hidden states. It combines state-dependent directions, targets model layers, masks generation positions and scales the intervention relative to a residual-stream norm. This is a computation change rather than merely a textual instruction about mood.

The implementation also reveals how many ways an intervention can disappear: incompatible vectors, detached hooks, neutral coefficients, stale state, quality clamps or a different serving lane. Preserve effective intervention telemetry. A setting that requests steering is not evidence that steering reached generation. The module contains historical comments about older alpha scales, so copying a documented constant would be especially unreliable.

Aura's [model-bound steering](https://github.com/youngbryan97/aura/blob/f7fbfe4e17019fa28b0abca40dc9bd0001b853b0/core/brain/llm/model_bound_steering.py) and qualification tools tie vector artifacts to a specific model descriptor. A historical migration artifact in the checkout marks steering deferred for that migration state; it does not establish the status of the author's current running system. Ukko should derive and evaluate vectors for its own base Qwen checkpoint rather than assume that Aura's fused model geometry transfers.

The published [CAA method](https://arxiv.org/abs/2312.06681) provides the independent starting point. The useful first study is whether a state-controlled intervention changes attention, exploration or conversational behavior while maintaining utility, compared with both a rich prompt and a random vector control.

### Inference ownership on a Mac

The reviewed [runtime configuration](https://github.com/youngbryan97/aura/blob/f7fbfe4e17019fa28b0abca40dc9bd0001b853b0/core/config.py) and [MLX client](https://github.com/youngbryan97/aura/blob/f7fbfe4e17019fa28b0abca40dc9bd0001b853b0/core/brain/llm/mlx_client.py) support a fused Qwen3.8-27B primary lane, model-worker lifecycle, admission, interruption and other model lanes. This is relevant to Ukko's target, but Aura's fusion, hardware and surrounding control layers differ from base Qwen on an M3 Ultra.

Adopt the principle of one owner for a resident model and measured memory admission. Begin with one primary model and a separate embedding lane. Additional fallbacks can preserve availability, but they also make a successful response ambiguous. Ukko should keep model identity, retries, failure and intervention state with every generation, and mark a failure instead of silently substituting a successful-looking answer.

### Learning where attention pays off

The [attention policy](https://github.com/youngbryan97/aura/blob/f7fbfe4e17019fa28b0abca40dc9bd0001b853b0/core/cognition/attention_policy.py) adapts channel allocations using measured returns per unit of spending, smooths changes, and retains a floor so a channel cannot become permanently unavailable. Its docstring acknowledges several competing allocation mechanisms elsewhere in the project. The small [attention field](https://github.com/youngbryan97/aura/blob/f7fbfe4e17019fa28b0abca40dc9bd0001b853b0/core/workspace/attention_field.py) is only a slot mapping; its presence alone does not establish end-to-end attention behavior.

Ukko should first make one attention policy authoritative, then define useful returns through external observations. A model assigning high scores to its own thoughts is a circular reward signal. The candidate aging mechanism already creates a simple comparison point for learned allocation.

### Voice as a separate processing lane

Aura's [streaming transcription](https://github.com/youngbryan97/aura/blob/f7fbfe4e17019fa28b0abca40dc9bd0001b853b0/core/voice/duplex/streaming_asr.py) handles incremental audio, a distinct model lease and local ASR implementations. The architectural lesson is to preserve sensory progress while the main model works. Its host-specific performance numbers do not predict Ukko's latency. Discord transport, encryption, transcription, conversational interruption and speech output need their own measurements.

## Simplification for Ukko

Keep one recurrent loop, one persistent workspace, one attention policy, one primary inference owner and one trace of decisions. Add a subsystem when an experiment establishes its role. A large collection of modules with neuroscience names makes attribution harder unless each variable has observable causes and consequences.

Aura's integration, state steering and measurement discipline are useful ideas. Its broad architecture, learned latent recurrence experiments and consciousness metrics are separate research programs. Ukko's first study should ask whether it maintains and revisits its own inquiries, revises beliefs from new evidence, and changes future action through memory. Those questions can be tested without treating a self-report or an aggregate consciousness score as the outcome.
