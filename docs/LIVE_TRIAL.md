# First Qwen live trial

Ukko completed ten real thought cycles on October 5, 2026, using the installed Ollama model `qwen3.8:latest`. It developed inquiries, replied to two natural human messages, and continued after a completed-cycle restart. This establishes a working local loop and persistence baseline. The main weaknesses were speculative claims about its internal processing and growing conversational latency.

## Configuration and records

The host was an Apple M2 Max with 32 GB unified memory. Ollama reported a 27.3B Q4_K_M checkpoint; its exact digest is in the [results](../experiments/results/qwen_live_trial_20261005.json). Generation used an 8192-token context, thinking disabled and a 500-token thought limit. `nomic-embed-text` provided 768-dimensional embeddings. Both models remained resident.

The [reusable configuration](../config/ukko.qwen.ollama.json) starts or continues the default subject. This trial uses its own runtime, identified by `runtime/latest-trial.json`. Its [manifest](../runtime/trials/qwen-20261005-153133/baseline/manifest.json), [journal](../runtime/trials/qwen-20261005-153133/baseline/journal.jsonl), [database](../runtime/trials/qwen-20261005-153133/baseline/mind.db), [restart checks](../runtime/trials/qwen-20261005-153133/baseline/restart_check.json) and [final state](../runtime/trials/qwen-20261005-153133/baseline/state.json) were frozen before interactive continuation. Runtime files are ignored by Git.

## Measured results

| Measure | Result |
| --- | --- |
| Completed cycles | 9 before the restart, 1 after |
| Recorded selection and thought calls | 20, all accepted on the first attempt by the lenient JSON parser |
| Recorded selection fallbacks after the fix | 0 |
| Generation time per cycle | 38.4–111.1 seconds; median 83.2 seconds |
| Highest-ranked candidate chosen | 9 of 10 choices |
| New inquiries | 6 interest outputs and 2 goals; 11 active interests including the 3 initial seeds |
| Human interaction | 2 incoming messages, 2 replies; both events eventually attended |
| Long-term memories | 14 embedded records: 10 generated hypotheses, 2 human observations, 2 speech observations |
| Retrieval | 13 memories had been accessed; all stored vectors were 768 floats |
| Database integrity | SQLite quick check passed |
| Restart | All 10 checkpoint fields, memory IDs and candidate status/visit records preserved |

Generation time combines attention selection and thought generation. It excludes embedding requests, prompt assembly and waits between cycles, so it is smaller than some message response times. JSON acceptance can include repairs; strict validity, truncation and schema completeness were not separately measured.

The first startup failed before completing any cycle: four embedding requests received HTTP 400 because `keep_alive="-1"` was sent as a duration string. Serializing it as the JSON number `-1` fixed residency requests. HTTP errors now retain the server's diagnostic body. Those startup errors remain in the raw journal. The ten completed cycles had no recorded generation errors. Partial failed cycles do not have complete attention receipts.

## Observed behavior

The first inquiry distinguished an unchanged world from an absence of observations. Ukko then generated questions about attention selection, processing latency and its own descriptions. Following a human message expressing care, its thoughts shifted toward relational explanations. When challenged about its wording, it revised the explanation. These are generated statements and conversational changes; the runtime did not measure an affect variable, entropy or a change in internal energy.

Most choices followed the scheduler ranking. After the restart, Ukko chose the pending human question in third place over two higher-ranked interests. This is one example of model arbitration within the shortlist, with no controlled comparison establishing its benefit or a causal effect of the restart.

The restart preserved context without a new synthetic prompt. This tests persistence at a completed-cycle boundary. It does not establish recovery from an arbitrary crash, independently tested delayed recall or prolonged behavioral continuity. No sleep cycle occurred, no inquiry was marked resolved, and web reading and file writing were disabled.

Whole-host swap usage was about 11.7 GB at one observation during the trial. There was no pre-trial snapshot, so that usage cannot be attributed to Ukko. The eventual M3 Ultra with 96 GB remains unbenchmarked.

## Next experiment

Expose measured generation latency and actual runtime capabilities as observations. Require proposed internal explanations to make a prediction, then compare that prediction with a later measurement. Attach evidence to memories and distinguish proposing an experiment from executing it. Improve event durability before a longer unattended run, and measure how prompt growth affects responsiveness.

The runtime suite now has 34 passing offline tests. A stopped-status fix ensures a recently completed run is displayed as stopped. The [summary utility](../experiments/live_trial_summary.py) reads existing records without starting another mind:

```sh
python3 -m experiments.live_trial_summary runtime/trials/qwen-20261005-153133/baseline --output runtime/trials/qwen-20261005-153133/baseline-summary.json
```

## Interactive continuation

After freezing the ten-cycle baseline, the same subject resumed for a bounded one-hour session because the human was still interacting in the observer. Those later events are outside the results above. The observer remains at [localhost:8765](http://localhost:8765). The time limit is checked between complete cycles, so the final cycle can extend beyond one hour.

To stop or resume this subject, use its preserved configuration:

```sh
python3 -m anima --config runtime/trials/qwen-20261005-153133/config.json control stop
python3 -m anima --config runtime/trials/qwen-20261005-153133/config.json run --max-seconds 3600
```

Run only one mind for this runtime at a time. Continuing it preserves its memories and pending interests.
