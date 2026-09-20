# DISTILLED KNOWLEDGE & HISTORICAL TASK ANALYSIS

_Synthesized on 2026-09-20 18:22:39Z from 1537 archived task records._

## 1. Executive Summary & Recurrent Themes

### Domain: "done-by-code" means someone can re-run the proof. (1 tasks)
- **AGY-1783**: Give every T- task marked done-by-code a command that demonstrates it  (WS-PROCESS | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no entry claims done-by-code without either a demonstration command or an explicit statement that it is unproven.
  - *Why:* a task list where "done" is unverifiable is a list that reports progress it has not made, and every plan built on it inherits the error.

### Domain: A bad upgrade rolls itself back, observed rather than configured. (1 tasks)
- **AGY-1780**: Watch greenboot roll a deliberately broken AI plane back  (WS-RUNTIME | P1 | M) [from T-002]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: two recorded boots exist -- one rolled back, one not -- from the same check set.
  - *Why:* rollback is the property that makes immutable updates safe to take automatically; untested it is a hope, and every deployed machine is one bad upgrade from being unreachable.

### Domain: A capability the guest plane can express but can never serve reads as available and fails at the hardware boundary. (1 tasks)
- **AGY-2584**: Make hardware-facing capabilities unclaimable by a hosted image  (WS-MINI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `radio` and `router` are Blade-plane capabilities with their shapes enforced, and all three negatives fail for the right reason.
  - *Why:* The prohibition is cheaper to add before the units exist than to retrofit after an archetype has already been granted something it cannot serve.

### Domain: A check gives the same verdict regardless of the invoking user. (1 tasks)
- **AGY-1861**: Running the gate as root produces different results  (WS-HOSTDEP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the full gate gives identical results as root and as an unprivileged user.
  - *Why:* two of this session's red readings were harness artefacts, which is a measurement problem, not a code problem.

### Domain: A check that cannot run on a host says so instead of passing. (1 tasks)
- **AGY-1853**: Shebang resolution differs by host and is not stated  (WS-HOSTDEP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every tool-invoking check reports unavailability through the one helper.
  - *Why:* the tree is developed on Windows and gated on Linux, so this difference is permanent and needs to be stated.

### Domain: A component that ships is either wired or declared unwired. (1 tasks)
- **AGY-1926**: Shipped runtime components are unwired  (WS-RUNTIME | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every shipped component is wired or declared, and a newly-shipped unwired component fails.
  - *Why:* the image's size and attack surface are paid for whether or not the components are used.

### Domain: A declared security control is actually enabled. (1 tasks)
- **AGY-1877**: The memory-poisoning scan is disabled while the SSOT says it runs  (WS-SEC | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the scan runs in the mode the SSOT declares, and a disagreement fails a check.
  - *Why:* a security control that is declared and not running is worse than one that is honestly absent.

### Domain: A declared unit references SSOT keys rather than repeating their values. (1 tasks)
- **AGY-1840**: `[units.*]` values are literals where SSOT keys exist  (WS-UNITS | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no `[units.*]` value repeats a number that has an SSOT key.
  - *Why:* a literal inside the SSOT is still a hardcode, just relocated.

### Domain: A doc that cites a gate number cites a real one. (1 tasks)
- **AGY-1817**: Gate ordinals cited in prose are not verified to exist  (WS-GATE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a citation of a nonexistent ordinal fails the check.
  - *Why:* the roadmap's third campaign counts 150 stale references; ordinals are a category of them nothing currently catches.

### Domain: A failed boot returns to the previous image automatically. (1 tasks)
- **AGY-1925**: Greenboot is shipped but no failure is proven to roll back  (WS-RUNTIME | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: an image that fails its health check rolls back to the previous deployment unattended.
  - *Why:* rollback is the property that makes an immutable OS safe to update automatically.

### Domain: A failing test cleans up as reliably as a passing one. (1 tasks)
- **AGY-1862**: Temp fixtures are left behind by failing tests  (WS-HOSTDEP | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a suite that leaks a fixture only when failing is caught.
  - *Why:* a leaked fixture pollutes the next run, producing failures in unrelated checks.

### Domain: A file tracked in both repositories has one content, not two. (1 tasks)
- **AGY-1727**: Reconcile the 18 shared files that diverged, and promote them to mirrored  (WS-PROCESS | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `not_mirrored` holds only files that are per-repository BY DESIGN, each with its reason, and everything else mirrors.
  - *Why:* the bootstrap repository is what a new machine installs from; a shared file with two contents means the installed system disagrees with the image depending on which repo you read.

### Domain: A floating reference is resolved and recorded at build time. (1 tasks)
- **AGY-1933**: Image references carry latest intent with no staleness check  (WS-SBOM | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a floating reference with no recorded resolution fails the build.
  - *Why:* an unresolved floating reference means the image contains something nobody recorded.

### Domain: A generated census does not produce a 130-line diff for a 1-line change. (1 tasks)
- **AGY-1864**: Line-indexed artefacts churn whenever a line is added anywhere  (WS-HOSTDEP | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: moving code without changing it produces no corpus churn.
  - *Why:* review fatigue from mechanical churn is how real changes get waved through.

### Domain: A hot or nearly-flat handset drains its work instead of dying mid-task. (1 tasks)
- **AGY-2579**: Android battery and thermal watchdog with greenboot wanted.d work drain  (WS-NODE-ANDROID | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Crossing either threshold drains work and refuses new tasks; the check never blocks boot; thresholds resolve from the SSOT.
  - *Why:* The edge node runs on a battery inside a phone, where sustained inference is a thermal event and an unannounced death strands the execution DAG.

### Domain: A measurement that cannot distinguish the healthy case from the broken one is not a measurement. (1 tasks)
- **AGY-1730**: Make every counting gate count the thing it claims  (WS-GATES | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each counting gate is either measuring the property or replaced by one that does, with the audit recorded.
  - *Why:* this is the repository's most expensive recurring defect, and a count is its most common disguise.

### Domain: A missing ceiling fails loudly instead of disabling its ratchet. (1 tasks)
- **AGY-1822**: Ratchet ceilings are read from the SSOT but never asserted to exist  (WS-GATE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: deleting any ratchet ceiling from the SSOT fails a check that names the key.
  - *Why:* an absent ceiling is a broken gate that looks like a passing one.

### Domain: A missing mios.toml is a failure, not a skip. (1 tasks)
- **AGY-1811**: check_structured passes against a tree with no SSOT at all  (WS-GATE | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: an empty directory still skips, and a directory that has `usr/` but no `mios.toml` reports a violation.
  - *Why:* the same early-return shape is repeated across the folded checks, so fixing it once establishes the pattern for the rest.

### Domain: A missing port key fails instead of silently defaulting. (1 tasks)
- **AGY-1870**: `[ports]` fallbacks can mask a missing key  (WS-SSOT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a fallback whose key is not rendered fails, and a fallback that disagrees with its key fails.
  - *Why:* a fallback that silently disagrees with the SSOT is a hardcode with a plausible disguise.

### Domain: A negative test cannot corrupt the run that follows it. (1 tasks)
- **AGY-1819**: Prove the drift-gate negatives suite restores the tree it perturbs  (WS-GATE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each case self-verifies its own restore, and a deliberately broken restore fails that case rather than the next one.
  - *Why:* a corrupting test suite produces failures in unrelated checks, which is the hardest kind of red to diagnose.

### Domain: A new themed surface must derive from `[colors]`. (1 tasks)
- **AGY-1874**: Theme surfaces are projected but new surfaces are not required to be  (WS-SSOT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a colour literal in an unregistered surface fails.
  - *Why:* the projection is only complete if joining it is mandatory.

### Domain: A new unseeded SSOT section is caught. (1 tasks)
- **AGY-1771**: Make the DB seed gate measure coverage, and stop its test faking the proof  (WS-GATES | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: appending a new top-level table to the SSOT turns the gate red without touching the seeder.
  - *Why:* it is the sole guard on the SSOT-to-config path the operator-defined model rests on, and its negative test manufactures the evidence that it works.

### Domain: A reference to a retired port fails. (1 tasks)
- **AGY-1917**: 16 references to dead ports were found once and the class is not gated  (WS-AI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a reference to a retired port fails, naming the port and its replacement.
  - *Why:* the recorded fix was manual, so the same drift will recur.

### Domain: A registered test that never turns its gate red is still not coverage. (1 tasks)
- **AGY-1729**: Prove each of the nineteen re-registered negative tests actually breaches its gate  (WS-GATES | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every one of the nineteen is shown red under its own mutation and green after restoration.
  - *Why:* they were written as coverage and delivered none; running them is necessary but does not by itself make them effective.

### Domain: A relocated key is proven to still be read. (1 tasks)
- **AGY-1876**: `[code_mode]` and `[pgvector]` keys were moved to reachable tables without consumer tests  (WS-SSOT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every relocated key has a test asserting its consumer reads the current location.
  - *Why:* satisfying a structural check by moving a key is exactly the kind of edit that quietly disconnects a setting.

### Domain: A required greenboot check that detects a fault reports one. (1 tasks)
- **AGY-1763**: Make the required health checks capable of failing  (WS-DEPLOY | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each required check fails on the fault it names and passes only on a healthy system.
  - *Why:* the checks that gate a rollback currently pass over the exact conditions they were written to catch.

### Domain: A shipped command either works or the build stops. (1 tasks)
- **AGY-1784**: Fail the build on any verb whose backend is a stub  (WS-CI | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a newly introduced echo-only backend fails the build.
  - *Why:* a stub that reports success is indistinguishable from a working command to an operator and to every test, and this repository has shipped at least one in its install path.

### Domain: A signed kernel image is verified by firmware at boot. (1 tasks)
- **AGY-1931**: Signed boot artefacts are described but not verified end to end  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a machine with secure boot enabled boots the signed image and reports verification.
  - *Why:* an unverified boot chain makes every downstream integrity claim decorative.

### Domain: A skipped check is visible in the summary, not only in stderr. (1 tasks)
- **AGY-1818**: `_need_python` reports a warning CI cannot distinguish from a pass  (WS-GATE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a run with skips prints the skip count and the skipped check names.
  - *Why:* the recorded failure mode is a whole suite skipping and reading as green.

### Domain: A smoke test with nothing to check fails instead of passing. (1 tasks)
- **AGY-1826**: Bake-smoke prints OK for an empty list  (WS-GATE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: an empty input list fails the suite with a message naming its source.
  - *Why:* this suite is on the exempt list, so it currently reports nothing to anyone; making it honest is a precondition for un-exempting it.

### Domain: A subcommand in the module is invoked by the gate. (1 tasks)
- **AGY-1829**: Nothing asserts a drift-check subcommand is reachable from the shell gate  (WS-GATE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a subcommand mentioned only in a comment fails the assertion.
  - *Why:* the duplicate-logic hazard it prevents is one the tree already had.

### Domain: A suite runs in the tier it is declared in. (1 tasks)
- **AGY-1923**: The CI suite registry's tier assignment is not validated against runtime  (WS-CI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a suite that did not run in its declared tier fails.
  - *Why:* the registry is the single list both publishers run from, so its accuracy is the whole point.

### Domain: A suite that finds nothing must say so, not crash. (1 tasks)
- **AGY-1715**: Make tests/test-directory-dispatch.sh assert instead of indexing an empty result  (WS-CI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the suite runs in the `unit` tier and its failure message names the missing fixture.
  - *Why:* it was one of thirteen suites no workflow ran; the reason it could not be wired in was a crash, not a real assertion.

### Domain: A test file that no tier runs is a failure at the moment it is added. (1 tasks)
- **AGY-1824**: Suites that run nowhere cannot be detected after the fact  (WS-GATE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: adding a test file outside every glob fails until it is claimed or exempted.
  - *Why:* an unrun suite is worse than no suite: it reports coverage that does not exist.

### Domain: A tethered node is discoverable over the cable and over nothing else. (1 tasks)
- **AGY-2576**: Real mDNS responder bound to the tethered interface, replacing the placeholder discovery module  (WS-NODE-ANDROID | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The node resolves over the tether within seconds of attach, and the negative test fails if the responder ever answers elsewhere.
  - *Why:* Discovery is what turns a cable into a cluster, and the module currently claims capabilities its code does not have.

### Domain: A user unit is declared as a user unit. (1 tasks)
- **AGY-1845**: User units and system units share one table with no distinction  (WS-UNITS | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a user unit renders to the user unit directory and a system unit to the system one.
  - *Why:* a user unit installed as a system unit either fails to start or starts in the wrong session.

### Domain: A2A agent federation supports capability metadata routing and compact semantic-frame JSON payload negotiation. (1 tasks)
- **AGY-1943**: Identity-aware delegation and progressive payload mode negotiation on A2A  (WS-FED | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A2A negotiation selects semantic-frame format between capable peers and falls back gracefully to standard text on legacy endpoints.
  - *Why:* Compact typed payloads drastically lower token serialization overhead in high-frequency inter-agent delegation loops.

### Domain: AI-Plane/Refactor (1 tasks)
- **T-273**: DEBT-03 -- Split mios_dispatch.py + finish server.py decomposition (TD-5)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `mios_dispatch.py` is extracted and imported live with `check_unwired_modules` green; `server.py` is under the 800-line composition-root target; `grep -n 'except:$'` over `usr/lib/mios/agent-pipe/` returns nothing; and the new >800-line Python drift-check passes in `just drift-gate`.

### Domain: AI-plane/Inference/Deploy (1 tasks)
- **T-178**: HEAVY-01 -- provision the heavy dGPU model so the stated lanes d
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a fresh install on a detected dGPU brings the heavy lane up per the stated SSOT defaults with the model auto-fetched (no manual step, Condition gate satisfied); a plain-English query is answered on the GPU with agents/nodes/hermes routed by `lane_priority` and light-lane + Windows co-tenancy staying OOM-free; both the vLLM and SGLang lanes come up -- neither silently dropped.

### Domain: AI/AQLMKernel (1 tasks)
- **T-952**: AQLM 2-bit multi-codebook vector engine and fused CUDA dequant kernel in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes AQLM 2-bit multi-codebook vector kernels on GPU Tensor Cores at <18.5GB VRAM.

### Domain: AI/AQLMTest (2 tasks)
- **T-871**: Automated 70B AQLM VRAM fitting (<16GB), lookup speed, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-16GB VRAM residency, fast codebook lookup throughput, and low perplexity degradation.
- **T-953**: Automated 2-bit AQLM 18.2GB VRAM fitting, 3.6x speedup, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-18.5GB residency, fast codebook lookup, and high perplexity retention.

### Domain: AI/AQLMVector (1 tasks)
- **T-870**: AQLM additive vector quantization engine and multi-codebook CUDA lookup kernel in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes AQLM multi-codebook vector lookups via fused CUDA kernels.

### Domain: AI/ASTDiff (1 tasks)
- **T-780**: Tree-Sitter AST structural diff engine and 2-peer review gate in agent-pipe
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Agent pipeline parses Tree-Sitter ASTs and enforces 2-peer review gating on structural diffs.

### Domain: AI/ASTDiffTest (1 tasks)
- **T-781**: Automated AST structural diff calculation and 2-peer review merge gating test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates AST diff precision, cosmetic change filtering, and 2-peer review consensus gating.

### Domain: AI/AWQInference (1 tasks)
- **T-844**: Activation-Aware Weight Quantization (AWQ) engine and fused W4A16 dispatcher in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine loads AWQ models and executes fused W4A16 Tensor Core kernels with >3.5x speedup.

### Domain: AI/AWQTest (1 tasks)
- **T-845**: Automated 3.5x AWQ matrix speedup, salient channel protection, and coding benchmark test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >3.5x matrix acceleration, salient channel preservation, and high coding accuracy.

### Domain: AI/Allocation (1 tasks)
- **T-481**: Dynamic Node Capability Profiler & Model Format Selector in agent-pipe
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Model allocation engine selects optimal quantization formats dynamically based on live node telemetry.

### Domain: AI/AsymQuantGEMM (1 tasks)
- **T-868**: Fused asymmetric scale and zero-point register execution engine in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes fused asymmetric scale and zero-point register math with >3.6x speedup.

### Domain: AI/AsymQuantTest (1 tasks)
- **T-869**: Automated 3.6x asymmetric GEMM speedup, register fusion, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >3.5x matrix acceleration, register-level fusion, and superior asymmetric perplexity.

### Domain: AI/BiAttention (1 tasks)
- **T-904**: Bi-Attention 1-bit Query-Key binarization engine and Hamming dot-product kernel in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes Bi-Attention 1-bit QK Hamming dot-products at >5x speedup.

### Domain: AI/BiAttnTest (1 tasks)
- **T-905**: Automated 5x attention speedup, 16x memory reduction, and 1M context needle test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >5x attention acceleration, 16x memory savings, and perfect needle retrieval.

### Domain: AI/BiLLMA1W1 (1 tasks)
- **T-924**: BiLLM A1W1 pure bitwise XNOR-POPCOUNT matrix engine in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes BiLLM A1W1 via pure bitwise XNOR-POPCOUNT kernels at >400 tok/s on CPU.

### Domain: AI/BiLLMA1W1Test (1 tasks)
- **T-925**: Automated 400 tok/s CPU throughput, multiplier elimination, and RAM fitting test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >400 tok/s CPU decoding speed, zero arithmetic multiplications, and low perplexity degradation.

### Domain: AI/BiLLMBinary (1 tasks)
- **T-864**: BiLLM 1-bit weight binarization engine and residual error compensation kernel in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine loads BiLLM 1-bit models and executes dual-popcount SIMD kernels on CPU.

### Domain: AI/BiLLMTest (1 tasks)
- **T-865**: Automated 70B BiLLM RAM fitting (<11GB), 250 tok/s CPU throughput, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates strict sub-11GB RAM fitting, >250 tok/s CPU throughput, and low perplexity degradation.

### Domain: AI/BiLoRA (1 tasks)
- **T-944**: Bi-LoRA binary low-rank adapter engine and sign-scaled integer dispatcher in mios-finetune-bilora
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Training and inference runtime fine-tunes and executes Bi-LoRA binary adapters at >3.6x speedup.

### Domain: AI/BiLoRATest (1 tasks)
- **T-945**: Automated 8x adapter RAM reduction, 3.6x speedup, and fine-tuning accuracy test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates 8x memory compression, rapid integer forward passes, and high adaptation fidelity.

### Domain: AI/BinaryEmbed (1 tasks)
- **T-894**: 1-bit binary embedding quantizer and hardware Hamming distance matcher in mios-embed-binary
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Embedding engine quantizes vectors to 1-bit and performs million-scale Hamming lookups in <100ms.

### Domain: AI/BinaryEmbedTest (1 tasks)
- **T-895**: Automated 32x embedding RAM reduction, 10M comparison/sec, and MRR test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates 32x memory compression, hardware POPCOUNT speed, and high semantic retrieval accuracy.

### Domain: AI/BitNetA8W1 (1 tasks)
- **T-908**: BitNet A8W1 fused sign-accumulation matrix engine in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes BitNet A8W1 via fused sign-accumulation integer kernels at >350 tok/s on CPU.

### Domain: AI/BitNetA8W1Test (1 tasks)
- **T-909**: Automated 350 tok/s CPU throughput, multiplier elimination, and RAM fitting test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >350 tok/s CPU decoding speed, zero float multiplications, and low perplexity degradation.

### Domain: AI/BitNetTernary (1 tasks)
- **T-804**: BitNet b1.58 ternary tensor execution engine and pure integer addition GEMM kernels
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine loads BitNet b1.58 models and executes pure integer addition kernels on CPU.

### Domain: AI/BitNetTest (1 tasks)
- **T-805**: Automated 70B BitNet RAM fitting (<14GB), 200 tok/s CPU speedup, and energy benchmark suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates strict RAM fitting bounds, >200 tok/s CPU throughput, and 10x energy efficiency.

### Domain: AI/CDIReload (1 tasks)
- **T-496**: Zero-downtime CDI re-generation and inference engine live reload daemon
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: CDI specifications update and inference engines recognize hotplugged GPUs with zero session downtime.

### Domain: AI/CPUGEMM (1 tasks)
- **T-784**: Hardware-calibrated CPU vectorized GEMM auto-tuner in mios-cpu-gemm
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: CPU inference engine auto-tunes SIMD vector kernels and executes cache-tiled matrix dot products.

### Domain: AI/CPUGEMMTest (1 tasks)
- **T-785**: Automated CPU quantized GEMM throughput (>30 tok/s) and SIMD dispatch test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates high-throughput SIMD vector dispatch, cache tiling efficiency, and architecture compatibility.

### Domain: AI/CPUVNNI (1 tasks)
- **T-830**: Fused VNNI vectorized dot-product kernel engine and L1 cache blocker in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes fused VNNI dot-product kernels with L1 cache blocking on CPU.

### Domain: AI/ChunkedPrefill (1 tasks)
- **T-888**: Interleaved chunked prefill scheduler and iteration-level batcher in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine schedules chunked prefills alongside active decode streams with <5ms jitter.

### Domain: AI/ChunkedTest (1 tasks)
- **T-889**: Automated chunked prefill streaming jitter (<5ms) and concurrent throughput test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-5ms streaming jitter, iteration batching correctness, and high GPU saturation.

### Domain: AI/DBQKernel (1 tasks)
- **T-960**: DBQ double-binarized dual-POPCOUNT matrix engine in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes DBQ dual-POPCOUNT matrix operations at >350 tok/s on CPU.

### Domain: AI/DBQTest (1 tasks)
- **T-961**: Automated 350 tok/s CPU throughput, dual-binary POPCOUNT, and RAM fitting test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >350 tok/s CPU decoding speed, minimal multiplier use, and low perplexity loss.

### Domain: AI/EAGLE2Spec (1 tasks)
- **T-896**: EAGLE-2 feature-level speculative head and dynamic draft tree verifier in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes EAGLE-2 feature-level speculative decoding at >2.5x speedup.

### Domain: AI/EAGLE2Test (1 tasks)
- **T-897**: Automated 2.5x EAGLE-2 speedup, dynamic draft tree acceptance, and token parity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >2.5x speedup, high draft acceptance rates, and exact output parity.

### Domain: AI/EXL2Engine (1 tasks)
- **T-792**: Dynamic EXL2 fractional bitrate execution engine and fused CUDA kernel manager in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine loads EXL2 models and executes fused CUDA kernels at >100 tok/s.

### Domain: AI/EXL2Test (1 tasks)
- **T-793**: Automated 70B EXL2 model VRAM fitting (<24GB), 100 tok/s speedup, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates strict VRAM fitting bounds, >100 tok/s token throughput, and low perplexity delta.

### Domain: AI/Eval (1 tasks)
- **T-488**: Automated LoRA adapter benchmark evaluator and catastrophic forgetting guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Benchmark evaluator gates adapter deployment on regression-free evaluation passes.

### Domain: AI/FP6KVCache (1 tasks)
- **T-808**: Dynamic FP6 (E3M2) KV-cache quantizer and bit-packed CUDA kernel manager in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine quantizes KV caches dynamically to bit-packed FP6 with fused CUDA kernels.

### Domain: AI/FP6Test (1 tasks)
- **T-809**: Automated 62.5% KV memory savings, FP6 reasoning accuracy (>99.8%), and packing benchmark suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates 62.5% memory reduction, high reasoning fidelity, and bit-packing alignment.

### Domain: AI/FineTune (1 tasks)
- **T-487**: Unprivileged containerized QLoRA fine-tuning engine using Unsloth
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: QLoRA fine-tuning engine trains domain adapters cleanly inside unprivileged containers.

### Domain: AI/FlashAttn3 (1 tasks)
- **T-848**: FlashAttention-3 warp-specialized kernel engine and FP8 TMA overlapping in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes FlashAttention-3 with warp specialization and TMA hardware acceleration.

### Domain: AI/FlashAttn3Test (1 tasks)
- **T-849**: Automated 1,200 TFLOPS attention benchmark, sub-10ms 128k TTFT, and TMA test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >1,200 TFLOPS throughput, sub-10ms 128k prompt prefill, and TMA memory overlapping.

### Domain: AI/GPTQMarlin (1 tasks)
- **T-874**: GPTQ-Marlin 2D tiled layout converter and fused Tensor Core GEMM dispatcher in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine loads GPTQ-Marlin models and executes fused 2D tiled Tensor Core kernels at >3.8x speedup.

### Domain: AI/Grammar (1 tasks)
- **T-984**: Put the GBNF compiler on the dispatch hot path or retire it
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Either a dispatch test proves a compiled grammar reaches the lane request, or the module is gone and the decision is recorded in the workstream.

### Domain: AI/HQQQuantizer (1 tasks)
- **T-824**: Calibration-free HQQ quantization compiler and fused dequantization GEMM manager
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: HQQ toolchain quantizes models in <30s and inference engine executes fused dequantization kernels.

### Domain: AI/HQQTest (1 tasks)
- **T-825**: Automated sub-30s HQQ model quantization, perplexity parity, and fused GEMM test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates instant calibration-free quantization speed, low perplexity degradation, and fast GEMM execution.

### Domain: AI/HybridQuant (1 tasks)
- **T-866**: Automated mixed-bit layer slicing compiler and sensitivity profiler in mios-quantize-hybrid
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Hybrid quantization compiler produces mixed-bit models with 68% compression and <0.02 perplexity loss.

### Domain: AI/HybridTest (1 tasks)
- **T-867**: Automated 68% size reduction, mixed-bit execution, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >65% compression, low perplexity degradation, and seamless mixed-bit execution.

### Domain: AI/KVOffload (1 tasks)
- **T-886**: Tiered PagedAttention KV-cache offloader (VRAM/RAM/NVMe via io_uring) in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine offloads and prefetches tiered KV blocks across VRAM, RAM, and NVMe seamlessly.

### Domain: AI/KVOffloadTest (1 tasks)
- **T-887**: Automated 1M token context offloading, sub-2ms swap latency, and zero-crash test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates massive context support, asynchronous NVMe swapping, and 100% retrieval accuracy.

### Domain: AI/KVRecycleTest (1 tasks)
- **T-837**: Automated multi-agent session handoff latency (<1ms) and VRAM recycling test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond session handoffs, zero memory churn, and stable VRAM residency.

### Domain: AI/KVRecycling (1 tasks)
- **T-836**: Warm KV-cache ring pooler and dynamic session recycling manager in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine maintains warm KV pool and recycles session memory across agent handoffs in <1ms.

### Domain: AI/LookaheadNgram (1 tasks)
- **T-876**: Lookahead N-gram prompt-lookup speculative decoding engine in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes Lookahead n-gram speculative decoding at >1.8x speedup on code/JSON.

### Domain: AI/LookaheadTest (1 tasks)
- **T-877**: Automated 1.8x code/JSON generation speedup, zero-VRAM overhead, and token parity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >1.8x speedup on structured tokens, zero memory overhead, and exact output parity.

### Domain: AI/MXFP8Engine (1 tasks)
- **T-948**: OCP MXFP8 microscaled tensor core engine and block exponent scaler in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference and training engine executes OCP MXFP8 microscaled Tensor Core kernels at >2.8x speedup.

### Domain: AI/MXFP8Test (1 tasks)
- **T-949**: Automated 2.8x MXFP8 speedup, dynamic range overflow prevention, and loss test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >2.75x matrix acceleration, automatic dynamic range scaling, and high training convergence.

### Domain: AI/MarlinTest (1 tasks)
- **T-875**: Automated 3.8x Marlin throughput speedup, memory bandwidth, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >3.5x matrix acceleration, >90% memory bus saturation, and low perplexity degradation.

### Domain: AI/MedusaSpec (1 tasks)
- **T-856**: Medusa multi-head self-speculative decoding engine and tree attention verifier in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes Medusa self-speculative decoding with tree attention at >2.0x speedup.

### Domain: AI/MedusaTest (1 tasks)
- **T-857**: Automated 2.2x self-speculative speedup, tree attention, and token parity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >2x speedup, tree attention verification correctness, and exact output parity.

### Domain: AI/NVFP4Pipeline (1 tasks)
- **T-914**: NVFP4 / MXFP4 block-scaled (E2M1 + E8M0) tensor core pipeline in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes NVFP4/MXFP4 block-scaled Tensor Core kernels at >4.5x speedup.

### Domain: AI/NVFP4Tensor (1 tasks)
- **T-838**: Native NVFP4 / MXFP4 Tensor Core execution engine and block-32 scale unpacker in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes native NVFP4 Tensor Core instructions with block-32 microscaling.

### Domain: AI/NVFP4Test (2 tasks)
- **T-839**: Automated 4x matrix throughput speedup, 70B NVFP4 VRAM fitting, and accuracy test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >3.8x matrix acceleration, sub-18GB VRAM residency, and high mathematical reasoning accuracy.
- **T-915**: Automated 4.5x FP4 speedup, 18.5GB VRAM fitting, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-18.5GB residency, 4.5x acceleration, and low perplexity degradation.

### Domain: AI/OCRMask (1 tasks)
- **T-540**: Lightweight on-device OCR regex credential masking pipeline for vision frames
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: OCR masking pipeline detects and redacts credential text patterns from vision frames locally.

### Domain: AI/OmniQuant (1 tasks)
- **T-892**: OmniQuant learnable clipping and equivalent transformation optimizer in mios-quantize-omniquant
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: OmniQuant optimizer compiles 3-bit models in <15min and inference engine executes fused Tensor Core kernels.

### Domain: AI/OmniTest (1 tasks)
- **T-893**: Automated 15-minute OmniQuant optimization, 3.6x speedup, and 3-bit perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates rapid learnable optimization, high GPU speedup, and low 3-bit perplexity degradation.

### Domain: AI/Partition (1 tasks)
- **T-537**: Multi-node dynamic AI workload partitioner and capability-aware task router
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Mesh distributor partitions and routes subtasks across relevant cluster nodes dynamically.

### Domain: AI/PipelinedSpec (1 tasks)
- **T-940**: Asynchronous staged speculative pipelining engine and lockless queue in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes asynchronous staged speculative pipelining across compute devices at >3.2x speedup.

### Domain: AI/PipelinedTest (1 tasks)
- **T-941**: Automated 3.2x pipelined speculative speedup, queue throughput, and token parity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >3.2x generation acceleration, microsecond queue streaming, and exact token parity.

### Domain: AI/PrefixCache (1 tasks)
- **T-796**: Radix Tree prefix KV-cache sharing engine in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine shares KV blocks via Radix Tree and delivers sub-5ms TTFT on shared prefixes.

### Domain: AI/PrefixTest (1 tasks)
- **T-797**: Automated shared prompt prefix hit rate (>95%) and sub-5ms TTFT benchmark suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates high Radix Tree cache hit rates, sub-5ms TTFT acceleration, and token parity.

### Domain: AI/QLoRAEngine (1 tasks)
- **T-918**: NF4 Double-Quantized base and fused LoRA residual adapter dispatcher in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference and training engine executes NF4 double-quantized models with fused LoRA adapters in <24GB VRAM.

### Domain: AI/QLoRATest (1 tasks)
- **T-919**: Automated 70B QLoRA 24GB VRAM fine-tuning, latency (<1ms), and convergence test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-24GB residency, rapid adapter execution, and exact training convergence parity.

### Domain: AI/QServeEngine (1 tasks)
- **T-860**: QServe W4A8KV4 mixed-precision execution engine and fused INT8 dispatcher in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes QServe W4A8KV4 via fused INT8 Tensor Core kernels with >3.0x speedup.

### Domain: AI/QServeTest (1 tasks)
- **T-861**: Automated 3.2x QServe speedup, 70B VRAM fitting (<22GB), and accuracy test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >3x matrix acceleration, sub-22GB VRAM fitting, and high mathematical reasoning accuracy.

### Domain: AI/QuIPSharp (1 tasks)
- **T-880**: QuIP# randomized Fast Hadamard Transform engine and E8 lattice dispatcher in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine loads QuIP# 2-bit models and executes fused FHT-GEMM kernels on Tensor Cores.

### Domain: AI/QuIPTest (1 tasks)
- **T-881**: Automated 70B QuIP# VRAM fitting (<18GB), FHT-GEMM speedup, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-18GB VRAM residency, fast FHT-GEMM execution, and low perplexity degradation.

### Domain: AI/ReDistribute (1 tasks)
- **T-538**: Automated node failure detection and zero-loss dynamic task re-distribution engine
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Task failover engine detects node drops and completes in-flight AI tasks across surviving nodes.

### Domain: AI/STT (1 tasks)
- **T-533**: Low-latency WebRTC streaming audio ingress and streaming Whisper speech-to-text bridge
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Streaming STT engine transcribes microphone audio in real time with sub-150ms token latency.

### Domain: AI/SVDLLMFactor (1 tasks)
- **T-810**: SVD-LLM low-rank matrix factorization engine and residual adapter dispatcher
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine loads SVD-factored models and executes fused low-rank residual projections.

### Domain: AI/SVDQuantCore (1 tasks)
- **T-884**: SVDQuant fused 4-bit and rank-16 low-rank core execution engine in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes SVDQuant fused W4A4 + Low-Rank GEMM kernels on GPU Tensor Cores.

### Domain: AI/SVDQuantTest (1 tasks)
- **T-885**: Automated 3.4x SVDQuant speedup, outlier absorption, and accuracy test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >3.2x matrix acceleration, outlier error absorption, and high mathematical reasoning accuracy.

### Domain: AI/SVDTest (1 tasks)
- **T-811**: Automated 70% memory bandwidth reduction, outlier preservation, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates 70% bandwidth reduction, outlier preservation, and low perplexity degradation.

### Domain: AI/SearchLocale (1 tasks)
- **T-999**: SEARCH-01 -- the anchor stopword screen is English-only while the tokenizer it screens is deliberately multilingual
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the screen resolves per-locale through the layered SSOT; default English behaviour is byte-identical to today for English corpora (proved by a before/after token-set diff on the same input); a non-English corpus either gets its own screen or is documented as deliberately unscreened; and the sibling test covers at least one non-Latin case.

### Domain: AI/SelfSpecTest (1 tasks)
- **T-957**: Automated 1.9x self-speculative speedup, 0MB VRAM overhead, and token parity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >1.9x generation acceleration, zero memory overhead, and exact token parity.

### Domain: AI/SelfSpeculation (1 tasks)
- **T-956**: Kangaroo draftless self-speculative early-exit engine in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes Kangaroo draftless self-speculative early-exit decoding at >1.9x speedup.

### Domain: AI/ShadowTest (1 tasks)
- **T-541**: Shadow dual-process candidate daemon validator and query mirroring harness
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Shadow testing harness validates candidate daemon patches in isolated namespaces safely.

### Domain: AI/SmoothQuant (1 tasks)
- **T-832**: SmoothQuant W8A8 activation-weight smoothing engine and fused INT8 Tensor Core dispatcher
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes SmoothQuant W8A8 via fused INT8 Tensor Core kernels with <0.02 perplexity loss.

### Domain: AI/SmoothQuantTest (1 tasks)
- **T-833**: Automated 2.0x INT8 Tensor Core speedup, outlier activation smoothing, and test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >1.9x INT8 matrix speedup, low perplexity degradation, and zero numerical exceptions.

### Domain: AI/SocketHandoff (1 tasks)
- **T-542**: Zero-downtime systemd socket handoff (sd_listen_fds) daemon swapper for agent-pipe
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Socket swapper transitions active daemon instances with zero client connection drops.

### Domain: AI/SpQRKernel (1 tasks)
- **T-936**: SpQR outlier isolation compiler and fused sparse-dense CUDA engine in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes SpQR fused sparse-dense CUDA kernels on GPU Tensor Cores at >3.5x speedup.

### Domain: AI/SpQRTest (1 tasks)
- **T-937**: Automated 3.5x SpQR speedup, <0.5% outlier density, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >3.4x matrix acceleration, minimal outlier overhead, and near-zero perplexity loss.

### Domain: AI/SparseGPT (1 tasks)
- **T-932**: SparseGPT 2:4 structural sparsity compiler and fused mma.sp Tensor Core engine
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Compiler prunes models to 2:4 sparsity and inference engine executes fused mma.sp sparse Tensor Core kernels.

### Domain: AI/SparseTensorCores (1 tasks)
- **T-812**: 2:4 hardware structural sparsity engine and Sparse Tensor Core dispatcher in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes 2:4 structural sparsity via Sparse Tensor Cores at >1.8x speedup.

### Domain: AI/SparseTest (2 tasks)
- **T-813**: Automated 2x Sparse Tensor Core throughput speedup and 2:4 pruning accuracy benchmark suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >1.8x matrix acceleration, Sparse Tensor Core execution, and high coding accuracy.
- **T-933**: Automated 2.0x sparse speedup, 2:4 structural validation, and accuracy test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >1.95x matrix acceleration, exact 2:4 structural patterns, and high coding accuracy.

### Domain: AI/SpecDraftTest (1 tasks)
- **T-819**: Automated speculative decoding speedup (>2.0x) and target output parity benchmark suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >2x throughput acceleration, rejection sampling correctness, and exact output parity.

### Domain: AI/SpecInferTest (1 tasks)
- **T-923**: Automated 2.8x SpecInfer speedup, tree-attention mask validity, and token parity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >2.8x generation speedup, exact tree attention causal masking, and 100% token distribution fidelity.

### Domain: AI/SpecInferTree (1 tasks)
- **T-922**: SpecInfer dynamic multi-draft tree engine and 2D tree-attention mask verifier in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine verifies dynamic candidate token trees concurrently via 2D tree-attention masks at >2.8x speedup.

### Domain: AI/SpeculativeDraft (1 tasks)
- **T-818**: Draft-model speculative decoding and parallel target verification engine in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes draft-model speculative decoding and achieves >2.0x speedup.

### Domain: AI/TTS (1 tasks)
- **T-534**: Concurrent streaming Piper/Kokoro TTS audio synthesis and PipeWire buffer feeder
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Concurrent TTS engine streams synthesized voice audio concurrently with token generation.

### Domain: AI/TernaryCompiler (1 tasks)
- **T-814**: Automated TriLM / BitNet ternary quantization compiler and bitpacker in mios-quantize-ternary
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Ternary compiler quantizes FP16 models to bitpacked ternary containers in under 2 minutes.

### Domain: AI/TernarySIMD (1 tasks)
- **T-900**: Parallel bit-manipulating ternary unpacker and fused SIMD accumulator in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes parallel bit-manipulation ternary unpacking and fused SIMD accumulation at >300 tok/s.

### Domain: AI/TernarySIMDTest (1 tasks)
- **T-901**: Automated 300 tok/s ternary unpacking throughput, zero-allocation, and SIMD test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates >300 tok/s CPU throughput, zero auxiliary memory allocations, and hardware bit-manipulation execution.

### Domain: AI/TernaryTest (1 tasks)
- **T-815**: Automated ternary compilation speed, MSE reconstruction parity (<0.02), and bitpack test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates high-speed ternary model compilation, mathematical MSE parity, and bitpacking fidelity.

### Domain: AI/TriLMKernel (1 tasks)
- **T-928**: TriLM fused 1.58-bit ternary GPU kernel and warp-specialized accumulator in llama-swap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Inference engine executes TriLM fused 1.58-bit ternary CUDA kernels on GPU Tensor Cores at >3.8x speedup.

### Domain: AI/TriLMTest (1 tasks)
- **T-929**: Automated 3.8x GPU ternary speedup, 14GB VRAM fitting, and perplexity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-14GB residency, fast warp-specialized execution, and low perplexity degradation.

### Domain: AI/VNNITest (1 tasks)
- **T-831**: Automated CPU K-Quant VNNI throughput (>35 tok/s) and cache-blocked benchmark suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates high VNNI token decoding throughput, L1 cache locality, and multicore scaling.

### Domain: AI/VisionRedact (1 tasks)
- **T-539**: ATSPI accessibility tree sensitive widget coordinate detector and Wayland frame blur filter
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Vision redaction filter blurs all ATSPI-reported password fields on captured screen frames.

### Domain: AI/WebSocket (1 tasks)
- **T-518**: Authenticated WebSocket real-time agent execution token stream (/v1/events/ws)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: WebSocket endpoint streams real-time execution events with sub-50ms latency.

### Domain: AI/Webhooks (1 tasks)
- **T-517**: HMAC-SHA256 authenticated webhook receiver and idempotent agent_inbox queue in agent-pipe
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Webhook receiver validates cryptographic signatures and queues events idempotently.

### Domain: Absorb outlier activations into rank-16 FP16 core and execute fused W4A4 + Low-Rank GEMM for >3.4x speedup. (1 tasks)
- **AGY-2482**: SVDQuant fused 4-bit and rank-16 low-rank core execution engine in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes SVDQuant fused W4A4 + Low-Rank GEMM kernels on GPU Tensor Cores.
  - *Why:* SVDQuant absorbs challenging activation outliers into low-rank channels, enabling high-speed 4-bit computation without accuracy loss.

### Domain: Accelerate primary LLM generation speed using small 1B/3B draft models in speculative decoding pipelines. (1 tasks)
- **AGY-1959**: Speculative decoding multi-model lane configuration with quantized draft models  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Speculative decoding runs stably with measurable throughput improvements across standard benchmarks.
  - *Why:* Speculative decoding significantly reduces time-to-first-token and tokens-per-second on local GPU hardware.

### Domain: Accounts/Identity/DB (1 tasks)
- **T-246**: VECTOR-04 -- V4 Accounts/users: DB-owned ids + prefs + bidirecti
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A new account gets its uid from the DB sequence, its dotfiles render from `account_preference` with no `etc/skel` copy, a change made on the OS side flows back into the DB on both platforms, and `just drift-gate` plus `test_mios_*` pass.

### Domain: Active long-running agent tasks can be gracefully suspended and resumed across turn boundaries using KV slot checkpoints. (1 tasks)
- **AGY-1938**: Compose turn-boundary preemption and context snapshot-suspend-resume  (WS-SCHED | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Background tasks suspend upon high-priority arrival and resume from their saved KV slot without losing prior conversation state.
  - *Why:* True preemptive scheduling is a foundational requirement of an agentic operating system to maintain low interactive latency under heavy autonomous load.

### Domain: Agents/A2A (2 tasks)
- **T-158**: MAO-05 -- Identity-aware delegation: extend agent-passport/A2A (
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Delegation demonstrably routes on attested, measured quality so a self-inflating delegate is not preferred, and a subtask's model tier is chosen from the delegate's `reasoning_profile`/`cost_hint` while sessions stop re-transmitting full history per call.
- **T-159**: MAO-06 -- Progressive payload / token-efficiency modes  [P3]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Two MiOS agents negotiate semantic-frame mode, fall back to text against a peer that lacks it, log the measured token reduction, and show no quality regression versus text on a delegation benchmark.

### Domain: Agents/Coordination (1 tasks)
- **T-156**: MAO-03 -- Document-mutation + LISTEN/NOTIFY coordination lane on
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: An agent row-mutation wakes a decoupled subscriber via NOTIFY with no polling loop involved and the whole exchange replays from DB rows alone; with the bus down or disabled, dispatch falls back to direct calls.

### Domain: Agents/Council (1 tasks)
- **T-155**: MAO-02 -- Structured deliberation for consequential tasks (DCI c
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A model classifier (not a keyword list) selects deliberation vs the cheap path with default off and routine tasks never paying the 62x cost, and a deliberation run writes a Decision Packet whose minority report survives instead of being averaged away.

### Domain: Agents/Memory (1 tasks)
- **T-157**: MAO-04 -- Manifest-guided progressive-disclosure retrieval  [P3]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A longitudinal-tree query retrieves via manifest LLM-select traversal with subtrees pruned, measurably beating flat vector recall on that query class, and a document mutation updates only local manifests with no sibling re-embed.

### Domain: Agents/Orchestration (2 tasks)
- **T-154**: MAO-01 -- Typed handoffs + parallel guardrails + tracing spans
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Handoffs are typed transfers with a hop failure caught and traced rather than swallowed; guardrails demonstrably run in parallel and can short-circuit; every hop emits a span visible on OWUI and the CLI; and `context_variables` carries shared state without appearing in any tool schema.
- **T-161**: MAO-08 -- Selectable topology + debate protocol from SSOT  [P2]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Topology and debate protocol are chosen per task-class from SSOT plus orchestrator judgement rather than a fixed code path, switching protocol visibly changes convergence/interaction behaviour as documented, and the default degrades open to today's fan-out.

### Domain: Agents/Reputation (1 tasks)
- **T-160**: MAO-07 -- Cheap contribution evaluation → reputation (IntrospecL
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: After a council session every agent carries an O(N) LOO contribution score in which a positively-necessary agent outscores a redundant one, those scores weight the next fan-out, and with no scoring model available weights fall back to equal.

### Domain: Aggregate container and host network flows in kernel eBPF maps to minimize monitoring overhead. (1 tasks)
- **AGY-2109**: In-kernel eBPF network flow aggregation probe and mios-netflowd collector daemon  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: eBPF flow probe aggregates network connections and streams summarized telemetry to userspace.
  - *Why:* In-kernel aggregation provides high-resolution network visibility without causing I/O bottleneck.

### Domain: Allocate POSIX shared memory in /dev/shm with atomic lock-free SPSC circular rings and eventfd signaling. (1 tasks)
- **AGY-2365**: Lock-free POSIX shared memory circular ring IPC engine in mios-shm-ring  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Shared-memory ring engine transfers high-bandwidth frames with sub-microsecond latency.
  - *Why:* Zero-copy lock-free shared memory delivers extreme IPC throughput for real-time multi-modal AI streaming.

### Domain: Allocate non-overlapping 65,536 subordinate UID/GID blocks per user account automatically. (1 tasks)
- **AGY-2075**: Deterministic /etc/subuid and /etc/subgid range generator in sysusers automation  (WS-USER | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Subordinate UID/GID ranges are generated deterministically with zero collision across user accounts.
  - *Why:* Non-overlapping user namespaces are essential for secure multi-tenant rootless container execution.

### Domain: Allow agents to index and search desktop visual states and window layouts using multi-modal embeddings. (1 tasks)
- **AGY-1972**: Multi-modal visual RAG pipeline extracting UI screenshot embeddings for desktop state reasoning  (WS-AI | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Visual memory indexes desktop screenshots periodically and enables visual state reasoning for UI automation agents.
  - *Why:* Autonomous desktop agents require visual grounding to debug graphical application errors and verify UI states.

### Domain: Allow dynamic registration of third-party and experimental subcommands without modifying core CLI code. (1 tasks)
- **AGY-2112**: Dynamic plugin loader and subcommand discovery in /usr/libexec/mios/plugins/  (WS-CLI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Dynamic plugin loader registers and executes external subcommands automatically.
  - *Why:* Subcommand extensibility allows modular feature expansion without touching base system binaries.

### Domain: An absent backend is a skip that says so, not a failure and not a silent pass. (1 tasks)
- **AGY-1717**: Make tests/test-reflection.py skip deliberately when no refine backend is reachable  (WS-CI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the suite skips with a named reason on a backend-less runner and asserts the correction where a backend answers.
  - *Why:* reflection is on the path every refined answer takes, and no CI has ever exercised it.

### Domain: An attached Android handset comes up as a CDC-NCM interface addressed from the SSOT, and an RNDIS handset is reported as degraded rather than silently accepted. (1 tasks)
- **AGY-2574**: USB CDC-NCM gadget orchestration, host link bring-up, and the edge.android_tether SSOT table  (WS-NODE-ANDROID | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Attach yields the SSOT-declared address on the tether interface; an RNDIS-only handset produces a degraded report; no IP, interface name or product ID is a literal in the script.
  - *Why:* The link is the precondition for every other Android task, and a wrong product ID silently produces an RNDIS link that no macOS host can drive.

### Domain: An authored file says why it is not projected. (1 tasks)
- **AGY-1911**: Authored files have no declared owner or reason  (WS-PROJ | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every authored file carries a reason and the not-yet-projected count is a declining ratchet.
  - *Why:* without reasons, the authored set becomes the place things go to stop being questioned.

### Domain: An exemption is temporary by construction. (1 tasks)
- **AGY-1825**: The exempt-suite table has a ceiling but no expiry  (WS-GATE | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: an exemption without a reason and a task id fails the check.
  - *Why:* exemptions without expiry become permanent, and the cap then measures nothing.

### Domain: App/Flatpak (1 tasks)
- **T-489**: Declarative Flatpak permission lockdown profiles in /etc/flatpak/overrides/
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Global Flatpak override profile enforces least-privilege sandbox boundaries across all installed desktop apps.

### Domain: App/Portal (1 tasks)
- **T-490**: XDG Desktop Portal permission and socket boundary verification suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Verification suite confirms sandbox containment for all baked Flatpak applications.

### Domain: Apply emergency kernel security livepatches and late microcode updates without system reboots. (1 tasks)
- **AGY-2143**: MOK-signed kpatch livepatching manager and late CPU microcode reload daemon  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Livepatch manager verifies signatures, applies in-memory patches, and reloads microcode seamlessly.
  - *Why:* Livepatching allows critical kernel vulnerability remediation on high-uptime clusters with zero service downtime.

### Domain: Apply signed kernel livepatches in <100ms via ftrace to neutralize critical CVEs with zero reboot downtime. (1 tasks)
- **AGY-2279**: Declarative kernel kpatch/livepatch manager and MOK signature validator in mios-kpatch  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Livepatch manager verifies and loads kernel security hotfixes dynamically with zero reboot downtime.
  - *Why:* Kernel live patching allows 24/7 AI and database servers to neutralize remote kernel exploits instantly.

### Domain: Apply sysctl --system and udev rules atomically in <50ms without requiring system reboots. (1 tasks)
- **AGY-2420**: Dynamic kernel sysctl/sysfs parameter synchronizer and udev reload daemon in mios-sys-sync  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: System synchronizer applies sysctl, sysfs, and udev rule updates on-the-fly in <50ms.
  - *Why:* Zero-reboot kernel parameter synchronization enables instant tuning of network, storage, and CPU parameters on live hosts.

### Domain: Arch/DeadCode (1 tasks)
- **T-1016**: UNWIRED-01 -- 112 of 176 usr/libexec/mios/<domain>/*.py modules have no caller; the gate that checks this looks elsewhere
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the extended check reports every unwired module by name; the register holds the measured 112 as a ceiling that only falls; a planted new unwired module under `usr/libexec/mios/<domain>/` fails the check, and a planted WIRED one does not.

### Domain: Artifacts land where the things that consume them look. (1 tasks)
- **AGY-1752**: One build output directory, derived, read by every consumer  (WS-DEPLOY | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: one declared path, and changing it in the SSOT moves every consumer.
  - *Why:* `just all` currently dies at `usb-installer` after hours of building, because the recipe cannot see the ISO its own dependency produced.

### Domain: Assign unique Core Scheduling cookies via PR_SET_CORE_SCHED to isolate untrusted subagent tasks on SMT siblings. (1 tasks)
- **AGY-2456**: Linux Core Scheduling cookie tagger and SMT sibling isolator in mios-core-sched  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Core scheduler tags untrusted processes and guarantees zero cross-SMT side-channel co-location.
  - *Why:* Core Scheduling eliminates speculative execution side-channel risks while retaining full multithreading performance.

### Domain: Attach 4 Medusa heads to base model to predict candidate trees and verify concurrently for 2.2x speedup. (1 tasks)
- **AGY-2454**: Medusa multi-head self-speculative decoding engine and tree attention verifier in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes Medusa self-speculative decoding with tree attention at >2.0x speedup.
  - *Why:* Medusa self-speculation doubles generation throughput without requiring additional VRAM for separate draft models.

### Domain: Attach eBPF programs to kernel LSM hooks (socket_bind, ptrace, file_open) for sub-microsecond policy enforcement. (1 tasks)
- **AGY-2440**: Declarative BPF LSM security policy enforcer and hook monitor in mios-bpf-lsm  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: BPF LSM programs enforce programmable in-kernel security policies and prevent privilege escalation.
  - *Why:* BPF LSM provides programmable, low-overhead in-kernel security enforcement that eliminates container escape vectors.

### Domain: Attach native XDP eBPF programs at NIC driver layer to process 10M+ pps and forward WireGuard packets directly. (1 tasks)
- **AGY-2400**: Native eBPF XDP network fastpath and WireGuard packet router in mios-xdp  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: XDP eBPF driver programs route packets and drop flood traffic at hardware line rate.
  - *Why:* Native driver-level XDP unlocks 10M+ packets/sec line-rate throughput for high-speed multi-node AI clusters.

### Domain: Audio/AECFilter (1 tasks)
- **T-786**: PipeWire virtual loopback manager and WebRTC AEC echo cancellation filter
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: PipeWire manages virtual loopbacks and suppresses speaker acoustic echo in microphone streams.

### Domain: Audio/AECTest (1 tasks)
- **T-787**: Automated acoustic echo cancellation (>40dB suppression) and full-duplex test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates high-performance echo cancellation and clean duplex microphone stream filtering.

### Domain: Audio/Benchmark (1 tasks)
- **T-506**: Automated audio buffer underrun and latency jitter benchmark suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Benchmark suite confirms inter-VM audio latency meets the sub-5ms performance SLA.

### Domain: Audio/Scream (1 tasks)
- **T-505**: Scream virtual audio to PipeWire JACK low-latency receiver daemon
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Scream receiver bridges VM audio to PipeWire with sub-5ms latency and zero crackling.

### Domain: Audio/VoiceTest (1 tasks)
- **T-829**: Automated WebRTC full-duplex voice latency (<120ms) and PipeWire bridge test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-120ms voice loop latency, PipeWire stream stability, and zero packet loss.

### Domain: Audio/WebRTCAudio (1 tasks)
- **T-828**: Duplex WebRTC audio gateway and PipeWire stream multiplexer in mios-webrtc-audio
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: WebRTC audio gateway streams full-duplex voice through PipeWire with <120ms turn-around latency.

### Domain: Audit /etc configuration drift against mios.toml and provide atomic reconciliation commands. (1 tasks)
- **AGY-2217**: Declarative configuration drift auditor and 3-way OCI overlay reconciler  (WS-CONFIG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Drift auditor detects un-tracked /etc modifications and reconciles state with SSOT cleanly.
  - *Why:* Continuous drift auditing preserves immutable reproducibility without sacrificing operator customization.

### Domain: Audit systemd service security exposures with systemd-analyze security and enforce exposure scores < 3.0. (1 tasks)
- **AGY-2263**: Declarative systemd unit hardening generator and security audit gate  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Systemd hardening script injects least-privilege sandboxing drop-ins and passes security audits.
  - *Why:* Declarative systemd sandboxing protects the host by containing compromised daemons inside restricted namespaces.

### Domain: Auth/MiOSUSB (1 tasks)
- **T-954**: Dedicated MiOS-USB global hardware key and FIDO2/PKCS#11 multi-node enrolment
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Authentication subsystem enrols and validates MiOS-USB hardware keys across all blades and edge nodes.

### Domain: Auth/MiOSUSBTest (1 tasks)
- **T-955**: Automated MiOS-USB FIDO2 token challenge-response (<10ms) and multi-node auth test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond token challenge verification, multi-node PAM integration, and zero key leakage.

### Domain: Auto-detect multi-GPU interconnect topology and calibrate NCCL environment variables for optimal AllReduce throughput. (1 tasks)
- **AGY-2311**: Automated NCCL topology discovery and NVLink/PCIe parameter optimizer in mios-nccl-tune  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: NCCL tuning engine discovers hardware topologies and optimizes collective communication parameters on boot.
  - *Why:* Optimal NCCL tuning unlocks near-linear multi-GPU Tensor Parallelism scaling for 70B+ model inference.

### Domain: Auto-dispatch Marlin INT4/FP16 kernels on Tensor Cores, ExLlamaV2 on AWQ/GPTQ, and GGUF to llama.cpp. (1 tasks)
- **AGY-2355**: Dynamic quantization kernel auto-dispatcher (Marlin / ExLlamaV2 / GGUF) in mios-quant-dispatch  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Quantization dispatcher dynamically selects and executes optimal hardware dequantization kernels.
  - *Why:* Hardware-tuned dequantization kernels maximize inference speeds across all quantized model formats.

### Domain: Automatically adjust sampling hyperparameters based on whether a task requires deterministic code or creative reasoning. (1 tasks)
- **AGY-1963**: Dynamic temperature and top-p scheduler based on task entropy estimation  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Sampling scheduler classifies prompt intent and applies optimal hyperparameter presets dynamically.
  - *Why:* Deterministic code generation requires zero-entropy greedy decoding to prevent syntax and logic hallucinations.

### Domain: Autonomous daemon agents coordinate via shared state mutations on PostgreSQL without HTTP point-to-point polling. (1 tasks)
- **AGY-1940**: Asynchronous document-mutation event bus over PostgreSQL LISTEN and NOTIFY  (WS-ORCH | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Autonomous tasks trigger reliably via database mutations and log event timestamps with sub-50ms reaction latency.
  - *Why:* Decoupled document mutation provides an auditable, persistent event trail while eliminating wasted CPU cycles from polling.

### Domain: Backlog (1 tasks)
- **T-1029**: QUEUE-02 -- one file per task under usr/share/mios/tasks/, typed frontmatter, acceptance criteria JOINED to drift-check ids
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `mios task ready --json` returns a selectable set from frontmatter alone with no document read; a task cannot reach `done` without a receipt naming a check that passed; both existing backlogs are migrated with every ID preserved; a hand-edited task file fails a gate.

### Domain: Bake restrictive Flatpak permission overrides into the immutable image. (1 tasks)
- **AGY-2087**: Declarative Flatpak permission lockdown profiles in /etc/flatpak/overrides/  (WS-APP | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Global Flatpak override profile enforces least-privilege sandbox boundaries across all installed desktop apps.
  - *Why:* Restricting Flatpak permissions prevents untrusted desktop apps from snooping key events or reading host configuration files.

### Domain: Bake signed physical host GPU drivers (NVIDIA/AMD/Intel) into the base image across all deployment shapes. (1 tasks)
- **AGY-2069**: Unified Host GPU Driver Ingestion & MOK Pre-Compilation Pipeline  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Physical host GPU drivers load automatically on boot across all deployment shapes with verified MOK signatures.
  - *Why:* Unconditionally loaded host drivers provide immediate hardware acceleration for local AI inference and CDI workloads.

### Domain: Binarize LoRA adapter weights to 1-bit signs with learnable scalar scales for 8x RAM savings and >3.6x speedup. (1 tasks)
- **AGY-2542**: Bi-LoRA binary low-rank adapter engine and sign-scaled integer dispatcher in mios-finetune-bilora  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Training and inference runtime fine-tunes and executes Bi-LoRA binary adapters at >3.6x speedup.
  - *Why:* Bi-LoRA enables parameter-efficient specialized adaptation of 1-bit models directly on edge devices with minimal RAM.

### Domain: Binarize Query/Key projections into 1-bit signs and compute attention via XOR-POPCOUNT for >5x speedup on 1M contexts. (1 tasks)
- **AGY-2502**: Bi-Attention 1-bit Query-Key binarization engine and Hamming dot-product kernel in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes Bi-Attention 1-bit QK Hamming dot-products at >5x speedup.
  - *Why:* Bi-Attention breaks the quadratic memory and bandwidth wall for million-token context retrieval via binary bitwise math.

### Domain: Binarize weights to 1-bit signs with residual compensation to fit 70B models in 11GB RAM at >250 tok/s on CPU. (1 tasks)
- **AGY-2462**: BiLLM 1-bit weight binarization engine and residual error compensation kernel in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine loads BiLLM 1-bit models and executes dual-popcount SIMD kernels on CPU.
  - *Why:* BiLLM 1-bit compression with residual compensation enables massive 70B models to run on standard laptops and NAS machines.

### Domain: Binarize weights/activations to 1-bit signs and compute matrix products via XNOR-POPCOUNT for >400 tok/s in <9.5GB RAM. (1 tasks)
- **AGY-2522**: BiLLM A1W1 pure bitwise XNOR-POPCOUNT matrix engine in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes BiLLM A1W1 via pure bitwise XNOR-POPCOUNT kernels at >400 tok/s on CPU.
  - *Why:* BiLLM A1W1 enables large 70B parameter models to run at lightning speed on low-power, multiplier-constrained mobile and edge devices.

### Domain: Boot/Composefs (1 tasks)
- **T-527**: Composefs fs-verity root filesystem sealing and atomic image descriptor validator
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Composefs seals the root filesystem and fs-verity blocks runtime binary modifications.

### Domain: Boot/Kargs (1 tasks)
- **T-1034**: UKICMD-01 -- a parse error in any kargs.d drop-in silently deletes that file's kernel args, and --check then certifies the result
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a corrupt drop-in makes BOTH the generator and `--check` exit non-zero and write nothing; the check compares against a source of truth other than a second run of the same generator; a fixture proves the ten mitigation args survive a clean render.

### Domain: Boot/Promotion (1 tasks)
- **T-508**: Automated UKI A/B boot promotion and Greenboot validation gate
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Greenboot gate automatically promotes verified staged UKI binaries to default boot entries.

### Domain: Boot/UKI (1 tasks)
- **T-507**: A/B UKI staging and systemd-ukify compilation pipeline with baked kargs
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: UKI compilation service builds staged UKIs with baked kargs and registers A/B boot entries.

### Domain: Bridge Windows/Linux VM guest audio to host PipeWire engine with sub-5ms latency. (1 tasks)
- **AGY-2103**: Scream virtual audio to PipeWire JACK low-latency receiver daemon  (WS-VFIO | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Scream receiver bridges VM audio to PipeWire with sub-5ms latency and zero crackling.
  - *Why:* Low-latency audio is essential for gaming VMs and real-time voice synthesis agents.

### Domain: Bridge browser WebRTC audio directly to PipeWire, ASR, and TTS to achieve <120ms conversational latency. (1 tasks)
- **AGY-2426**: Duplex WebRTC audio gateway and PipeWire stream multiplexer in mios-webrtc-audio  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: WebRTC audio gateway streams full-duplex voice through PipeWire with <120ms turn-around latency.
  - *Why:* Zero-latency WebRTC audio bridging delivers instantaneous, natural voice conversations with local AI models.

### Domain: Broadcast detailed hardware specifications and accelerator capabilities to the cluster coordinator. (1 tasks)
- **AGY-1992**: Edge node capability advertising in Announce frames  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Edge nodes advertise verified hardware specs and appear in the central cluster node registry.
  - *Why:* The scheduler requires accurate node capability telemetry to make optimal task placement decisions.

### Domain: Build customized Windows 11 installation media with pre-slipstreamed wireless/wired network drivers and unattended setup. (1 tasks)
- **AGY-1955**: DISM-native Windows 11 driver slipstreaming and offline network driver pack  (WS-WISO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Windows 11 installs zero-touch with functional networking out-of-the-box on mainstream hardware.
  - *Why:* Unattended offline provisioning fails completely if network adapters are unrecognized post-install.

### Domain: Build/Android (1 tasks)
- **T-977**: AArch64 target triple, explicit linkage decision, and on-device packaging for mios-node
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: CI emits an AArch64 artifact and `mios-node --version` runs on-device; the crate path cited in ROADMAP.md resolves.

### Domain: Build/BakePlan (1 tasks)
- **T-1057**: BAKEPARITY-01 -- BOTH halves of the headline are STALE, measured: the native producer is not "two fixes behind" (it renders all 5 .list files + bound-images.tsv byte-identical to the Python leg AND to the committed plan.d), and bare it does not render nothing or blame the SSOT (`env -i ... --check` from / exits 0; on an empty-SSOT tree it exits 2 naming the unresolved ${MIOS_VERSION_CEPH}, which is its own resolution failure, correctly attributed). The row's REAL clause held: one producer must make the plan and the same one must be what the gate certifies. It was not. MEASURED: the gate's candidate list was release/debug/libexec, stage 85's is libexec/release/python -- and CI builds DEBUG ONLY, so on every PR the gate certified target/debug, a binary stage 85 can never run. /usr/libexec/mios/mios-bake-plan -- stage 85's FIRST branch and the gate's third candidate -- has never existed, because 55-native-build.sh does not install it. DONE HERE: the gate resolves in stage 85's order from stage 85's candidates with debug dropped (a debug-only tree is exactly where the two diverge, so it is now loud -- control: the old list picks the debug binary that is present, the new one refuses); 55-native-build.sh installs mios-bake-plan; CI builds it --release, and also builds generate-names-registry so check_names_registry_equivalence stops compiling inside itself. STILL OPEN as T-1072: retiring the Python producer -- that is a deletion and needs a yes
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: one generator produces the plan and the same one is what `check_bake_plan` validates; the Rust resolves floated tags from SSOT rather than only from `env`, proved by a bare run (no exported `MIOS_VERSION_*`) rendering all 6 artifacts byte-identically to the Python's; an unresolvable placeholder names the VARIABLE, not the core image -- proved by planting one; the miosd module and `tools/native` copy do not drift again (one of them is deleted, or a gate diffs them); and `85-bake-plan.sh` dispatches by absolute path so the branch taken is not a function of PATH.

### Domain: Build/Cosign (1 tasks)
- **T-510**: Local Cosign image signing and registry push validation gate
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Cosign publish tool signs images and verifies signatures before host deployment transitions.

### Domain: Build/DNF5 (1 tasks)
- **T-503**: Atomic DNF5 package installation pipeline with local cache staging
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: DNF5 builds execute atomically with local caching and automated mirror failover.

### Domain: Build/Dispatch (1 tasks)
- **T-1018**: DISPATCH-01 -- 18 bake-time gates prefer the Rust path via a PATH lookup that cannot resolve; the Rust tier never runs
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: for each converted stage the Rust path is observably the one that runs during a bake AND its output is byte-identical to the bash fallback it replaces; `[build.tool_dispatch].max_unreachable` falls to 0; each bash fallback is deleted in the commit that proves its replacement, per ADR-0021.

### Domain: Build/Firewall (1 tasks)
- **T-1041**: FIREWALL-01 -- a malformed or absent [firewall] table silently opens a hardcoded wrong port set, and an unbound var aborts the tier mid-sequence
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a malformed or absent `[firewall]` table FAILS the stage rather than falling back; the argv sequence is identical between tiers on the real SSOT and on a planted one; no unbound variable can abort the tier mid-sequence.

### Domain: Build/HWCaps (1 tasks)
- **T-1005**: HWCAPS-01 -- build the glibc-hwcaps rebuild stage [hwcaps] specifies
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the stage runs in the pipeline and its output is observable (variant directories exist and ld.so selects them); toggling `native_rebuild` in a COPY of the SSOT changes whether the stage does work; `level` selects the variant set; and the pipeline index regenerates to include the new stage with no hand edit.

### Domain: Build/Image (1 tasks)
- **T-330**: BAKE-01 -- A ~16 GB payload ships for a lane no archetype starts
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the decision is made explicitly and recorded in ADR-0016 rather than inherited from a default nobody chose. Either (a) the payload becomes opt-in -- empty by default, baked when the operator sets it, with the heavy lane's first start documented as needing egress; or (b) it stays baked and the ADR says why, with the size stated so it is a chosen cost. **Measure the real bake delta before choosing** -- the ~16 GB figure is the SSOT's prose, not something this session weighed.

### Domain: Build/Phases (1 tasks)
- **T-1038**: PHASELIST-01 -- [build.phases].list omits 55-native-build.sh and load_from_toml fails open to a 6-phase hardcoded registry
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `[build.phases].list` matches the scripts on disk under a regenerate-and-diff guard; a nonexistent root, malformed TOML, an empty list, a miosd non-zero exit and a mistyped script name each exit non-zero; the ordered ALL_SCRIPTS list is byte-identical with miosd absent and present.

### Domain: Build/Quadlets (1 tasks)
- **T-1040**: ENVSUB-01 -- envsubst eats systemd's $$ runtime refs, the nested-default regex corrupts base_url, and *.socket is outside the find filter
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: no rendered unit under the scan dirs contains a residual `${MIOS_`; the socket unit renders its port; `base_url` renders exactly once; a fixture pins the systemd `$$` no-substitute list.

### Domain: Build/RPMTest (1 tasks)
- **T-504**: Upstream mirror failover and RPM transaction integrity verification test
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Automated test suite validates DNF5 mirror failover and transaction integrity.

### Domain: Build/RollbackTest (1 tasks)
- **T-502**: Automated boot-failure and Greenboot atomic rollback recovery test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates automatic greenboot rollback on simulated boot failure.

### Domain: Build/Rust (6 tasks)
- **T-1007**: LANG-02 -- one src/mios-rs workspace: absorb tools/native, vendor deps, builder stage, cross-compiled targets
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: one `cargo build --workspace` from src/mios-rs emits every binary for every declared target with the network off; `tools/native/` holds no crate of its own; every legacy binary name still resolves; `podman history` shows no cargo/rustc layer in the final image.
- **T-1008**: LANG-03 -- make mios-resolver the ONE Rust reader; 11 files parse mios.toml around it
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: miosd resolves through mios-resolver and matches the Python twin byte-for-byte on a planted three-layer fixture, including the empty-string-does-not-override rule and the derived-port case; mios-config carries no loader of its own; the count of Rust files parsing mios.toml directly only falls; perturbing ANY ONE of the three twins fails the twin check and names which one.
- **T-1009**: LANG-05 -- mios-gate: port the drift checks strangler-style, byte-identical plus surviving negative controls
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: for each ported check, old and new emit identical bytes on the current tree; the negative control still fails and names the planted cause; the script is gone; `[legibility].max_tooling_python_lines` and `max_shell_lines` both fall.
- **T-1010**: LANG-06 -- mios-gen: port the generate-*/render-* SSOT projectors
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: each ported generator reproduces its committed output byte-for-byte; its drift-check still fails on a hand-edited derived file; the script is gone.
- **T-1012**: LANG-07 -- cross-compile the PowerShell host surface, keeping only the paste-able entry point
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `Get-MiOS.ps1` still runs from one paste with no follow-up step; the verb dispatcher's backends are binaries; `[legibility].max_ps_lines` falls and stays fallen.
- **T-1015**: MIGRATE-01 -- all four [migration].use_rust_resolver_* toggles say true and nothing reads them
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: flipping any `use_rust_resolver_*` to false in a COPY of the SSOT observably changes which implementation resolves that surface, proved per surface; or the keys are gone and the ADR says the cutover is unstarted.

### Domain: Build/SBOM (1 tasks)
- **T-509**: Hermetic multi-stage Podman OCI image synthesis and Syft SBOM generation pipeline
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Build pipeline compiles OCI image and generates verifiable SPDX SBOM automatically.

### Domain: Build/Testbed (1 tasks)
- **T-501**: Headless QEMU KVM/TCG microVM boot and Greenboot verification test runner
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Headless microVM test runner boots generated images and validates greenboot health in automated CI.

### Domain: CI produces an AArch64 mios-node binary that runs on the handset. (1 tasks)
- **AGY-2575**: AArch64 target triple, explicit linkage decision, and on-device packaging for mios-node  (WS-NODE-ANDROID | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CI emits an AArch64 artifact and `mios-node --version` runs on-device; the crate path cited in ROADMAP.md resolves.
  - *Why:* mios-node is x86_64-only today, so the edge node is a document rather than a deployment.

### Domain: CI/Enforcement (3 tasks)
- **T-1001**: GATE-05 -- check_no_inert_ssot_tables credits a table from prose, and cannot tell a sub-table read from a top-level one
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a comment or docstring naming an access shape does NOT credit the table -- proved by planting such a comment for a registered table and observing the register entry survive; a read of `[x].y` does not credit top-level `[y]` -- proved the same way; and the clean tree's consumed count is re-measured and the register reconciled to whatever the tightened predicate actually finds.
- **T-997**: GATE-02 -- check_schema_consumers shares the name-collision blind spot; a SQL-context predicate closes it
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a dead table is reported dead whether or not its name collides with existing text -- proved by planting two identical unused tables, one common-word and one nonsense, and observing both flagged; every currently declared table is matched or registered, so the clean tree still passes; and a table consumed only through a schema-qualified reference is still recognised as live.
- **T-998**: GATE-03 -- the value-dup ledger's sanctioned remedy for coincidental duplicates is rejected by check_value_aliases
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a coincidental equal-value pair has exactly one documented, gate-accepted representation; the T-996 pair (MIOS_SCHED_URGENCY_HIGH / MIOS_SSOT_TABLES_MAX_UNCONSUMED) passes through it; and both gates agree on what keep-distinct means.

### Domain: CLI/Plugins (1 tasks)
- **T-514**: Dynamic plugin loader and subcommand discovery in /usr/libexec/mios/plugins/
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Dynamic plugin loader registers and executes external subcommands automatically.

### Domain: Cache pre-computed KV-cache states in a Radix tree to achieve sub-20ms TTFT on shared prompt prefixes. (1 tasks)
- **AGY-2233**: Radix tree prefix hash cache manager and prompt KV warm-starter in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine reuses warm KV caches for static prompt prefixes across agent turns.
  - *Why:* Prefix caching eliminates redundant prompt processing and delivers 10x faster agent tool-loop response times.

### Domain: Cache web search results locally in pgvector for instant zero-latency retrieval on repeated queries. (1 tasks)
- **AGY-2074**: Search Result Semantic Vector Cache & Deduplication in pgvector  (WS-RAG | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Semantic search cache serves repeated queries locally with sub-10ms response times.
  - *Why:* Local search caching saves network bandwidth, accelerates agent turn latency, and improves offline usability.

### Domain: Capture DMA-BUF frames from PipeWire, encode via NVENC/VAAPI/AMF, and stream over WebRTC with <30ms latency. (1 tasks)
- **AGY-2386**: Hardware-accelerated PipeWire WebRTC desktop video streamer in mios-screen-stream  (WS-APP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Screen streamer encodes PipeWire DMA-BUF frames on GPU hardware and streams over WebRTC.
  - *Why:* Hardware-accelerated WebRTC streaming delivers crisp, instantaneous remote desktop visualization for humans and agents.

### Domain: Capture Hyprland framebuffers via GPU DMA-BUF descriptors and feed NVENC/VA-API for 60fps WebRTC streaming in <16ms. (1 tasks)
- **AGY-2444**: Zero-copy DRM DMA-BUF frame capture and hardware encoder pipeline in mios-dmabuf-stream  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Desktop streamer captures DMA-BUF frames and encodes 60fps video directly on GPU silicon.
  - *Why:* Zero-copy DMA-BUF streaming delivers responsive, high-fps remote desktop interaction for human operators and AI agents.

### Domain: Capture decoding kernels into static CUDA Graphs for batch sizes 1..16 to eliminate CPU driver launch overhead. (1 tasks)
- **AGY-2307**: Static CUDA Graph capture manager and multi-batch hardware replay buffer  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine captures and executes CUDA Graphs for fixed decoding batches with zero CPU launch stalls.
  - *Why:* CUDA Graphs eliminate CPU-to-GPU launch roundtrips and double single-batch token generation speeds.

### Domain: Capture minimal compressed kernel crash dumps on panics and reboot safely. (1 tasks)
- **AGY-2113**: Reserved memory kdump kernel deployment and automated zstd crash dump extractor  (WS-DIAG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Kdump captures compressed crash dumps to persistent storage and reboots safely on panics.
  - *Why:* Forensic crash dumps provide essential diagnostics to troubleshoot driver panics and hardware faults.

### Domain: Catch USB over-current kernel events, isolate the faulting port, and cycle port power safely. (1 tasks)
- **AGY-2275**: Udev USB over-current event handler and port power cycling daemon  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: USB surge daemon catches over-current faults, suspends port power, and recovers port after cool-down.
  - *Why:* Automated USB over-current isolation prevents permanent motherboard hardware damage from faulty peripherals.

### Domain: Classify target hardware across consumer PC, laptop, NAS, and mobile phone tiers for localized AI inference. (1 tasks)
- **AGY-2450**: Consumer PC, Laptop, NAS, and modern smartphone edge target matrix in mios-hardware-profile  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Hardware profiler classifies device tiers and configures AI inference profiles across all supported hardware.
  - *Why:* A comprehensive hardware target matrix ensures MiOS runs seamlessly from modern smartphones to multi-GPU servers.

### Domain: Compact historical tool outputs at 75% context capacity while preserving essential reasoning milestones. (1 tasks)
- **AGY-2145**: Semantic KV-cache context compaction engine and episodic summary generator in agent-pipe  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Context compaction engine compresses historical trajectory and writes episodic milestones to PostgreSQL.
  - *Why:* Semantic compaction enables infinite-horizon agent execution loops without hitting model context boundaries.

### Domain: Compile and sign staged UKI images with updated kernel command-line parameters safely. (1 tasks)
- **AGY-2105**: A/B UKI staging and systemd-ukify compilation pipeline with baked kargs  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: UKI compilation service builds staged UKIs with baked kargs and registers A/B boot entries.
  - *Why:* Baked UKI kargs maintain cryptographic boot integrity while A/B staging prevents bricked bootloaders.

### Domain: Compile out-of-tree .ko drivers inside bubblewrap, sign with local MOK key, and cache in /var/lib/dkms/. (1 tasks)
- **AGY-2363**: Ephemeral containerized DKMS engine and MOK kernel module signer in mios-dkms  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: DKMS subsystem compiles and signs out-of-tree drivers inside isolated containers.
  - *Why:* Ephemeral containerized DKMS enables custom hardware support while preserving the immutable bootc root filesystem.

### Domain: Compress historical conversation turns into concise factual nodes linked in the PostgreSQL fact ledger. (1 tasks)
- **AGY-1970**: Cross-turn episodic memory compaction into hierarchical semantic trees  (WS-RAG | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Episodic memory compacts automatically and provides relevant factual recall on subsequent queries.
  - *Why:* Uncompacted chat logs consume excessive database storage and slow down semantic search recall.

### Domain: Compress historical journal logs to columnar Parquet files and index diagnostic error clusters into pgvector. (1 tasks)
- **AGY-2197**: Structured Parquet log archival daemon and episodic vector indexer in mios-log-archiver  (WS-RAG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Log archiver compacts journal logs to Parquet and indexes error clusters into pgvector automatically.
  - *Why:* Columnar log compaction saves 85%+ disk space while vector indexing enables instant natural-language root cause diagnosis.

### Domain: Compute/AI-lanes (2 tasks)
- **T-211**: IGPU-01 -- In-VM iGPU compute lane; retire native `mios-igpu-ser
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the iGPU lane serves inference from inside the VM and both the native Windows iGPU server and its Tailscale hop are gone from the tree and from the running host.
- **T-212**: IGPU-02 -- llama.cpp RPC fabric across lanes + coopmat2 verify
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a model larger than any single lane's VRAM answers a request through the one logical endpoint; coopmat2 is confirmed working on the Vulkan lane.

### Domain: Computer Use (2 tasks)
- **T-038**: CU-01 -- Computer-Use Action Hierarchy + Verify-After-Action
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A click tries the a11y tree first and only falls back to vision on a11y failure, a Qwen3-VL normalized `(512,384)` maps correctly to physical pixels on 1920x1080, a failed click is caught by verify-after-action and retried with re-grounding, and 3 exhausted retries escalate to HITL.
- **T-065**: GAP-6 -- smart_resize: Formal 3-Constraint Spatial Normalization
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A 3840x2160 HiDPI screenshot resizes to a patch-aligned tensor, raw VLM coord (512,384) maps to physical pixel (1536,1152), `pc_click` lands within 2px of the target element, and a constraint violation raises a logged error instead of silently shipping a corrupt tensor.

### Domain: Configure Alacritty/Ghostty with OpenGL/Vulkan glyph shaders and Wayland DMA-BUF for sub-5ms latency. (1 tasks)
- **AGY-2325**: GPU-accelerated terminal configuration and Wayland zero-copy DMA-BUF presentation manager  (WS-APP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Terminal emulator uses GPU shader acceleration and locks rendering to display refresh VSync.
  - *Why:* GPU shader acceleration provides instantaneous keystroke response during high-velocity AI token streaming.

### Domain: Configure Cilium BGP Control Plane with ECMP to announce service VIPs directly to upstream routers. (1 tasks)
- **AGY-2357**: Cilium native BGP peering and dual-stack ECMP LoadBalancer ingress manager  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Cilium BGP Control Plane announces LoadBalancer VIPs to upstream routers with sub-100ms BFD failover.
  - *Why:* Native BGP VIP announcement enables enterprise-grade high availability and load balancing for cluster services.

### Domain: Configure Level Zero runtime and XMX SYCL kernels for 16-token PagedAttention blocks on Intel Arc/Battlemage. (1 tasks)
- **AGY-2367**: Intel oneAPI Level Zero PagedAttention engine and XMX SYCL matrix kernels in IPEX  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Intel GPU inference lane executes PagedAttention via oneAPI Level Zero and XMX kernels.
  - *Why:* Level Zero XMX acceleration brings high-density local inference to Intel Arc and Xe workstation graphics.

### Domain: Configure Netavark with rootless nftables chains and restrict container port bindings to loopback/mesh IPs. (1 tasks)
- **AGY-2339**: Declarative Netavark network isolation and rootless nftables firewall manager  (WS-APP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Netavark isolates container network bridges and binds ports strictly to loopback and mesh IPs.
  - *Why:* Declarative network firewalling prevents compromised containers from moving laterally or exposing internal ports to LANs.

### Domain: Configure PCIe ASPM L1.2 sub-states and runtime D3cold to reduce idle GPU power draw to <3W. (1 tasks)
- **AGY-2281**: PCIe ASPM L1.2 and runtime D3cold GPU power manager in mios-gpu-powerd  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: GPU power manager enables ASPM L1.2 sub-states and transitions idle GPUs into sub-3W D3cold sleep.
  - *Why:* PCIe ASPM and D3cold power transitions maximize laptop battery endurance and reduce thermal noise at idle.

### Domain: Configure THP in madvise mode with proactive background compaction and khugepaged defragmentation. (1 tasks)
- **AGY-2398**: Transparent Huge Pages (THP madvise) and proactive memory compaction manager  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Kernel allocates huge pages via madvise and defragments memory in the background asynchronously.
  - *Why:* THP madvise reduces TLB cache misses and accelerates large AI tensor computations by up to 25% without memory bloat.

### Domain: Configure WirePlumber for LDAC/AptX HD codec auto-negotiation and deploy persistent virtual audio loopbacks. (1 tasks)
- **AGY-2211**: WirePlumber high-fidelity Bluetooth policy manager and virtual loopback provisioner  (WS-APP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: WirePlumber negotiates high-bitrate Bluetooth codecs and creates isolated virtual audio loopback channels.
  - *Why:* High-fidelity Bluetooth codecs and virtual loopbacks deliver audiophile-grade playback and echo-free agent voice isolation.

### Domain: Configure hardware /dev/watchdog devices and systemd RuntimeWatchdogSec to recover frozen nodes automatically. (1 tasks)
- **AGY-2209**: Tiered hardware watchdog driver configurator and systemd watchdog integration  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Watchdog configurator binds hardware watchdog and enforces systemd service ping loops.
  - *Why:* Hardware watchdogs guarantee autonomous node recovery from hard kernel deadlocks or unresponsive agent daemons.

### Domain: Configure hardware GPU slices (MIG / ROCm partition) from mios.toml and generate scoped CDI device profiles. (1 tasks)
- **AGY-2183**: Declarative NVIDIA MIG / AMD ROCm hardware slice configurator and dynamic CDI generator  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: MIG configurator partitions hardware GPU instances and binds CDI profiles automatically.
  - *Why:* Hardware GPU slicing guarantees dedicated compute and memory bandwidth for latency-sensitive voice and agent workloads.

### Domain: Configure io_uring with IORING_SETUP_SQPOLL and fixed file descriptors for >1,000,000 IOPS zero-syscall I/O. (1 tasks)
- **AGY-2438**: Dedicated in-kernel io_uring SQPOLL thread manager and registered buffer allocator  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Storage engines process I/O asynchronously via in-kernel io_uring SQPOLL threads.
  - *Why:* Zero-syscall io_uring SQPOLL eliminates kernel context switch overhead, unlocking the full potential of NVMe SSDs.

### Domain: Configure multi-tier Bcachefs (foreground=nvme, background=hdd) with transparent zstd compression. (1 tasks)
- **AGY-2359**: Declarative Bcachefs multi-device tiering and transparent SSD caching manager  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Bcachefs manages multi-device tiering and transparent SSD caching seamlessly in-kernel.
  - *Why:* Bcachefs tiering combines NVMe write burst speeds with high-capacity bulk drive density transparently.

### Domain: Configure native kernel overlayfs with ID-mapped mounts and metacopy=on for 10x faster rootless container I/O. (1 tasks)
- **AGY-2303**: Native in-kernel ID-mapped OverlayFS storage configurator for rootless Podman  (WS-APP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Podman storage configuration activates native kernel overlayfs with ID-mapped mounts for rootless containers.
  - *Why:* Native kernel overlayfs eliminates context-switch overhead and provides 10x faster container build I/O.

### Domain: Configure systemd-boot for 0s timeout fastboot with signed UKI baked kargs and Space/Esc recovery override. (1 tasks)
- **AGY-2297**: Zero-timeout systemd-boot silent fastboot configurator and baked UKI kargs manager  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Systemd-boot executes zero-timeout silent fastboot to signed UKI with emergency key fallback.
  - *Why:* Zero-timeout direct UKI fastboot maximizes boot speed while guaranteeing immutable kernel argument security.

### Domain: Configure systemd-coredump for zstd compression, exclude secret memory, and extract stack minidumps. (1 tasks)
- **AGY-2349**: Sanitized systemd-coredump configurator and automated minidump extractor in mios-crash  (WS-DIAG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Systemd-coredump captures sanitized minidumps in journal/database and purges raw memory dumps.
  - *Why:* Sanitized minidump extraction enables instant autonomous crash diagnosis without risking credential leakage or disk bloat.

### Domain: Configure systemd-oomd to kill thrashing background tasks at 50% PSI and protect core desktop/database services. (1 tasks)
- **AGY-2265**: Declarative systemd-oomd memory pressure configuration and cgroup2 PSI policies  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Systemd-oomd mitigates memory thrashing by killing low-priority cgroups and protecting core services.
  - *Why:* Declarative PSI-based OOM mitigation prevents kernel swap thrashing and desktop lockups under extreme RAM pressure.

### Domain: Configure systemd-oomd with 50% PSI thresholds, protect core system slices, and evict subagent workers first. (1 tasks)
- **AGY-2418**: Proactive systemd-oomd PSI pressure manager and cgroup hierarchy protector  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Systemd-oomd evicts runaway worker cgroups under PSI pressure and preserves system stability.
  - *Why:* Proactive PSI-based memory reclamation prevents destructive system freezes and guarantees continuous OS availability.

### Domain: Consequential system tasks trigger a 4-archetype deliberation council that converges on structured Decision Packets. (1 tasks)
- **AGY-1939**: Structured deliberation loop with typed epistemic grammar and Decision Packets  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Consequential prompts execute structured deliberation and persist the resulting Decision Packet in `fact_ledger`.
  - *Why:* High-impact system operations require rigorous multi-perspective challenge and consensus rather than unverified single-agent execution.

### Domain: Consolidate WebView2 background rendering and WSLg window watching into a single, native Rust service (`mios-wallpaperd`). (1 tasks)
- **AGY-1956**: Unified Rust living wallpaper daemon with live SSOT color theme sync  (WS-LANG | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The native Rust wallpaper daemon runs silently as a Windows service and dynamically reflects system theme changes.
  - *Why:* Native compiled wallpaper rendering eliminates memory bloat, avoids console flashing, and ensures unified cross-platform branding.

### Domain: Consolidate background polling and supervisor loops into a single high-performance native daemon. (1 tasks)
- **AGY-1995**: Standalone compiled miosd daemon in Rust replacing Python supervisor loops  (WS-LANG | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The native `miosd` daemon replaces loose Python supervisor scripts with sub-15MB RAM utilization.
  - *Why:* Native compiled system daemons drastically reduce system memory footprint and eliminate Python interpreter overhead.

### Domain: Container units are held to the same standard as service units. (1 tasks)
- **AGY-1835**: Quadlet container files are projected but not covered by the unit gate  (WS-UNITS | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: one command reports projection status for both systemd units and Quadlets.
  - *Why:* Quadlets are the larger surface in the image and are currently measured less rigorously than units.

### Domain: Create virtual loopback sinks and filter mic/desktop audio via webrtc-aec to eliminate feedback loops. (1 tasks)
- **AGY-2384**: PipeWire virtual loopback manager and WebRTC AEC echo cancellation filter  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: PipeWire manages virtual loopbacks and suppresses speaker acoustic echo in microphone streams.
  - *Why:* Acoustic echo cancellation allows seamless full-duplex conversational voice interaction while media plays.

### Domain: D-1 The comment corpus is lossless -- a re-tag can never truncate or split a header, so every downstream doc generator reads whole prose. (1 tasks)
- **AGY-1580**: Fix mios-ai-tag's multi-line hint orphaning and repair the 22 damaged headers  (WS-DOCGEN | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-ai-tag --selftest` passes; a full `--no-llm --dry-run` over the tree reports zero diffs on already-tagged files; no `AI-related:` line in the tree ends in a comma.
  - *Why:* generating a manual from a corpus with silent truncation bakes the truncation into the product, and every later step reads this corpus.

### Domain: D-10 No documentation surface is built by scraping deleted comments or dumping whole files. (1 tasks)
- **AGY-1592**: Retire the comment graveyard and the unified-knowledge dump  (WS-DOCGEN | P2 | M) **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: all three are gone, `ai-bootstrap.sh` and `sync-wiki.py` consume the audit JSON, and the markdown corpus drops from 9.99 MB to ~5.9 MB.
  - *Why:* 42% of the doc corpus by bytes is mechanically-transcribed deleted comments shipped into `/usr/share/doc/`, and one commit has already re-duplicated part of it back into manual.md.

### Domain: D-11 Every fact has one home; the codebase is quickly auditable because there is nothing to cross-check. (1 tasks)
- **AGY-1593**: Collapse the 69-copy boilerplate, the 3 duplicate doc pairs, and mios-codebase-index's rival taggability  (WS-DOCGEN | P2 | M) **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the boilerplate exists once; the three pairs are one file each with a pointer; `mios-codebase-index` defines zero taggability constants of its own and its file count matches `mios-ai-hint-coverage`'s denominator.
  - *Why:* "fewer, more feature-complete components" is unachievable while three tools disagree about which files exist and one paragraph has 69 independently-drifting copies.

### Domain: D-3 "Stay in code" vs "migrate to docs" is a mechanical, testable function -- not a judgement call made once per file by whoever is reading it. (1 tasks)
- **AGY-1583**: Build the comment lexer + classifier library with the 30-fixture unit test  (WS-DOCGEN | P1 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: all 30 fixtures pass; aggregate counts over the real tree land within 3% of STAY ~5,000 / MIGRATE ~1,900 / DROP ~400 / READONLY 42; `test_mios_manual.py` runs inside `just drift-gate` beside `test_mios_docgen.py`.
  - *Why:* without a fixed classifier the ratchet has no comparable number and "we migrated some comments" is unmeasurable.

### Domain: D-4 Documentation references resolve -- an `AI-related` line that names a file which no longer exists sends the next reader (human or agent) to a dead path. (1 tasks)
- **AGY-1601**: Ratchet the 150 stale AI-related references down to zero  (WS-DOCGEN | P2 | M) **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `max_stale_refs` reaches 0 and `check_doc_refs_resolve` passes with it; no reference is silenced by widening the allowlist without a stated reason.
  - *Why:* the count was 0 only because the check could never fail -- its violations went to stderr while the wrapper captured stdout, so it reported success on every run. The real backlog was invisible.

### Domain: D-4 One documentation CLI exists, it reads the repo, and its output is reproducible byte-for-byte between a developer and CI. (1 tasks)
- **AGY-1584**: Land `mios-manual` with the corpus ledger and retire generate-manual.py  (WS-DOCGEN | P1 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-manual ledger --check` is green on a clean tree; two runs from different CWDs produce byte-identical output; `tools/generate-manual.py` and the `manual:` Justfile target are gone.
  - *Why:* the two surfaces in this repo that are actually documentation are the only two with no drift gate, which is exactly why the shipped manual has 21 dead links and 50 `file:///C:/MiOS/` paths inside a Linux OS's docs.

### Domain: D-5 Regeneration can never destroy hand-written prose, and a stale manual fails the build. (1 tasks)
- **AGY-1585**: Create the authored manual tree and gate manual.md with `render --check` (the real AGY-238)  (WS-DOCGEN | P1 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `render --check` is green; appending a line to manual.md turns gate 152 red; appending a paragraph OUTSIDE a marker in a chapter file leaves it green; `just sync` regenerates the manual.
  - *Why:* today regenerating the manual DELETES its H1 title while simultaneously fixing 20 dead links -- the committed file and its generator diverged in both directions, the signature of an ungated generator.

### Domain: D-6 A path, unit or `mios-*` name printed in a header or a generated doc is guaranteed to exist. (1 tasks)
- **AGY-1587**: Add `check_doc_refs_resolve` and clear the ~70 verified stale references  (WS-DOCGEN | P1 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `max_stale_refs = 0` and the gate is green; injecting `# AI-related: automation/99-nonexistent.sh` into a scratch file turns it red.
  - *Why:* 24 of the ~70 stale refs sit inside AI-hint/AI-related header lines, which never self-correct because `mios-ai-tag` reuses an existing hint verbatim forever -- so without a gate they are permanent.

### Domain: D-7 The ~100k characters of prose currently hiding in the `AI-hint:` field live in documentation, and the tagger's own cap becomes safe to re-impose. (1 tasks)
- **AGY-1588**: Harvest the 363 over-cap AI-hints into docs, then prune them behind the landing gate  (WS-DOCGEN | P1 | L) **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: harvest and prune are SEPARATE commits with `audit --deletions` green between them; a full `mios-ai-tag --no-llm` pass is byte-identical afterwards; gate 154 goes red if a harvested passage is gutted.
  - *Why:* this is the single largest data-loss hazard in the tree -- `existing_hint()` re-applies the 260-char cap on reuse, so the very next tagger run silently truncates all 363.

### Domain: D-8 Narrative comment volume can only go down, and "raise the ceiling" is a gate violation rather than a one-character fix. (1 tasks)
- **AGY-1589**: Land the comment ratchet and its monotone guard  (WS-DOCGEN | P1 | M) **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: both gates are enforcing at the measured baseline, both RED edits have been observed red and reverted, and the ratchet number appears in `just drift-gate` output.
  - *Why:* gate 155 alone is unfalsifiable in practice -- this repo has a documented history of gates that cannot fail, and a ratchet whose ceiling is freely raisable is exactly one of them.

### Domain: D-9 The 1,764 narrative blocks / 16,481 lines / ~150k words of design prose living in comments become chapters and ADRs. (1 tasks)
- **AGY-1590**: Harvest the narrative mass: mios.toml, the two Windows entry points, and the agent-pipe tree  (WS-DOCGEN | P2 | XL) **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each wave lands as harvest-commit then prune-commit with `audit --deletions` green between; `max_unmigrated_narrative` has fallen by the wave size; no source block was deleted without a ledger row proving its landing.
  - *Why:* this is the extraction prize -- ~150k words of decisions, rejected alternatives and incident history that today only an agent reading whole files can find.

### Domain: Data/Durability (1 tasks)
- **T-175**: DURA-01 -- pgvector durability + exposure hardening. EXPOSURE AUDITED: the cluster binds `listen_addresses=127.0.0.1` on the `pgvector` port inside `mios-ai.pod` as uid 826 (not network-exposed), but its credential is `Environment=POSTGRES_PASSWORD=mios` in a WORLD-READABLE Quadlet -- and Law 11's enforcer never saw it, because it scans only `*.env`/`*secrets*` files for three hardcoded secret NAMES. A sweep found 7 such literals across units, including `WEBUI_SECRET_KEY=mios-stable-secret-change-me`. LANDED: `check_credential_literals` (gate 162) + `[security.credential_literals].grandfathered`, a SHRINK-ONLY registry -- the 7 are recorded, a NEW one fails the gate, and removing one without updating the list also fails. It distinguishes credentials from token COUNTS, boolean flags and `${VAR}` indirection (8-case sibling test + negative test). REMAINING for done: rotate the 7 into `/etc/mios/secrets.env` (0600) via `EnvironmentFile=`, which needs firstboot generation plus unit ordering AND a migration guard -- POSTGRES_PASSWORD only applies at initdb, so rotating it on an existing cluster locks the agent plane out of its own datastore. Needs a host to validate; not shippable blind. Durability (WAL/backup cadence) also still open.
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the timer fires and leaves a restorable dump under `/var/lib/mios/backups`; `ss -ltnp` shows pgvector on `127.0.0.1` only with stock config and an off-loopback bind is refused without a non-default password; `bootc container lint` and the NO-MKDIR-IN-VAR postcheck stay green.

### Domain: Data/Migration (1 tasks)
- **T-240**: A3F-01 -- Central-path legacy-datastore→pg primary flip + un-mirrored w
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: With `db_backend=postgres`, a live recall + skill round-trip passes and no write site bypasses pg; the RELATE-edge schema decision is applied in the schema.

### Domain: Data/State (1 tasks)
- **T-980**: Transient-link ledger reconciliation and CRDT type-name correction
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Detach, mutate on both sides, reattach: no write lost, no merge blocked; and the type name matches its implementation.

### Domain: Database/CompactTest (1 tasks)
- **T-776**: Automated vector memory compaction, disk reclamation, and non-blocking query test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates non-blocking vector reindexing, disk space reclamation, and sustained query throughput.

### Domain: Database/MemCompact (1 tasks)
- **T-775**: Semantic memory distillation daemon and non-blocking vector reindexer in mios-mem-compact
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Memory compaction daemon distills scratchpads and reindexes vector tables non-blockingly.

### Domain: Declare known hardware blades with TPM Endorsement Key fingerprints in mios.toml for automated zero-touch enrollment. (1 tasks)
- **AGY-2127**: Declarative SSOT blade pre-enrollment registry and TPM EK fingerprint parser  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: SSOT parser registers declared hardware blades with valid TPM EK fingerprints.
  - *Why:* Declarative pre-enrollment establishes an explicit hardware root-of-trust before blades connect to the mesh.

### Domain: Declared units reach the image. (1 tasks)
- **AGY-1836**: A unit can be declared, faithful, and still not installed  (WS-UNITS | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a unit declared in the SSOT but absent from the built image fails.
  - *Why:* the thesis is about the OS the image is, not the files the repo holds.

### Domain: Declaring a unit in the SSOT is not scored as a regression. (1 tasks)
- **AGY-1935**: Declaring a unit trips three shrink-only ratchets, so campaign 2 cannot proceed  (WS-UNITS | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: declaring a unit moves only measures that should move, and the remaining 52 can be declared without a ratchet decision each time.
  - *Why:* the roadmap calls unit projection the largest single gap in "one file defines the OS", and its own gates currently score closing that gap as regression.

### Domain: Decompose model matrices into truncated SVD factors (U*V) and quantized residuals (R) for 70% bandwidth savings. (1 tasks)
- **AGY-2408**: SVD-LLM low-rank matrix factorization engine and residual adapter dispatcher  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine loads SVD-factored models and executes fused low-rank residual projections.
  - *Why:* SVD-LLM low-rank factorization preserves critical outlier channels while drastically slashing memory bandwidth demands.

### Domain: Decompress /var/crash/vmcore.zst, extract demangled C/Rust backtraces headlessly, and file bug reports into PostgreSQL. (1 tasks)
- **AGY-2239**: Headless kernel crash dump triage engine (drgn / crash) and symbol resolver  (WS-DIAG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Crash triage service extracts demangled stack traces from vmcore dumps and records bug reports.
  - *Why:* Automated headless crash triage provides instant root-cause diagnostics directly to autonomous self-healing coding agents.

### Domain: Decouple draft worker and target verifier over lockless ring buffer to overlap computation for >3.2x speedup. (1 tasks)
- **AGY-2538**: Asynchronous staged speculative pipelining engine and lockless queue in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes asynchronous staged speculative pipelining across compute devices at >3.2x speedup.
  - *Why:* Speculative pipelining completely hides draft model compute latency by overlapping drafting and target verification across devices.

### Domain: Deduplicate crash stack traces and log minimal C reproducers into PostgreSQL. (1 tasks)
- **AGY-2156**: Automated fuzz crash deduplication and PostgreSQL bug_tracker reproducer logger  (WS-BUILD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Crash triage parser deduplicates kernel crash logs and stores minimal reproducers in PostgreSQL.
  - *Why:* Automated triage provides actionable C reproducers directly to autonomous coding agents for self-healing.

### Domain: Deep codebase and memory tree searches navigate structured manifests to prevent cosine vector space collapse. (1 tasks)
- **AGY-1941**: Manifest-guided progressive-disclosure hierarchical retrieval engine  (WS-RAG | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Hierarchical tree queries return accurate context with reduced token overhead compared to flat exhaustive similarity searches.
  - *Why:* Single-vector cosine distance across thousands of dissimilar files suffers from semantic crowding and loses structural hierarchy.

### Domain: Deletes replicate, provably, across more than two peers. (1 tasks)
- **AGY-1918**: The CRDT convergence fix has no multi-peer test  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a multi-peer test with partition and reorder converges, and reverting the fix makes it fail.
  - *Why:* an eventually-consistent store that resurrects deleted records corrupts state silently and permanently.

### Domain: Deliberate high-impact system mutations across a 3-agent council and enforce 2/3 majority consensus. (1 tasks)
- **AGY-2251**: Multi-agent 3-peer council swarm and weighted Byzantine consensus engine in agent-pipe  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Council swarm evaluates proposals concurrently and enforces 2/3 majority consensus.
  - *Why:* Multi-agent deliberation eliminates single-model hallucinations and protects system integrity from adversarial prompts.

### Domain: Deploy 2+ active MDS ranks with dynamic subtree pinning for >50,000 metadata file operations/s. (1 tasks)
- **AGY-2337**: Active-Active CephFS MDS metadata clustering and dynamic subtree partitioner  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CephFS operates multi-active MDS daemons with dynamic subtree metadata partitioning.
  - *Why:* Active-Active MDS metadata clustering prevents CPU bottlenecks during large-scale concurrent agent builds.

### Domain: Deploy Hyprland with Quickshell desktop UI, direct DRM scanout, and GNOME apps/GDM session fallback. (1 tasks)
- **AGY-2375**: Hyprland + Quickshell native desktop environment and direct DRM scanout manager  (WS-APP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Hyprland and Quickshell launch as primary desktop with direct scanout and GNOME fallback.
  - *Why:* Hyprland + Quickshell provides sub-millisecond input response, ultra-smooth animations, and modular tiling.

### Domain: Deploy/Cat (2 tasks)
- **T-256**: CAT-01 -- Flatten + single-owner: mios-bootstrap owns cat/, delete C:\MiOS dup
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: One MiOS-Cat home exists at `cat\`; `C:\MiOS` contains no installer tree; a cross-repo `diff` finds no `medicat_installer` duplicate; the deepest path drops from `src\autounattend\medicat_installer\resources\ventoy\` to `cat\resources\ventoy\`.
- **T-259**: CAT-04 -- Fold the web one-liners (irm\
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `irm …/cat | iex` and `curl …/cat.sh | sh` reach an identical verb set; `cat install` means the same thing regardless of shell; the legacy scripts are thin shims rather than peer implementations.

### Domain: Deploy/Cat/Mirrors (1 tasks)
- **T-263**: CATREPO-04 -- Offline dnf/flatpak/pip mirrors on MiOS-Data + `cat update` self-refresh
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: An offline build or first boot resolves all dnf, flatpak and pip packages from USB; `cat update` refreshes the store and re-stamps `manifest.json` when online.

### Domain: Deploy/Cat/Models (1 tasks)
- **T-262**: CATREPO-03 -- Model embedding + `cat provision` (Law 12 offline, zero-network heavy lane)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A deployed host's heavy lane starts with ZERO network because `/usr/share/mios/vllm/model/config.json` is present; the GGUFs and AWQ weights are provisioned offline from MiOS-Data; every model's checksum is verified against a build-resolved value rather than a hardcoded one.

### Domain: Deploy/Cat/Repo (2 tasks)
- **T-260**: CATREPO-01 -- Small MiOS-Repo shadow-config partition (always) + kickstart path fix
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A small stick carries the shadow-config brain (mios.toml + mios.html + Portal + MiOS-Cat + a small repos-clone) and fits any USB; a fully offline bare-metal kickstart install succeeds sourcing from `MiOS-Repo/repos/`; the kickstart repo path matches what the stager writes.
- **T-261**: CATREPO-02 -- Separate MiOS-Data bulk store (512GB+): OCI tar + artifacts
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: On a 512 GB+ disk, MiOS-Data is created separately from MiOS-Repo and an offline `podman load` plus `bootc switch` from USB succeeds; on a smaller disk MiOS-Data is skipped and only the small MiOS-Repo is written.

### Domain: Deploy/Cat/SSOT (1 tasks)
- **T-258**: CAT-03 -- `[cat]` SSOT block + fix dangling drivepath/medicatver/cache_path reads
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: No MiOS-Cat value that has an SSOT home is hardcoded; the `[cat]` and `[colors]` reads resolve against `usr/share/mios/mios.toml`; the drift-check fails when a `[cat]` key is missing.

### Domain: Deploy/Windows (1 tasks)
- **T-254**: MDRIVE-01 -- Hyper-V Gen 2 .vhdx off M: + sovereign Ceph OSD on M
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A MiOS Gen 2 VM boots from `M:\MiOS-images\mios-0.3.0.vhdx` with a populated `/var/home`, `bootc status` reports healthy, and `curl http://localhost:8640/v1/models` answers from Windows; with the OSD vhdx and `[storage.cephfs].enable=true`, `findmnt /var/home` reports `type ceph` and survives a root-vhdx rebuild; `bootc upgrade` and `bootc rollback` both work in-guest.

### Domain: Desktop/BrowserLaunch (1 tasks)
- **T-1004**: BROWSER-01 -- build the launcher [browser] specifies, as a Rust static binary
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: opening a URL routes through the binary; adding a browser binary name to `[browser].family.<f>` makes the launcher recognise it with no code change -- proved by planting a name in a COPY of the SSOT and observing the resolution change; `[browser]` leaves the unconsumed register because it is read, not because a predicate moved.

### Domain: Desktop/DMABUFStream (1 tasks)
- **T-846**: Zero-copy DRM DMA-BUF frame capture and hardware encoder pipeline in mios-dmabuf-stream
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Desktop streamer captures DMA-BUF frames and encodes 60fps video directly on GPU silicon.

### Domain: Desktop/DMABUFTest (1 tasks)
- **T-847**: Automated 60fps 4K WebRTC streaming latency (<16ms) and zero-copy DMA-BUF test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates 60fps frame rates, sub-16ms streaming latency, and zero-copy GPU pipeline execution.

### Domain: Desktop/HyprlandQuickshell (1 tasks)
- **T-777**: Hyprland + Quickshell native desktop environment and direct DRM scanout manager
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Hyprland and Quickshell launch as primary desktop with direct scanout and GNOME fallback.

### Domain: Desktop/HyprlandTest (1 tasks)
- **T-779**: Automated Hyprland direct scanout (<1ms latency) and Living Wallpaper render test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates Hyprland direct scanout, Quickshell initialization, and low-power living wallpaper rendering.

### Domain: Desktop/WebRTCStream (1 tasks)
- **T-788**: Hardware-accelerated PipeWire WebRTC desktop video streamer in mios-screen-stream
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Screen streamer encodes PipeWire DMA-BUF frames on GPU hardware and streams over WebRTC.

### Domain: Desktop/WebRTCTest (1 tasks)
- **T-789**: Automated 4K 60FPS WebRTC desktop stream latency (<30ms) and encoder test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates hardware-accelerated WebRTC streaming, 60 FPS delivery, and low CPU load.

### Domain: Detect CPU SIMD extensions (AVX-512 VNNI, AMX TMUL, Neon) and configure tiled integer dot-product kernels. (1 tasks)
- **AGY-2382**: Hardware-calibrated CPU vectorized GEMM auto-tuner in mios-cpu-gemm  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CPU inference engine auto-tunes SIMD vector kernels and executes cache-tiled matrix dot products.
  - *Why:* Hardware-tuned SIMD vectorization unlocks fast, responsive local AI inference on systems lacking discrete GPUs.

### Domain: Detect GPU compute capability and dispatch pre-compiled architecture-tuned FlashAttention-3 and CUTLASS kernels. (1 tasks)
- **AGY-2247**: GPU compute capability detector and FlashAttention-3 / CUTLASS kernel dispatcher  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Kernel dispatcher detects GPU architecture and loads optimal Tensor Core GEMM kernels dynamically.
  - *Why:* Architecture-specific Tensor Core kernels maximize token generation throughput and minimize inference energy consumption.

### Domain: Detect PCIe link training degradation (e.g. x16 dropping to x1) and emit diagnostic alerts. (1 tasks)
- **AGY-2162**: PCIe link width degradation detector and hardware anomaly alert test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Link width detector catches degraded PCIe buses and alerts the operator automatically.
  - *Why:* Catching PCIe link width training errors prevents silent 90%+ bandwidth drops on GPU inference.

### Domain: Detect and repair corrupted database pages and indices automatically after sudden power outages. (1 tasks)
- **AGY-2005**: Database corruption detector and automated repair script for SQLite and PostgreSQL stores  (WS-DURA | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Database doctor detects corrupted pages and restores operational integrity automatically on boot.
  - *Why:* Abrupt power cuts or disk hardware glitches can corrupt database b-trees and halt system startup.

### Domain: Detect anomalous network connection patterns and log security events into PostgreSQL. (1 tasks)
- **AGY-2110**: Jensen-Shannon divergence anomaly alarm and PostgreSQL threat_events vector sink  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Anomaly detector flags abnormal network traffic shifts and stores threat vectors in PostgreSQL.
  - *Why:* Statistical anomaly detection identifies stealthy lateral movement and beaconing without fragile signature rules.

### Domain: Detect external GPU hotplug events and trigger automated driver binding and CDI updates. (1 tasks)
- **AGY-2093**: Udev hotplug handler for dynamic Thunderbolt/USB4 eGPU and PCIe accelerator re-enumeration  (WS-VFIO | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Udev rules detect hotplugged GPUs and trigger automated provisioning immediately.
  - *Why:* External eGPUs allow mobile laptops and modular workstations to dynamically expand AI compute capacity.

### Domain: Detect failed OSDs, mark out after 5min grace, and throttle backfill to 30% link bandwidth. (1 tasks)
- **AGY-2327**: Bandwidth-throttled Ceph self-healing daemon and PG rebalance orchestrator  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Ceph self-healing daemon rebalances degraded PGs at throttled speeds without violating client SLAs.
  - *Why:* Throttled automated self-healing restores cluster redundancy without degrading active agent workloads.

### Domain: Detect on-screen password/sensitive fields via ATSPI and blur matching screen coordinates on captured frames. (1 tasks)
- **AGY-2137**: ATSPI accessibility tree sensitive widget coordinate detector and Wayland frame blur filter  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Vision redaction filter blurs all ATSPI-reported password fields on captured screen frames.
  - *Why:* Visual privacy redaction prevents on-screen user credentials from leaking into agent prompt context or logs.

### Domain: Diffuse outlier weights via Fast Hadamard Transforms and quantize to 8D E8 lattice codebooks at 2 bits/weight. (1 tasks)
- **AGY-2478**: QuIP# randomized Fast Hadamard Transform engine and E8 lattice dispatcher in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine loads QuIP# 2-bit models and executes fused FHT-GEMM kernels on Tensor Cores.
  - *Why:* QuIP# randomized Hadamard incoherence enables 2-bit quantization without the catastrophic outlier degradation of scalar rounding.

### Domain: Discover CPU/NUMA topology on boot across Intel, AMD, ARM and partition performance/efficiency cores dynamically. (1 tasks)
- **AGY-2255**: Vendor-agnostic boot-time CPU topology discovery and dynamic NUMA/core partition allocator  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CPU topology allocator discovers core layouts on boot and partitions systemd slices dynamically.
  - *Why:* Vendor-agnostic core partitioning guarantees jitter-free real-time audio and microVM performance across any CPU architecture.

### Domain: Discover local MiOS nodes automatically on LAN subnets via mDNS/DNS-SD and initiate secure WireGuard mesh peering. (1 tasks)
- **AGY-2185**: Zero-configuration mDNS/DNS-SD peer discovery and automated WireGuard peering daemon  (WS-NET | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Peer discovery daemon locates local nodes and establishes encrypted mesh tunnels automatically.
  - *Why:* Zero-configuration discovery enables seamless plug-and-play bare-metal cluster expansion.

### Domain: Discover nearby MiOS nodes using Bluetooth Low Energy (BLE) advertisements when Wi-Fi is unconfigured. (1 tasks)
- **AGY-1993**: BLE beaconing for offline local mesh bootstrap  (WS-NODE | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: BLE discovery enables zero-touch initial network provisioning for headless edge blades.
  - *Why:* Headless edge nodes without Ethernet ports need an out-of-band discovery mechanism for initial onboarding.

### Domain: Distill intermediate agent scratchpads into summary vectors and execute non-blocking REINDEX CONCURRENTLY. (1 tasks)
- **AGY-2373**: Semantic memory distillation daemon and non-blocking vector reindexer in mios-mem-compact  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Memory compaction daemon distills scratchpads and reindexes vector tables non-blockingly.
  - *Why:* Periodic distillation prevents memory bloat while preserving key semantic insights and sub-5ms query latency.

### Domain: Distill successful complex tool call sequences into reusable SKILL.md modules. (1 tasks)
- **AGY-1974**: Automatic skill synthesis and extraction from successful multi-step task execution traces  (WS-ORCH | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: High-performing execution traces are automatically converted into documented, reusable skills.
  - *Why:* Self-improving operating systems must learn new workflows from successful operations without manual documentation authoring.

### Domain: Distribute AI inference and agent tasks dynamically across all available and relevant cluster nodes. (1 tasks)
- **AGY-2135**: Multi-node dynamic AI workload partitioner and capability-aware task router  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Mesh distributor partitions and routes subtasks across relevant cluster nodes dynamically.
  - *Why:* Distributing AI workloads maximizes cluster throughput and parallelizes multi-agent workflows.

### Domain: Distribute queued subtasks dynamically across available edge nodes using work-stealing. (1 tasks)
- **AGY-1990**: Task offloading priority queue in mios-node with work-stealing scheduler  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Work-stealing scheduler balances task queues across heterogeneous nodes automatically.
  - *Why:* Static task placement leads to unbalanced clusters where fast nodes sit idle while slow nodes are overloaded.

### Domain: Distributed edge nodes maintain convergent state across network partitions using LWW-Element-Set and Vector Clocks. (1 tasks)
- **AGY-1946**: Conflict-free replicated data type (CRDT) engine for edge node state synchronization  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Network partitions heal automatically with deterministic CRDT state convergence across all participating nodes.
  - *Why:* Edge mesh topologies experience frequent intermittent disconnects and require lock-free, eventually consistent replication.

### Domain: Distributed micro-nodes communicate over a strict, deterministic 16-byte binary wire header with CRC32 integrity. (1 tasks)
- **AGY-1944**: 16-byte fixed binary wire protocol framing in mios-node runtime  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The `mios-node` binary frame codec encodes and decodes all seven message opcodes with full CRC32 validation.
  - *Why:* A lightweight, fixed-size binary header minimizes framing overhead and CPU latency on embedded edge nodes and microVMs.

### Domain: Docs (1 tasks)
- **T-1103**: CONSOL -- The three standing drift violations
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Narrative harvested, doc refs decided, drift-gate green.

### Domain: Docs/Governance (1 tasks)
- **T-1014**: ADRNS-01 -- docs/adr/ is a second ADR namespace with colliding numbers, outside the index and the template
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: every ADR in the tree is under the canonical directory, carries a unique ordinal, passes `check_template_conformance`, and appears in the regenerated `ADR.md`; a planted ADR-shaped file outside the canonical directory fails a check.

### Domain: Docs/Pipeline (1 tasks)
- **T-1074**: DOCREF-01 -- 120 of check_doc_refs_resolve's 124 stale references are FORWARD refs to components and chapters that were never built, not broken links; the check cannot be drained by fixing references
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: each of the 120 is resolved by a decision recorded per reference -- the component is built, the chapter is written, or the header is retired with its intent moved into the backlog -- and `[docs].max_stale_doc_refs` falls to the surviving count. Never by repointing a reference at a document that does not describe it.

### Domain: Docs/Refs (1 tasks)
- **T-1017**: GHOSTSTAGE-01 -- 24 modules cite 22 automation stages that do not exist, at numbers other stages now occupy
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: every `automation/NN-*.sh` cited by a module header either exists or has been removed from the header because the module's fate is settled; `check_doc_refs_resolve`'s count falls by the corresponding amount.

### Domain: Docs/SSOT (1 tasks)
- **T-332**: MINI-04 -- One architecture, two documents, two names, both shipped (207 of 224 lines identical)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: one canonical copy; the other is a pointer; the diagram label is a decision rather than a leftover; and a gate catches the next near-duplicate pair -- `docs/design/dedup-campaign.md` already exists, so this belongs to that campaign rather than to a one-off deletion here.

### Domain: Drop-ins are declared the same way units are. (1 tasks)
- **AGY-1844**: Drop-in directories are projected inconsistently  (WS-UNITS | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every drop-in in the tree is declared in the same form and renders to the right path.
  - *Why:* an inconsistent declaration form is a gap in a projection that claims to be total.

### Domain: Durability/Memory (1 tasks)
- **T-220**: STD26-04 -- Durable event-sourcing over swarm/DAG + Memory-Block
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a DAG run killed mid-execution resumes from the event history on restart, and recall/write paths go through Memory-Block with no raw-row access left in the callers.

### Domain: Dynamically adapt PipeWire daemon clock rate to source audio (44.1k-192k) for bit-perfect playback. (1 tasks)
- **AGY-2301**: Dynamic PipeWire bit-perfect sample rate adapter and hardware DAC pass-through manager  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: PipeWire adapts sample rates dynamically to deliver bit-perfect audio to capable DACs.
  - *Why:* Dynamic sample rate switching provides bit-perfect audiophile fidelity while preserving system-wide audio multiplexing.

### Domain: Dynamically evaluate each peer agent's contribution to council decisions and update peer reputation scores. (1 tasks)
- **AGY-1942**: IntrospecLOO marginal contribution scoring for swarm and council agents  (WS-ORCH | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Completed council sessions record individual agent contribution deltas into `peer_reputation` automatically.
  - *Why:* Quantifying agent contribution enables the orchestrator to prune hallucinating or unhelpful models from future deliberation rounds.

### Domain: Dynamically select optimal model quantization formats based on reported node hardware capabilities. (1 tasks)
- **AGY-2079**: Dynamic Node Capability Profiler & Model Format Selector in agent-pipe  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Model allocation engine selects optimal quantization formats dynamically based on live node telemetry.
  - *Why:* Heterogeneous cluster nodes require adaptive model format selection to maximize throughput and prevent OOM errors.

### Domain: Dynamically switch system operational profile between Seat (Wayland/GNOME/ASR) and Blade (k3s/Ceph/RPC) with 0 VRAM leaks. (1 tasks)
- **AGY-2568**: Dual-mode dynamic topology switcher (Seat UI vs Headless Blade) in mios-node  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Topology switcher transitions between seat and blade operational profiles with zero resource leaks.
  - *Why:* Dual-topology support allows the same immutable image to serve as a local desktop workstation or a remote compute blade dynamically.

### Domain: E-01 Compiled native tier -- brings the untargeted materialize cluster under typed models and the shared dispatcher. (1 tasks)
- **AGY-1103**: Port/consolidate the materialize-*.py DB round-trip build-context projectors  (WS-DEBT | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The materialize family shares typed models and the shared resolver; the DB->TOML and DB->/ctx round-trip checks 31/32 are green; goldens are committed; `just drift-gate` green.
  - *Why:* Four drift-gated projectors with subtle round-trip semantics sit outside every port and hardening task, so a change to the DB schema or SSOT shape can break the build context with no typed model to catch it.

### Domain: E-01 Compiled native tier -- closes the coverage hole where the highest-traffic SSOT projector has no port assignment. (1 tasks)
- **AGY-1102**: Port generate-ai-manifest.py (verb-catalog projector, gate check 8) to Rust with a byte-parity golden  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The Rust binary emits a byte-identical ai/v1 verb manifest against the golden; check 8's `--check` is green through the dispatcher; the `.py` is demoted and then deleted; `cargo test` and `just drift-gate` green.
  - *Why:* The verb catalog is core AI-plane contract surface and the most-exercised projector in the gate, so leaving it as the one un-hardened interpreted script undermines the parity story the other ports establish.

### Domain: E-01 Compiled native tier -- collapses the long tail of tiny generate-*.py scripts into one typed, audited compiled projector. (1 tasks)
- **AGY-1089**: Batch-port four small SSOT projectors (cargo-manifests, ipa-enroll-env, cockpit-conf, blade-dropins) into one Rust codegen crate  (WS-DEBT | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: All four artifacts are emitted byte-identical to their `.py` sources against goldens; each subcommand's `--check` matches the old drift semantics; invocation and drift sites call the Rust crate with per-tool `.py` fallback; `cargo test` and `just drift-gate` green; all four `.py` files deleted with explicit staging.
  - *Why:* The loose-script count lives in this long tail, and porting each tiny script as its own crate would pay four crates' overhead for four small jobs — batching is the only economical way to retire them while keeping each cutover independently gated.

### Domain: E-01 Compiled native tier -- finishes one strangler-fig lane so a libexec-tier bash/Python generator is replaced by a compiled binary only after byte-parity is proven. (1 tasks)
- **AGY-1410**: Cut check_names_registry over to the compiled generate-names-registry and demote the Python generator to a thin exec shim  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: check_names_registry validates against the compiled generator and is green on the full tree with the Python script out of the hot path; a negative test that stales `names.generated.txt` still fails the gate.
  - *Why:* Two live implementations of the registry generator can drift apart the moment either side is edited, and the drift-gate would keep validating the slower, unhardened one.

### Domain: E-01 Compiled native tier -- keeps the strangler-fig parallel-run window honest so bash and Rust cannot silently diverge mid-port. (1 tasks)
- **AGY-1544**: Add check_shim_delegates: a demoted bash verb must be a thin shim that execs its Rust binary  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A verb listed as ported that still carries business logic fails the check; a ported verb whose crate is not a workspace member fails; a negative test exists.
  - *Why:* A "ported" verb whose bash still holds real logic means two divergent implementations of the same behavior ship in the image, with no signal for which one ran.

### Domain: E-01 Compiled native tier -- makes every compiled verb report SSOT errors identically, as compiler-grade diagnostics. (1 tasks)
- **AGY-1093**: Give the migrated Rust projectors a miette/thiserror typed-diagnostic error surface pointing at mios.toml spans  (WS-DEBT | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Each ported projector depends on `mios-diagnostics` and returns `miette::Result`; a malformed `[security.sigstore]` or `[pods]` value produces a spanned diagnostic naming the offending `mios.toml` line; a trycmd fixture pins the diagnostic format; `cargo test` and `just drift-gate` green.
  - *Why:* Without a shared span-mapper each ported tool invents its own error text, and an operator who mistypes a port value gets an opaque traceback instead of "this value is invalid, here, try X" — losing the main UX dividend of compiling the tier.

### Domain: E-01 Compiled native tier -- makes rollback a first-class deliverable of the strangler migration so no compiled slice can wedge the bake. (1 tasks)
- **AGY-1411**: Add an inert `[migration]` toggle table to mios.toml so every Rust cutover has a one-value rollback  (WS-GUP | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the `[migration]` table is present in both repos with safe defaults; `MIOS_MIGRATION_*` keys appear in `env-baseline.txt` under a deliberate baseline bump; check_migration_toggles is green and a flipped-default negative test fails.
  - *Why:* Without a declared rollback substrate, every later compiled slice is a one-way cutover -- a regression in the resolver or version checker means reverting commits mid-campaign while the publish bake stays red.

### Domain: E-01 Compiled native tier -- one compiled generator owns every systemd artifact instead of a Rust and a Python one running side by side. (1 tasks)
- **AGY-1354**: Subsume `generate-pod-quadlets.py` into mios-unit-gen behind a differential-parity harness  (WS-SYSTEMD | P1 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-unit-gen` emits every file under `usr/share/containers/systemd` byte-identical to `generate-pod-quadlets.py` across the full SSOT; the Python generator is a shim or deleted and `33-generate-quadlets.sh` calls the binary; `cargo test`, the differential harness and the drift-gate are green.
  - *Why:* Leaving the already-SSOT-generated container side un-converged ships TWO unit generators with two rendering semantics — and the quadlet tree the existing golden task omits has no parity net at all.

### Domain: E-01 Compiled native tier -- removes TD-3's hand-rolled-parsing risk from the code path that decides what actually gets installed. (1 tasks)
- **AGY-985**: Port the packages.sh awk resolver library to `miosd packages` behind the shim helpers  (WS-LANG-AUTO | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd packages list/enabled` returns identical package sets and enable state to the awk helpers across all sections (differential test); `install_packages*` call the binary with awk fallback; dnf stays shell; the parity test is green.
  - *Why:* A mis-parse in the awk cascade silently DROPS a package, so the image is missing software with no error anywhere in the build log.

### Domain: E-01 Compiled native tier -- removes the last duplicated copy of resolver logic, so the compiled resolver is the only implementation. (1 tasks)
- **AGY-1577**: Delete the ~200-line Python heredoc from both `userenv.sh` twins once the native resolver is proven  (WS-PORTFLOAT | P2 | M) **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: neither twin contains a heredoc; the twin-equivalence checks are retired or repointed at the binary; a booted image resolves an identical `MIOS_*` set before and after the change.
  - *Why:* the heredoc is the third live copy of the resolver and the sole reason the twin-parity gates exist, so every resolver change is currently a three-place edit.

### Domain: E-01 Compiled native tier -- replaces the highest-traffic shell string-munging surface in the tree with a compiled, type-checked resolver core. (1 tasks)
- **AGY-1412**: Scaffold the mios-resolve crate: a typed layered resolver whose `--emit-env` matches env-baseline exactly  (WS-GUP | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo run -p mios-resolve -- --emit-env` under `HOME=/nonexistent` with vendor-only layers diffs empty against `env-baseline.txt`; the crate builds clean under `clippy -D warnings`; the toggle stays off so nothing is rerouted.
  - *Why:* Today a shell/Python resolver silently yields a wrong string on an edge-case layer merge and that value flows straight into a Quadlet -- there is no type system anywhere between mios.toml and a running container.

### Domain: E-01 Compiled native tier -- retires two loose Python projectors into the compiled tier and proves the batch-port pattern. (1 tasks)
- **AGY-1088**: Port generate-gate-index.py and generate-pipeline-index.py to a single Rust index generator with parity goldens  (WS-DEBT | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Both indexes are emitted byte-identical to the `.py` output across the captured goldens; `--check` drift behavior matches; the drift-checks invoke the Rust binary with `.py` fallback; `cargo test` and `just drift-gate` are green; both `.py` files are deleted with explicit staging.
  - *Why:* Two near-identical small projectors staying in interpreted, untested Python keeps the loose-script count high and leaves the batch-port technique unproven for the larger projector fleet behind it.

### Domain: E-01 Compiled native tier -- supplies the characterization harness that must prove byte-parity BEFORE any shell resolver path is deleted. (1 tasks)
- **AGY-1413**: Golden trycmd/insta snapshots pinning mios-resolve to the shell oracle across all four layer scenarios  (WS-GUP | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p mios-resolve` runs all four scenario snapshots green, and deliberately altering one fixture value flips a snapshot -- proving the tests bite rather than rubber-stamp.
  - *Why:* Without recorded goldens the compiled resolver can drift from the shell result in a scenario nobody hand-wrote an expectation for, and the divergence surfaces as a broken service at first boot.

### Domain: E-01 Compiled native tier -- the actual strangler cutover: old and new resolvers coexist behind one SSOT value, provably lossless in both states. (1 tasks)
- **AGY-1415**: Route userenv.sh through mios-resolve behind the toggle, keeping the Python heredoc as the degrade-open fallback  (WS-GUP | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: with `use_rust_resolver=false` the resolved env is byte-identical to today; with `=true` both `just` and `mios-env-snapshot` reproduce `env-baseline.txt`; `check_userenv_parity` stays green and the lossless gate passes in both toggle states.
  - *Why:* Until the compiled resolver is actually on the path it is dead code -- and a cutover without a toggle means the only rollback for a bad resolve is a revert-and-rebuild while every service reads wrong values.

### Domain: E-01 Compiled native tier -- the campaign actually reduces the codebase, leaving one compiled generator instead of scattered shell. (1 tasks)
- **AGY-1346**: Complete the strangler cut: delete the bash unit-authoring path once every family is gate-green  (WS-SYSTEMD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: No shell hand-authors `usr/lib/systemd/system/*` content; the build path is `mios-unit-gen` only with the Python reference reachable via the toggle; `generate-pod-quadlets.py` is untouched; full drift-gate + golden + proptest green; the merge is visible in the git graph.
  - *Why:* A strangler port that never deletes the legacy slice leaves two authoring paths forever — double maintenance, and the next contributor edits the shell one because it is still there.

### Domain: E-01 Compiled native tier -- the operator-facing half of the compiled resolver: config failures become compiler-grade, span-anchored reports. (1 tasks)
- **AGY-1416**: Give mios-resolve miette/thiserror diagnostics that point at the offending mios.toml span  (WS-GUP | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: feeding mios-resolve a mios.toml with a bad `[ports]` value or malformed `[colors]` hex prints a miette diagnostic with the correct highlighted span; internal errors are typed thiserror variants; `clippy -D warnings` is clean.
  - *Why:* Today a mistyped SSOT value produces an opaque bash failure string or, worse, a silent empty default -- the operator gets no line number and the gates get no matchable error variant.

### Domain: E-01 Compiled native tier -- the parity oracle that lets fragile untested bash be refactored without silently changing generated bytes. (1 tasks)
- **AGY-963**: Record golden masters (trycmd + insta) of current build-phase output before any phase is ported  (WS-LANG-AUTO | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p mios-build` runs the golden suite; each snapshot matches the byte output of the corresponding current bash/python phase on the fixture; `cargo insta test` is green; a deliberately divergent port fails loudly with a diff.
  - *Why:* Without a recorded oracle, every port is a guess — a one-byte difference in a rendered Quadlet or kargs file ships as a boot/runtime regression that no test can catch.

### Domain: E-01 Compiled native tier -- the strangler-fig port carries a one-flip rollback so the bake never goes red waiting on a regressed family. (1 tasks)
- **AGY-1343**: Add an oxidizr-style `[migration]` toggle for per-family Rust-vs-Python unit generation  (WS-SYSTEMD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Setting `use_rust_unit_gen=false` regenerates units via the Python reference with byte-identical output; a per-family flip works independently; the default flips to Rust only for gate-green families; both repos' `mios.toml` agree.
  - *Why:* Without a rollback switch, any regression in a single unit family becomes an emergency revert of the whole compiled generator mid-campaign — the exact failure mode the oxidizr playbook exists to avoid.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and libexec tool fleet -- gives the strangler-fig migration a directional gate so it cannot stall or backslide. (1 tasks)
- **AGY-1542**: Add check_migration_ratchet: bash-script count may only fall, cargo-test count may only rise  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Adding a new non-shim bash script fails the ratchet; deleting a cargo test fails it; the baseline is in `mios.toml [migration]` and mirrored in mios-bootstrap.git; a negative test exists.
  - *Why:* Nothing today stops net-new bash from landing beside the Rust port, so the 121 automation scripts and 144 libexec tools can grow faster than they are retired.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- Secure-Boot state parsing stops being sed/grep string-munging. (1 tasks)
- **AGY-1497**: Port enroll-mok.sh's `status_probe` to a compiled `mios-mok --status` with differential parity  (WS-SBOM | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-mok --status` emits the identical state string as the bash probe across the fixtures; `enroll-mok.sh` delegates to it with a bash fallback; differential/trycmd parity green; clippy -Dwarnings clean; `just drift-gate` green; both repos carry it.
  - *Why:* Enrollment decisions branch on a state string produced by fragile text pipelines -- a formatting change in `mokutil` output silently misclassifies Secure Boot state and the wrong enrollment path runs.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- a recorded parity oracle exists before a single security projector is rewritten. (1 tasks)
- **AGY-1067**: Capture every SSOT `--check` projector's stdout/stderr/exit in a trycmd golden-master harness before any Rust port  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p mios-projector-golden` passes against committed fixtures for >=6 projectors; snapshots include exit code plus full stdout/stderr; the harness runs inside `just drift-gate`; fixtures are byte-frozen with an accept workflow documented.
  - *Why:* Without a recorded oracle, a Rust rewrite of a projector that emits `policy.json` or the kernel cmdline can diverge byte-wise and nobody will notice until a boot-integrity control silently stops enforcing.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- a security-boundary projection is generated by typed compiled code that validates its inputs. (1 tasks)
- **AGY-1082**: Port generate-egress-firewall.py to Rust with typed SSOT input and golden parity  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust binary's output is byte-identical to the `.py` across the goldens; an invalid CIDR or port yields a miette diagnostic instead of a malformed rule; `check_egress_firewall` calls Rust with `.py` fallback; `cargo test` and `just drift-gate` green; `.py` demoted or deleted with explicit staging.
  - *Why:* A typo'd CIDR in SSOT currently passes straight through string assembly into a live egress rule -- the firewall silently allows or blocks the wrong network with nothing rejecting the bad value.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- a typed serializer for the one file three different parsers must agree on. (1 tasks)
- **AGY-1020**: Port system-sync-env.sh to a mios-toml-core install.env writer with proven byte-parity  (WS-LANGX | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-toml-core sync-env --dry-run` is byte-identical to `system-sync-env.sh --dry-run` for the vendor SSOT; the R4 self-test invariants (no `="`, no secrets, sources clean under `set -u`) hold in Rust; the install-env-safe drift-check is green; the bash generator body no longer exists, leaving only the shim.
  - *Why:* install.env is consumed by three parsers with incompatible quoting rules; the shell string-munging that builds it is the class that produced the historic `$6: unbound variable` service cascade, and it can leak a secret into a world-readable env file.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- bring 399 lines of hand-emitted YAML under the render-from-SSOT pattern with real coverage. (1 tasks)
- **AGY-1002**: Port the GPU CDI family (23-27) to `miosd render-cdi` driven from SSOT  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd render-cdi` emits byte-identical CDI YAML and passthrough config against golden fixtures, the five phases are shims, a GPU-less build still succeeds, and `cargo test` plus the drift-gate are green.
  - *Why:* The CDI family hand-writes device specs from SSOT-adjacent data with zero test coverage, so a malformed spec surfaces only when a GPU container fails to start on real hardware — the slowest possible feedback loop.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- collapse an inline-python config read plus a separate python verdict gate into a single typed compliance path. (1 tasks)
- **AGY-991**: Port the oscap severity gate (86-oscap-compliance.sh + mios-oscap-gate) into one `miosd compliance-gate`  (WS-LANG-AUTO | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd compliance-gate` reproduces the disabled no-op and, on a fixture ARF, the same at/above-severity verdict as mios-oscap-gate, the datastream resolution matches, 86 is a thin shim invoking oscap plus the binary, and the golden tests are green.
  - *Why:* Compliance posture is currently decided by an inline python tomllib blob in a shell phase plus a second python parser — two fragile pieces that can disagree about whether a build is compliant, and neither is testable without a full oscap run.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- collapses a coupled bash cluster that builds `flatpak` commands by string interpolation into one audited crate. (1 tasks)
- **AGY-1045**: Port the flatpaks-manage.sh + flatpak-launch cluster into one Rust flatpak subcommand set  (WS-LANGX | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust flatpak tool issues byte-identical `flatpak` argv and override sets vs the bash family on fixtures; `mios flatpaks` is unchanged; golden tests green; the flatpak cluster's contribution to the bash-tool ratchet drops accordingly.
  - *Why:* Six scripts each build `flatpak` argv by interpolation, so app ids and override strings are duplicated and unquoted across the cluster, and every one of them counts against the 145-tool bash surface.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- collapses ~1.8k lines of /sys-munging bash on the MiOS-Metal passthrough path into one audited compiled subcommand. (1 tasks)
- **AGY-1041**: Port the vfio-config / vfio-check / vfio-toggle family to a `miosd vfio` subcommand set  (WS-LANGX | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd vfio check` emits a byte-identical binding/IOMMU report vs `vfio-check.sh` on a `/sys` fixture; config/toggle side effects match; the three verbs behave unchanged for the operator; golden tests green; the ratchet is decremented by 3.
  - *Why:* GPU passthrough binding is decided by fragile text-parsing of `/sys`; a misparse silently binds the wrong device or leaves the host GPU claimed, and this sits on the split-plane critical path.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- complete the render family so no ad-hoc bash config emitter remains and the phase ratchet can reach zero. (1 tasks)
- **AGY-1010**: Sweep the last small SSOT-to-config emitters (46-sshd-port, 48-dropin-fanout, 12-hostname, 10-locale-theme) into `miosd render-*`  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: all four phases emit byte-identical config via `miosd render-*`, they are shims behind the toggle, no bash emitter remains in the render family, and `cargo test` plus the drift-gate are green.
  - *Why:* The headline render ports leave a tail of small emitters in bash, and while any remain the bash-phase count ratchet cannot be driven down and "every projection is compiled" stays a claim rather than a checked fact.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- consolidates the read-only diagnostics reporters onto the one resolver that already owns the MIOS_* projection. (1 tasks)
- **AGY-1043**: Port system-env.sh and system-summary.sh to `miosd env` / `miosd summary` subcommands  (WS-LANGX | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd env` and `miosd summary` produce byte-identical output vs their bash predecessors on a fixture; the two verbs are unchanged; golden tests green; the ratchet is decremented by 2.
  - *Why:* Both re-implement env-inspection logic that `mios-toml-core` already owns, so the layered resolution shown to an operator can disagree with the resolver the system actually uses.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- eliminates the single largest loose-script liability in usr/libexec/mios. (1 tasks)
- **AGY-1042**: Port capability-audit.sh (2632 lines, the largest bash tool) to a `miosd assess` subcommand  (WS-LANGX | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd assess` reproduces `capability-audit.sh`'s full report section-for-section on a fixture host under a golden snapshot; `mios assess` is unchanged for the operator; the 2632-line bash file is a shim; the ratchet is decremented.
  - *Why:* 2632 untested lines of capability-probing shell decide what MiOS believes the hardware can do; a parse regression there silently mis-provisions a host and nothing catches it.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- establish the reusable idempotent-unit template on the smallest firstboot before the big ones. (1 tasks)
- **AGY-1030**: Port hermes-worker-firstboot to a small idempotent Rust unit binary (the firstboot port template)  (WS-LANGX | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust binary reproduces hermes-worker-firstboot's side effects and exit code idempotently (a second run no-ops); the `.service` invokes it unchanged; degrade-open is verified (a non-zero step never aborts boot); golden test green; ratchet decremented.
  - *Why:* Without an audited template proven on a 43-line unit, each of the larger firstboot ports (696 and 1916 lines) reinvents idempotence and degrade-open, and a mistake there wedges boot on real hardware.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- establishes the pyo3 strangler + differential-parity pattern the rest of the port campaign copies. (1 tasks)
- **AGY-1114**: Port jsonsalvage `loads_lenient` to a pyo3 crate proven by differential proptest  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test` differential proptest shows Rust == Python for all generated inputs, the toggle switches implementations at runtime, `test_mios_jsonsalvage.py` is green under BOTH toggle states, and the crate is a workspace member staged explicitly.
  - *Why:* Without a proven lowest-risk first slice, every later Rust port is an unbounded rewrite with no parity method behind it.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- give every subsequent phase port native primitives so it never has to shell back into bash. (1 tasks)
- **AGY-1000**: Port the shared phase-runtime libs (common.sh, masking.sh, root-merge.sh) into mios-build modules, keeping bash shims  (WS-LANG-AUTO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: all three libs have native equivalents, the `test_masking.sh` cases pass as cargo tests, native log/step/ok output is byte-identical to the bash prefixes, the shims remain source-compatible for un-ported phases, and the drift-gate is green.
  - *Why:* These are the primitives every phase calls; port them late and each phase port re-shells into bash for logging and redaction, leaving multiple secret-masking implementations where exactly one should exist and be audited.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- gives the "/ IS $ROOT" self-updating-tree design compiled guarantees on the code that mutates the live system root. (1 tasks)
- **AGY-1060**: Port the root-as-git-tree machinery (git-root-init.sh, mios-sync-to-root, verify-root.sh) to a `miosd root` subcommand  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the mutable-vs-immutable gate is preserved and covered by a test that fails if sync is attempted against an immutable root; `miosd root verify` exits non-zero on an integrity mismatch; the units invoke miosd; characterization tests pass; gate green.
  - *Why:* A gating regression in `mios-sync-to-root` would write onto an immutable bootc root, and a soft-failing `verify-root` lets a tampered composefs boot unnoticed -- both under the code that underpins the self-updating tree.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- harden the release-topology plane where admin credentials and tokens are handled. (1 tasks)
- **AGY-1033**: Port forge-firstboot.sh to Rust with explicit secret sourcing from secrets.env  (WS-LANGX | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust binary provisions Forgejo idempotently (second run no-ops) with the same observable API sequence and exit code as the bash against a mock; secrets are read only from `secrets.env`; golden test green; ratchet decremented.
  - *Why:* Forge provisioning handles admin credentials and API tokens in shell string context, where a mis-quoted value can leak into a process listing or a log — and Forgejo is a co-equal publisher in the release topology, so a half-provisioned forge breaks publishing parity.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- hardens the pre-sysinit namespace/device shell on the cross-platform WSL leg. (1 tasks)
- **AGY-1055**: Port the WSL early-boot bootstrap family (wsl-early, wsl-init, mios-wslg-env-import, wsl-theme-bridge.sh) to a `miosd wsl` subcommand  (WS-LANGX | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the `mios-wsl-*` units invoke the `miosd wsl` subcommands; characterization tests match the bash on mounts, device nodes, `wsl.conf` content and the subnet fix; drift-gate green.
  - *Why:* This runs before sysinit and is the least-tested provisioner class in the tree; a partial failure leaves podman and cockpit broken on the Windows leg with no diagnostic.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- let the compiled orchestrator own ordering and concurrency, which is the concrete payoff of moving build policy out of bash. (1 tasks)
- **AGY-992**: Declare a `[build.phases].deps` DAG in SSOT and run independent phases concurrently in `mios-build`  (WS-LANG-AUTO | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd build` runs the independent bake-builder phases concurrently, a fixture build's rootfs and phase logs match the sequential golden, fatal/non-fatal policy is honored from the registry, and wall time on the bake-builder band drops measurably.
  - *Why:* Every build pays the full serial cost of the five heaviest GPU/UI builders, and the ordering rules that would allow otherwise live nowhere a machine can read them — so the build stays slow and phase order stays an implicit property of filenames.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- lets ports land without converting soft-fail provisioners into boot blockers. (1 tasks)
- **AGY-1054**: Migrate the 70 systemd ExecStart references onto ported binaries with prefixes intact, gated by an ExecStart-resolves drift-check  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the drift-check fails on any dangling or non-executable ExecStart libexec path; all 70 units resolve after porting; ported units keep identical paths and `-`/`+` prefixes; gate green.
  - *Why:* A path rename or a dropped `-` prefix during a port silently turns a degrade-open provisioner into a boot-blocking one, and the tree has no gate today that even asserts an ExecStart target exists.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- make the hottest firstboot in the tree memory-safe without ever wedging a boot. (1 tasks)
- **AGY-1035**: Port mios-ai-firstboot to an idempotent sentinel-gated Rust provisioner (bash kept as fallback)  (WS-LANGX | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust provisioner writes the sentinel under the identical all-pieces-present condition, seeds the venv offline from the OCI image byte-for-byte, and returns 0 (degrade-open) on any partial failure exactly like the bash; the `.timer` re-fire no-ops once complete; golden fixtures green; parity confirmed before the shim body is deleted.
  - *Why:* This is where the operator-reported "outages / must deploy every time" failures lived — a premature sentinel write leaves the AI plane permanently half-provisioned because the timer never retries, and 696 lines of `set +eu` shell is the least verifiable place in the boot path.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- make the native/bash cutover reversible per phase so the port lands incrementally instead of as a big bang. (1 tasks)
- **AGY-1001**: Establish the strangler-fig control plane: a per-phase MIOS_NATIVE toggle plus a cutover-order ADR  (WS-LANG-AUTO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `MIOS_NATIVE=1` in CI runs every already-ported phase natively while `0` runs bash, both producing byte-identical images, the ADR and tracking table exist in both repos, and the drift-gate is green.
  - *Why:* Dozens of queued phase-port tasks have no agreed order and no A/B switch, so any single port that regresses the image can only be diagnosed by reverting the commit — and without the ADR the ports will land in an order that breaks their own dependencies.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- moves a security boundary into memory-safe compiled code with zero operator-visible change. (1 tasks)
- **AGY-1115**: Port mios_argval enum/synonym validation to a pyo3 crate with byte-identical reject messages  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the insta golden of reject messages matches byte-for-byte, the proptest differential is green, `test_mios_argval.py` passes under both toggle states, and the crate is in `members` and staged explicitly.
  - *Why:* Arg-enum validation stands between model output and the broker; leaving it in untyped Python keeps a security boundary in the least-hardened tier.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- moves the resolver from a crate that merely compiles to the code the product actually runs. (1 tasks)
- **AGY-1572**: Build and install the `mios-resolver` binary into the image and cut generation over to it behind a differential gate  (WS-PORTFLOAT | P1 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the binary is present in the baked image; the differential gate is green; a booted image demonstrably takes the native branch in `userenv.sh`.
  - *Why:* the entire WS-RESOLVER crate is inert today -- it compiles and passes its own tests while nothing in the shipped product ever calls it -- and AGY-1577 cannot start until it does.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- moves the single largest firstboot bash mass onto the compiled tier by porting its pure SSOT-projection slice first (strangler-fig), so no shell is deleted before byte-parity is proven. (1 tasks)
- **AGY-1036**: Extract the hermes config-YAML renderer out of the 1916-line mios-hermes-firstboot into a `mios-toml-core hermes-config` subcommand  (WS-LANGX | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-toml-core hermes-config` writes both config.yaml files byte-identical to the current bash for the vendor SSOT; the firstboot script calls it instead of the inline renderer; the remaining bash line count is measurably smaller; the golden test is green; the bash-tool ratchet is unaffected until the whole tool becomes a shim.
  - *Why:* 1916 lines of boot-critical bash re-derive AI config from SSOT on every boot with no test; a silent render bug there ships a broken Hermes config to every host, and the mass keeps growing while it stays in shell.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- no script is deleted until its exact current behavior is recorded and reproduced. (1 tasks)
- **AGY-1491**: Stand up a trycmd + insta golden-master harness as the parity oracle for every port  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test` runs trycmd+insta over fixtures encoding the exact current bash/python output; a deliberate output change fails the snapshot and is reviewable via `cargo insta review`; both repos carry it.
  - *Why:* Every port scheduled behind this one would otherwise be a rewrite with no oracle -- a silent behavior change in the cosign policy, the MOK probe or the compliance gate would ship undetected.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- one Cargo workspace with every crate a member, the precondition for `cargo build --workspace` in a single cached Containerfile stage. (1 tasks)
- **AGY-1012**: Repair the tools/native cargo workspace by adopting the 5 orphaned crates the drift-gate already builds  (WS-LANGX | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo build --workspace --manifest-path tools/native/Cargo.toml` and `cargo build -p mios-ssot-lint -p mios-aiplane-lint -p mios-bake-plan` both succeed from a clean checkout; the drift-gate steps referencing `target/release/mios-{ssot-lint,aiplane-lint,bake-plan}` find their binaries; `just drift-gate` green.
  - *Why:* Today `-p mios-ssot-lint` resolves against a workspace that excludes the crate — a latent break in the very governance tooling the campaign depends on, and a blocker for every later port that assumes one coherent workspace.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- one error surface every ported phase inherits, so the compiled tier is a UX upgrade over bash rather than a lateral move. (1 tasks)
- **AGY-996**: Land the shared thiserror/miette error model with mios.toml span diagnostics before the phase ports  (WS-LANG-AUTO | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: mios-config and mios-build expose thiserror enums wrapped by miette, a malformed mios.toml value produces a diagnostic highlighting the exact line/span with help text, miosd's main returns `miette::Result`, unit tests assert the diagnostic against a bad fixture, and builds are warning-clean.
  - *Why:* Every port that lands before this invents its own error strings, and retrofitting a shared model across a dozen crates later costs far more than defining it once — meanwhile operators keep getting bash-grade opaque messages from compiled code.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- one error/diagnostic foundation every port builds on instead of each reinventing one. (1 tasks)
- **AGY-1490**: Establish a shared `mios-diag` thiserror+miette crate for the migrated supply-chain verbs  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-diag` builds, exports a Result alias plus a span-carrying TOML-error helper, is a workspace member covered by the clippy/deny/audit gates, and is consumed by at least one ported verb; `cargo test` green; both repos carry it.
  - *Why:* Without a shared foundation each port invents its own error handling, producing the same opaque bash-grade error strings in compiled form -- and the operator still gets no pointer to the mios.toml line that broke.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- one immutable image whose compiled tools are context-independent, so the same binary serves the builder, the runtime and the stripped firstboot-tier. (1 tasks)
- **AGY-1011**: Build miosd as a static musl binary so one artifact runs at build, in-image, and in the firstboot-tier  (WS-LANG-AUTO | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `ldd /usr/libexec/mios/miosd` reports "not a dynamic executable"; the binary executes on the base image and in a distroless/firstboot context; image size does not regress; `cargo test` and `just drift-gate` are green.
  - *Why:* miosd is becoming the executor for postcheck and the renderers while the firstboot-tier deliberately evicts the vLLM/SGLang whales; a glibc-dynamic binary can fail to load in exactly that shrunk tier, and cannot be reused as a host build tool on any other base.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- one materializer owns the SSOT walk so the resolver twins stop diverging. (1 tasks)
- **AGY-1707**: Make the twins actually consume `mios-ssot-walk` instead of duplicating the walk verbatim  (WS-LANG | P2 | L)  [BROKEN]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: grep finds the exclusion/keep lists in exactly ONE place; editing that place changes the output of resolver-twin (check 45) and names (check 30); the crate has a real consumer beyond the workspace manifest.
  - *Why:* three verbatim copies of the walk rules remain, so any future exclusion change must be made three times or the twins silently disagree -- and the "gates green" claim proves nothing because the crate is bypassed entirely.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- one memory-safe diagnostic entry point for agents and operators, with no embedded python. (1 tasks)
- **AGY-1028**: Port mios-doctor to a miosd doctor health-probe subcommand  (WS-LANGX | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd doctor` emits the same section headers and pass/fail verdicts as the bash on a fixture host; the exit code matches; the embedded `python3 -c` probes are gone; golden trycmd green; ratchet decremented.
  - *Why:* mios-doctor is the structured replacement for throwaway diagnostic scripts, but its embedded python heredocs make it unlintable and dependent on a python that the firstboot-tier may not carry — so the one tool used when things are broken is itself fragile.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- one typed console/diagnostic surface for the orchestrator instead of duplicated framing math and an opaque failure blob. (1 tasks)
- **AGY-993**: Move build.sh's ASCII progress UI into `mios-build` and report phase failures as miette diagnostics  (WS-LANG-AUTO | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd build` renders the framed progress UI byte-compatible with today's build.sh output under snapshot test, a phase failure prints a miette diagnostic carrying phase name and step-log path, library errors are thiserror enums, and the drift-gate is green.
  - *Why:* A failing build currently emits a grep-assembled FAILURE LOG that names no log path and no cause, so every failure costs an operator a manual hunt — and the framing math is duplicated across nine shell helpers that drift from the real output.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- ports are proven byte-parity before the shell/Python original is trusted less. (1 tasks)
- **AGY-1706**: Make the Rust names-registry generator emit byte-identical output and put it on check-30's path  (WS-LANG | P2 | L)  [BROKEN]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `diff <(rust-gen) <(python3 tools/generate-names-registry.py)` is empty for both outputs; check-30 invokes the Rust binary (or the task states it does not); the crate fails to build if the parity harness diverges.
  - *Why:* a workspace member that compiles trivially and emits nothing was marked done -- the exact "byte-identical Rust port that isn't" failure, which erodes trust in every subsequent port claim.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- puts the boot-time hardware enumerators that gate all containerized GPU access on tested PCI/sysfs parsing. (1 tasks)
- **AGY-1056**: Port the GPU/CDI detection + passthrough family (gpu-detect, gpu-pv-detect, mios-cdi-detect, mios-gpu-passthrough, mios-sriov-init) to a `miosd gpu` subcommand  (WS-LANGX | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `/run/cdi` output is byte-identical vs the bash across golden multi-vendor sysfs fixtures; the two units invoke `miosd gpu`; gate green.
  - *Why:* Multi-vendor sysfs/PCI text-parsing in shell decides whether containers see a GPU at all; a misparse silently disables acceleration for the whole AI plane or breaks passthrough, and there are no fixtures proving otherwise.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- puts the hottest verb backend, the `mios build` pipeline driver, under a compiled orchestrator that owns step order and gating explicitly. (1 tasks)
- **AGY-1039**: Port mios-build-driver to a `miosd build` orchestrator behind the verb dispatcher  (WS-LANGX | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd build` drives the same pipeline step order, writes an identical `/etc/mios/install.env` identity block, and resumes idempotently like the bash on a dev build; the 66 NN-*.sh steps are byte-unchanged; the side-by-side diff is clean; the ratchet is decremented once the shim is the only bash left.
  - *Why:* TD-7 flags the driver's hand-maintained ordinal/gating blobs; today a silent bash failure aborts a multi-GB build with no typed error and no explicit DAG, and the ordering lives in untested shell.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- remove the silent-failure class from the developer-environment boot path. (1 tasks)
- **AGY-1032**: Port wsl-firstboot to Rust with the WSL-detect gating preserved  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust binary reproduces wsl-firstboot's WSL-gated side effects idempotently with an identical exit code; a non-WSL host no-ops; degrade-open preserved; golden test green; ratchet decremented.
  - *Why:* WSL persistence-link provisioning is a recurring developer-environment failure that fails silently and is then debugged by hand every time the dev VM is rebuilt.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- removes a standalone bash launcher by keeping venv-binary resolution in one audited place. (1 tasks)
- **AGY-1048**: Fold the usr/bin/hermes launcher into the verb dispatcher  (WS-LANGX | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `hermes <subcommand>` passes argv through byte-identically and the not-installed path prints the same guidance with exit 127 as the bash; `usr/bin/hermes` is a shim; golden test green; ratchet decremented.
  - *Why:* Venv-path resolution duplicated outside the dispatcher means a venv layout change has to be fixed in two places, and this file counts against the loose-script surface for no benefit.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- removes a string-interpolating bash launcher from the AI plane's process-spawn seam. (1 tasks)
- **AGY-1037**: Port mcp-server-runner to a Rust launcher with explicit argv (no string-built commands)  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust runner spawns each MCP server with byte-identical argv/env vs the bash on fixtures; the unknown-server error message and exit code match; the golden test is green; the bash-tool ratchet is decremented by 1.
  - *Why:* MCP server names and args flow from config into a shell command string today, which is an injection surface on the agent tool plane, and the endpoints it resolves are not provably SSOT-derived.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- replaces 1265 lines of privileged bash redirects with explicit, error-checked writes driven by SSOT parameters. (1 tasks)
- **AGY-1044**: Port tune-performance.sh to a `miosd tune` subcommand with checked sysfs writes  (WS-LANGX | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd tune --dry-run` lists the identical set of sysfs/cmdline mutations as `tune-performance.sh` on a fixture; apply mode produces the same effect and returns non-zero on a failed write; `mios tune` is unchanged; golden test green; ratchet decremented.
  - *Why:* A failed sysfs redirect in bash is invisible, so today a partial tune leaves the host in a half-isolated state that reports success, and the tuning parameters are not provably SSOT-sourced.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- retire a bash validator whose native replacement already exists but is never built or run. (1 tasks)
- **AGY-1007**: Finish the 97-ssot-lint cutover to the existing mios-ssot-lint crate and ship it from the Containerfile  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-ssot-lint` produces byte-identical findings against the 97-ssot-lint.sh golden, the Containerfile builds and ships the crate, 97-ssot-lint.sh is a shim, and `cargo test` plus the drift-gate are green.
  - *Why:* The native crate is dead weight today — maintained, compiled by nobody, shipped nowhere, while the bash version does the real work — and the missing Containerfile wiring will block every other `tools/native` crate the same way.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- retires an opaque packed-zipapp artifact (neither loose script nor hardened binary) from the image. (1 tasks)
- **AGY-1038**: Replace the mios-dashboard python zipapp with a compiled Rust reporter binary  (WS-LANGX | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust dashboard renders `--dash`/`--mini` snapshots matching the zipapp's framed output on a fixture with ports driven from SSOT; the zipapp artifact no longer exists in the built image; `mios dash` / `mios mini` are unchanged for the operator; the golden test is green.
  - *Why:* A packed zipapp is un-reviewable in-tree and drags a Python runtime into the hot `mios mon` path, and its telemetry duplicates the greenboot probe helpers instead of using them.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- reuse the audited idempotent-unit template to shrink the bash surface again. (1 tasks)
- **AGY-1034**: Port mios-swarm-pack-firstboot to Rust on the shared firstboot crate  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust binary reproduces mios-swarm-pack-firstboot's side effects idempotently with a matching exit code on fixtures; degrade-open preserved; golden test green; ratchet decremented.
  - *Why:* Another firstboot orchestrator whose failures are invisible to its unit; leaving it in bash keeps a duplicate, unaudited copy of the idempotence logic the shared crate already owns.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- rollback as a first-class deliverable so adopting a compiled verb never risks the bake. (1 tasks)
- **AGY-1019**: Add the [migration] SSOT toggle for oxidizr-style per-verb Rust/bash opt-out and rollback  (WS-LANGX | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: setting `[migration].verb.sync_env="rust"` routes `mios sync-env` to the Rust binary and `"bash"` routes back to the shim, with both producing byte-identical output; unset keeps bash; drift-gate green; the Law-15 mirror is confirmed present in both repos.
  - *Why:* Without a per-verb switch, every port is an all-or-nothing commit: a regression discovered after the bake requires reverting and rebuilding the whole image instead of changing one SSOT value.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- stabilizes the agent-facing JSON envelope shape by generating it from typed structs instead of hand-written bash. (1 tasks)
- **AGY-1059**: Port the eight-tool mios-flatpak-* lifecycle family to a native JSON-envelope binary  (WS-LANGX | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: JSON-envelope output is byte-parity with the bash under insta snapshots across search/install/upgrade/run and the error path; the init and install units invoke the native binary; gate green.
  - *Why:* Agent tool-calling parses that exact envelope, and a hand-built bash JSON emitter breaks it on any unescaped app name or error string -- on a path invoked per app launch, so it is hot as well as brittle.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- supply the hermetic seam that makes byte-parity provable before any security-sensitive shell script is deleted. (1 tasks)
- **AGY-999**: Build a record/replay host-tool sandbox (podman, semanage, nvidia-ctk, systemd-analyze) so phases are characterizable offline  (WS-LANG-AUTO | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a recorded fixture set exists for the host tools each ported phase invokes, `cargo test` runs all phase characterization tests offline on both Windows and Linux runners with no podman/semanage present, and a replay mismatch fails the test.
  - *Why:* Without a hermetic host-tool seam, the golden harness cannot verify parity for exactly the phases that touch SELinux, GPU CDI, systemd and podman — so the most security-sensitive strangler-fig cutovers are blocked or would have to land unverified.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the agent plane's view of the tree stays truthful as bash tools are retired. (1 tasks)
- **AGY-1063**: Regenerate the AI manifest/catalog after each shim retirement and gate on tracked build cruft  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: manifest and catalog are regenerated with retired entries removed; `git ls-files usr/libexec/mios` shows no `*.bak`/`*.retrytest*`/`__pycache__`; the new drift-check fails when one is reintroduced; `just drift-gate` green.
  - *Why:* A manifest full of ghost source content actively misleads the agent plane into editing files that no longer exist, and the .bak/pyc files already in the tree show the cleanup step does not exist today.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the boot-integrity policy generator becomes compiled, typed and parity-proven. (1 tasks)
- **AGY-1489**: Port generate-cosign-policy.py to a typed compiled `mios-cosign-policy` with golden parity  (WS-SBOM | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-cosign-policy` reproduces the committed `policy.json` byte-for-byte (trycmd green) and `--check` parity holds; `generate-cosign-policy.py` is a delegating shim; `cargo test`, `just drift-gate` and clippy -Dwarnings are green; both repos carry it.
  - *Why:* The file that decides which container signatures the OS trusts is currently produced by a script that degrades to "trust everything" on any parse hiccup -- a malformed SSOT edit disarms boot integrity with no error.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the compiled resolver core that makes SSOT-operator-defined a single typed engine instead of three hand-synced twins. (1 tasks)
- **AGY-1013**: Build mios-toml-core: one figment-based typed layered mios.toml resolver crate with a --shell emitter  (WS-LANGX | P1 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-toml-core --shell` diffs byte-identical against `source tools/lib/userenv.sh && env | grep ^MIOS_ | sort` for the vendor SSOT; a malformed value yields a miette diagnostic with the correct byte-span; `cargo test` green; the crate is a workspace member.
  - *Why:* Three parallel resolvers (mios_toml.py, the userenv.sh twins, globals.ps1) held together only by twin-equivalence testing is the duplication the operator flagged; every divergence between them silently mints wrong values into Quadlets and install.env.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the enabler that makes any Rust port actually ship inside the bootc image. (1 tasks)
- **AGY-1049**: Extend the Containerfile rust-builder to build the tools/native workspace and COPY every release binary into /usr/libexec/mios  (WS-LANGX | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `podman build` produces an image containing `/usr/libexec/mios/<bin>` for every declared native crate; a new drift-check asserts each declared binary exists and is executable in the built layer; the bake is green.
  - *Why:* Every port is inert today: the compiled artifact is not in the image, so a ported tool cannot be verified end-to-end and the running system keeps executing the bash it was supposed to replace.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the fail-closed compliance verdict runs on memory-safe, tested code. (1 tasks)
- **AGY-1502**: Port mios-oscap-gate to a compiled Rust verb with golden ARF fixtures  (WS-SBOM | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust gate reproduces the python count and exit code over the golden ARF fixtures (insta green); the python is a shim; `86-oscap-compliance.sh` drives it unchanged; `cargo test` and clippy -Dwarnings green; both repos carry it.
  - *Why:* An untested python script parsing untrusted XML currently holds a veto over whether the image is compliant enough to ship, and a parser bug either blocks a good build or passes a non-compliant one.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the first real cutover demonstrates the strangler-fig + SSOT-toggle + byte-parity playbook. (1 tasks)
- **AGY-1073**: Wire the already-written Rust generate-names-registry into the build and check 30; demote the .py to a toggled fallback, then delete it  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: check 30 invokes the Rust binary; Rust and `.py` outputs are proven byte-identical on the current tree; flipping one `[migration] use_rust_verbs` value rolls back to the `.py`; `just drift-gate` green; the `.py` deleted or shimmed with the change staged by explicit path.
  - *Why:* A finished Rust binary sits unused while the gate runs the Python it was written to replace -- so the campaign carries maintenance cost for two implementations and has proven neither the toggle nor the parity workflow that 20 later ports depend on.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the kernel-cmdline projector becomes compiled code without changing a byte of the signed UKI payload. (1 tasks)
- **AGY-1081**: Port generate-uki-cmdline.py to Rust with byte-parity on the signed kernel cmdline  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust binary reproduces `usr/lib/kernel/cmdline` byte-identically and its `--check` diff format matches; trycmd goldens pass; the UKI render step calls Rust with the `.py` fallback toggle; `just drift-gate` green; `.py` demoted or deleted with explicit staging.
  - *Why:* The cmdline is embedded in the signed UKI and cannot be edited at boot -- a dropped or reordered karg ships a system that boots permissive or without LUKS args, and only a reinstall fixes it.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the largest projector becomes reproducible compiled output, making the recurring digest-drift failure structurally impossible. (1 tasks)
- **AGY-1083**: Port generate-pod-quadlets.py to Rust to kill the quadlet-digest-drift class at the generator root  (WS-DEBT | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust generator emits every Quadlet unit type byte-identical to the `.py`, proven per-type against goldens; `check_pod_quadlets` passes with Rust as the generator and `.py` as fallback; regenerating after a broad stage no longer strips pins; `just drift-gate` green; `.py` demoted or deleted with explicit staging.
  - *Why:* Quadlet-digest drift is a documented recurring outage in this tree -- the pod-quadlets check goes red, someone re-stages pins by hand, and it happens again next commit; generating-not-authoring ends the cycle.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the signature-enforcement projector becomes typed, memory-safe compiled code with proven byte-parity. (1 tasks)
- **AGY-1080**: Port generate-cosign-policy.py to Rust with miette diagnostics and a trycmd golden, demoting the .py to a toggled fallback  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust binary emits `policy.json` byte-identical to the `.py` across the trycmd goldens in both modes; a malformed `policy_mode` yields a miette span diagnostic; the drift-check calls Rust with `.py` fallback via the SSOT toggle; `cargo test` and `just drift-gate` green; `.py` deletion staged explicitly.
  - *Why:* `policy.json` is what makes `sigstoreSigned` enforcement real -- a silent formatting or field divergence there disables image signature checking with no visible symptom.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the strangler seam where the verb NAME is the stable façade and compiled ports slot in behind it unchanged. (1 tasks)
- **AGY-1018**: Build mios-verb-dispatcher to replace the eval-bearing verb routing seam  (WS-LANGX | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every verb in KNOWN_VERBS resolves through mios-verb-dispatcher to the identical exec target (golden snapshot passes); a fuzzed or hostile arg cannot reach `eval` or an unlisted command; `mios build`, `mios theme` and `mios sync-env` behave byte-identically; `cargo test` green.
  - *Why:* Verb arguments arrive from an untrusted agent boundary and today reach `eval` in nine places — a command-injection surface sitting in the OS's primary CLI, and the one seam that must be stable before any verb body can be ported.

### Domain: E-01 Compiled native tier: Rust-port the build orchestrator and the libexec tool fleet -- the template slice for migrating a leaf libexec verb to compiled, memory-safe code with no interface change. (1 tasks)
- **AGY-1457**: Port mios-hardcode-lint to a std-only Rust crate behind the identical CLI facade (strangler)  (WS-ZEROHC | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo build -p mios-hardcode-lint` succeeds; `cargo test -p mios-hardcode-lint` passes every trycmd golden fixture byte for byte; the Rust binary and the Python tool produce identical violation sets over the live repo; the Python tool is untouched and the fallback is intact.
  - *Why:* The lint that enforces NO-HARDCODE is itself an unhardened interpreted script with no type safety and no test suite; until it is compiled and characterized, the gate's own correctness rests on nothing.

### Domain: E-02 Technical-debt retirement (TD-1..TD-8) -- removes the silent-failure class from the runtime monitor and clears the ruff baseline. (1 tasks)
- **AGY-1087**: Replace the 7 bare `except:` clauses in MiOS-Mon.py with typed exception handling  (WS-DEBT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `ruff --select E722` over `MiOS-Mon.py` reports zero findings; every handler names its exception type(s); the monitor still renders when a probe is unavailable; `just drift-gate` green.
  - *Why:* A system monitor that swallows all exceptions hides exactly the errors it exists to surface and cannot be interrupted with Ctrl-C, and its 7 findings are the sole blocker to enabling the E722 rule tree-wide.

### Domain: E-02 Technical-debt retirement -- eliminates the named TD-1 eval-injection surface from the verb library and gates its return. (1 tasks)
- **AGY-1110**: Kill the eval-on-agent-args launcher path in mios-launch/mios-window (TD-1)  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Neither file evals an agent-derived string; launcher behavior is verified against a golden of prior launch commands; the no-eval gate is green and RED against a deliberately planted eval; the `[laws]` entry is mirrored in both repos.
  - *Why:* `eval` on agent-controlled arguments is direct remote-code-execution surface (cf. the Gemini-CLI eval-injection CVE) reached straight from the dispatch chokepoint, and the system's own rule is that agent input is never authorization.

### Domain: E-02 Technical-debt retirement -- finishes the consolidation `mios_toml.py` was created for, so one resolver semantics holds everywhere. (1 tasks)
- **AGY-1092**: Route every tool through the shared resolver, deleting the ~13 re-rolled `try tomllib/except tomli` + hardcoded-layer copies  (WS-DEBT | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `grep -r 'import tomli' usr/libexec/mios tools` matches only `mios_tools/config`; every consumer resolves `mios.toml` solely through the shared resolver; a deliberately reintroduced local tomli fallback fails the new drift-gate check; `just drift-gate` green.
  - *Why:* A dozen divergent copies of the layer-resolution boilerplate means a fix to vendor<host<user semantics lands in one place and silently misses the other twelve — the exact drift the shared resolver was supposed to end.

### Domain: E-02 Technical-debt retirement -- pulls author-workflow tooling out of the shipped image and inside the packaging boundary. (1 tasks)
- **AGY-1104**: Inventory and relocate the remaining dev-only one-shot scratch scripts in tools/  (WS-DEBT | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Every script carries a recorded classification with call-site evidence; the dev-only ones are excluded from the shipped image and package; no gate or build phase references a moved path; `just drift-gate` green.
  - *Why:* Retiring 2 of ~9 scratch scripts leaves seven author-workflow tools inside the production image, growing its surface and sitting outside the packaging and typing boundary everything else is being pulled into.

### Domain: E-02 Technical-debt retirement -- puts typed wire schemas under the agent-pipe HTTP boundary ahead of the server.py decomposition. (1 tasks)
- **AGY-1108**: Introduce pydantic wire-schema models for the FastAPI request/response bodies  (WS-DEBT | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The two pilot handlers accept typed models; a malformed body returns 422 naming the field; `test_server_import.py` and the surface-parity gate stay green; the schemas package has a sibling test.
  - *Why:* Raw-dict bodies at the HTTP boundary let a wrong-typed value travel deep into dispatch before failing (or worse, succeed with the wrong meaning), and there is no shared substrate for the per-cluster pydantic tasks until these models exist.

### Domain: E-02 Technical-debt retirement -- removes a local-escalation hazard and adds the gate that keeps it removed. (1 tasks)
- **AGY-1095**: Replace predictable /tmp temp-file paths with tempfile mkstemp/mkdtemp and gate literal-/tmp  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `grep -r '/tmp/' usr/libexec/mios --include='*.py'` excluding tests returns empty; the ruff S108 gate is active and green; oscap-scan writes under a 0700 `mkdtemp`; `just drift-gate` green.
  - *Why:* A privileged compliance scanner writing to a guessable `/tmp` filename is a symlink-attack primitive an unprivileged local user can exploit, and nothing else in the campaign touches temp-file safety.

### Domain: E-02 Technical-debt retirement -- removes non-portable, re-runnable tree mutators from the shipped tools surface. (1 tasks)
- **AGY-1090**: Retire the hardcoded-path one-shot scratch scripts tools/fix-agy.py and tools/apply-unification.py  (WS-DEBT | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Both files no longer exist; git history shows their edits already in-tree; `grep -r 'fix-agy\|apply-unification'` over the repo is empty; `just drift-gate` green; the deletions staged by explicit path.
  - *Why:* Two dead scripts hardcoding `c:\MiOS` are unrunnable off this one machine and actively dangerous if re-executed, since they rewrite tracked files in place with no guard.

### Domain: E-02 Technical-debt retirement -- replaces silently-swallowed SSOT failures with typed, spanned, gate-matchable diagnostics. (1 tasks)
- **AGY-1109**: Add a typed exception hierarchy + operator-facing config diagnostics  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A malformed `[colors]` value raises a typed `MiosConfigError` naming the section/key with a span; absence of an optional section still returns `{}` degrade-open; a sibling test covers both paths.
  - *Why:* An operator who mistypes one SSOT value today gets a silently-defaulted system and a buried warning line — the worst failure mode in a config-projected OS, since the wrong behavior looks like correct behavior.

### Domain: E-02 Technical-debt retirement -- shrinks the module-ceiling grandfather list toward zero so the tools become typeable and testable. (1 tasks)
- **AGY-1091**: Split mios-dotfiles-render (1239) and mios-computer-use (1113) below the module ceiling  (WS-DEBT | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: No module under `mios_tools.dotfiles_render` or `mios_tools.computer_use` exceeds 800 lines; the characterization tests for both entry-points pass unchanged; both names are gone from the grandfather list; `just drift-gate` green.
  - *Why:* After mios-daemon these are the two largest ceiling offenders, and while they stay monolithic the ceiling gate is permanently softened by a grandfather list that never shrinks.

### Domain: E-02 Technical-debt retirement -- unblocks console-script packaging by removing absolute-venv coupling. (1 tasks)
- **AGY-1096**: Normalize Python shebangs and retire the two hardcoded venv-path interpreters  (WS-DEBT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Both tools run under the standard interpreter or packaged entry-point; the shebang-uniformity gate is active; `grep '.venv/bin/python' usr/libexec/mios` is empty; `just drift-gate` green.
  - *Why:* Two hardcoded venv shebangs will silently break the packaging migration mid-flight, and they are enumerated nowhere else in the task set.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- an importable package boundary is the strangler-fig façade every later typing, test and Rust-port task lands into. (1 tasks)
- **AGY-1066**: Package the 122 libexec Python tools as an installable `mios_tools` module, killing the 52 sys.path hacks  (WS-DEBT | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `python -m build` produces a wheel and `pip install` exposes `import mios_tools.config` with NO `sys.path.insert`; the 3 shared modules import cleanly as `mios_tools.*`; `just drift-gate` green; changes staged by explicit path (no `git add -A`).
  - *Why:* 52 fragile `sys.path.insert` calls and the SourceFileLoader workarounds they force break on any file move, and without importable modules there is nothing for mypy, pytest coverage or a typed model layer to attach to.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- breaks up the hottest and largest agent-pipe module with proof that request behavior is unchanged. (1 tasks)
- **AGY-1130**: Split routing/chat.py behind a chat-transcript golden  (WS-DEBT | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the chat transcript golden is byte-identical pre/post, chat.py is under 800 lines with sibling tests, `test_mios_chat.py` and surface-parity are green, and the ceiling allowlist entry is removed.
  - *Why:* Every operator chat request runs through this 2140-line file, so it is simultaneously the riskiest to touch and the most expensive to leave unsplit.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- brings the biggest federation module under the ceiling while leaving the signed identity bytes untouched. (1 tasks)
- **AGY-1129**: Split federation/a2a and extract a pydantic AgentCard schema  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the served agent-card is byte-identical pre/post, both files are under 800 lines, the a2a suites and surface-parity gate are green, and a2a.py leaves the ceiling allowlist.
  - *Why:* The agent-card is a SIGNED federation identity document; any unguarded edit to a 1720-line module can change bytes that peers verify.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- brings the routing cluster's two heaviest execution engines under the module ceiling without altering execution behavior. (1 tasks)
- **AGY-1138**: Split routing/dag_exec (1595) and native_loop (1527) behind transcript goldens  (WS-DEBT | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: DAG and native-loop transcripts are byte-identical pre/post; all four files are under 800 lines; `test_mios_dag_exec.py`, `test_mios_native_loop.py` and the surface-parity check are green; both allowlist entries removed.
  - *Why:* These are the hottest code paths in the router; while they stay 2x over the ceiling, every change to them is reviewed by eye instead of by gate, and the ratcheting ceiling can never close.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- closes TD-8 so documented line-count claims are derived, not asserted. (1 tasks)
- **AGY-1270**: Add the TD-8 doc-metric re-derivation drift-check  (WS-TEMPLATE | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: An over-claimed line-count metric turns the gate RED; corrected claims pass; the `server.py` "~26k" claim is fixed and now gated.
  - *Why:* Wrong metrics send agents to the wrong file -- the operator already got burned by the 3x `server.py` overclaim when planning a decomposition that was aimed at mass that wasn't there.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- completes the modular-monolith by pulling the last large tool-loop module into the package. (1 tasks)
- **AGY-1133**: Migrate mios_skills into mios_pipe with type hints and a parity golden  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `execute_skill` output is byte-identical pre/post, the shim re-exports every public name, the module is mypy-strict clean, and `test_mios_skills.py` plus the sibling-test and boundary gates are green.
  - *Why:* A top-level module on the tool loop sits outside the package's boundary and sibling-test gates, so it is typed by nobody and gated by nothing.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- completes the modular-monolith package boundary the drift-gate is already trying to enforce. (1 tasks)
- **AGY-1143**: Move the six residual top-level modules into mios_pipe and kill gateway_queue's server.py global DI  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: all six modules live under `mios_pipe.*` with scratchpad de-duplicated, the top-level files are thin shims, gateway_queue no longer reads server.py module globals, sibling tests and mypy pass, and the drift-gate is green.
  - *Why:* The tool-execution seam currently only works if server.py imported first and monkey-set its globals, which makes it untestable in isolation and leaves the package migration permanently half-finished.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- decomposes the security-critical verb->bash chokepoint without altering a single emitted command. (1 tasks)
- **AGY-1113**: Split mios_dispatch.py behind a golden command-builder snapshot  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the `_build_dispatch_cmd` golden is byte-identical pre/post, both files are under 800 lines, `test_mios_dispatch.py` passes unchanged, and mios_dispatch leaves the ceiling allowlist.
  - *Why:* The largest security-critical file is also the one every verb traverses; splitting it without a golden oracle risks silently changing what gets executed on the host.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- dissolves the 7812-line monolith the whole modular-monolith refactor exists to remove. (1 tasks)
- **AGY-1112**: Continue the server.py R-wave strangler: extract ceph-health and LoRA blocks  (WS-DEBT | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the moved blocks live in `mios_pipe` with sibling tests, the surface-parity gate diff is zero, the regenerated `surface.generated.json` is staged explicitly, server.py's `wc -l` drops, and the matching ceiling-allowlist entries are removed.
  - *Why:* server.py is the worst ceiling offender; every hour it stays a 7812-line monolith, any change to it risks the whole /v1 surface.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- finishes the over-ceiling inventory and types the OS-action exec surface while it is open. (1 tasks)
- **AGY-1150**: Split oscontrol/vision/toolexec and memory/knowledge, typing the OS-control action schema on the way  (WS-DEBT | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: all four files are <=800 lines, goldens are byte-identical pre/post, oscontrol still uses exec-form subprocess behind a typed action schema, and the ceiling + sibling-test drift-gates are green.
  - *Why:* These are the last unowned over-ceiling modules, and oscontrol in particular executes host actions on model-shaped input with no schema between the two.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- hardens the fitness-function generator every server.py split task depends on, so the parity gate emits signal rather than noise. (1 tasks)
- **AGY-1137**: Make mios_surface.py deterministic: type it, add a pydantic surface record, prove idempotent regeneration  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: regenerating twice yields byte-identical JSON (stable ordering, no host paths); `mypy --strict` clean; the WS R0 parity gate green; the regenerated file staged by explicit path.
  - *Why:* A generator with unstable ordering or leaked host paths makes the parity gate flap on every refactor, which trains reviewers to ignore the one check that guarantees no public route silently disappears.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- hardens the taint/HITL/quarantine boundary between agent input and the broker without touching its name-keyed contract. (1 tasks)
- **AGY-1128**: Type-harden the access security gates with a verdict golden and taint property tests  (WS-DEBT | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the `(verb,tier,taint)` verdict golden is unchanged, the three property invariants hold under hypothesis, the modules are mypy-strict clean, dispatch tests are green, and no symbol was renamed.
  - *Why:* These untyped gates are the last thing standing between model-supplied input and host command execution, and nothing currently proves a tainted session cannot reach a privileged verb.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- makes cache invalidation across the fleet an explicit reviewed decision instead of a refactor side effect. (1 tasks)
- **AGY-1122**: Type toolsearch and pin the embedding-cache fingerprint with a golden  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the module is mypy-strict clean, fingerprint and persisted-cache JSON match the golden, and `test_mios_toolsearch.py` plus the boundary gate are green.
  - *Why:* A one-character fingerprint change today silently invalidates every operator's on-disk cache and triggers a fleet-wide re-embed storm.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- makes connection pooling structural rather than a convention one code path already ignores. (1 tasks)
- **AGY-1119**: Route every outbound call through the pooled httpx client and gate ad-hoc clients out  (WS-DEBT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no `httpx.AsyncClient(` remains outside `_get_client`, the gate rejects a planted ad-hoc client, and planner requests reuse the pool with unchanged behavior.
  - *Why:* Every planner call currently pays a TCP connect and teardown on a hot outbound path that already has a pool sitting unused.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- makes the agent datastore's injection defense a reviewed snapshot diff rather than a code-reading exercise. (1 tasks)
- **AGY-1123**: Golden-snapshot the parameterized SQL builders in memory/pg  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: golden SQL snapshots cover the recall/insert/RLS matrix, the property tests pass, the module is mypy-strict clean, and `test_mios_pg.py` is green with no DB required.
  - *Why:* Nothing currently fails if someone splices a value into a query string, so the datastore's whole injection defense rests on reviewer vigilance.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- makes the highest-risk agent path sandbox-mandatory and degrade-CLOSED, and moves it into the governed package. (1 tasks)
- **AGY-1132**: Harden mios_codemode, the model-controlled code-execution surface  (WS-DEBT | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: codemode lives under `mios_pipe` with a sibling test, every exec path is sandbox-wrapped, the no-eval/exec-of-model-output lint is green and fails on a planted violation, and degrade-closed is verified.
  - *Why:* Executing model-authored code is the most dangerous verb path in MiOS, and today nothing mechanically guarantees it is sandboxed or that it refuses to run unsandboxed.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- pins the token-budget and cache-reuse logic that every single turn passes through. (1 tasks)
- **AGY-1148**: Type and golden the KV-cache/context cluster (kvfork/kvgc/compact/ctxpack/tokenize/promptfmt/promptver)  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mypy --strict` is clean over `context/` excluding grounding, the token-budget and compaction goldens are byte-stable, the kvgc pinned-fork proptest is green, sibling tests exist, and the drift-gate is green.
  - *Why:* A ctxpack overrun truncates prompts or blows the context window at inference time, and a kvgc bug that evicts a pinned fork silently destroys cache reuse -- both surface as vague model-quality complaints rather than as test failures.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- proves the fail-closed and degrade-open invariants of the pure policy cluster instead of asserting them in comments. (1 tasks)
- **AGY-1127**: Property-test the council diversity/arbiter/blades invariants  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the three invariants hold under hypothesis for all generated inputs, the modules are mypy-strict clean, and the existing council tests plus the boundary gate are green.
  - *Why:* arbiter is a second-opinion security gate; example-based tests can pass while an unknown tier quietly ranks BELOW the ceiling and is allowed.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- proves the split+type+parity pattern on the smallest over-ceiling module so the rest of the agent-pipe decomposition can follow it. (1 tasks)
- **AGY-1136**: Split context/grounding.py (842) under the 800-line ceiling and type it, with an output-parity golden  (WS-DEBT | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: grounding output is byte-identical pre/post split; both files are under 800 lines; `mypy --strict` is clean; `test_mios_grounding.py` is green; the ceiling-allowlist entry for grounding.py no longer exists.
  - *Why:* Today the ceiling gate can only ever be advisory while allowlisted modules sit above it, and the campaign has no demonstrated, low-risk template for splitting a live RAG module without changing its output.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- puts the deliberation layer's structured-output contract under a typed schema that cannot drift from its vocabulary. (1 tasks)
- **AGY-1120**: Derive the DCI act schema from a pydantic model instead of a hand-written dict  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: dci.py is mypy-strict clean, the pydantic-generated schema is byte-identical to the golden of `_DCI_ACT_SCHEMA`, and `test_mios_dci.py` plus the server-free boundary gate stay green.
  - *Why:* Acts and schema are maintained separately today, so adding an act can silently produce a schema the model is never told about.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- removes a live event-loop stall from the /v1 front door every agent request traverses. (1 tasks)
- **AGY-1118**: Remove blocking subprocess.run from async handlers and lint the class shut  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the three ceph probes run non-blocking, the AST lint reports zero `subprocess.run` inside `async def` and fails on a planted one, health endpoints return byte-identical bodies (golden parity), and the timeout resolves from env.
  - *Why:* One blocking call head-of-lines every concurrent request on the AI front door — this is measurable latency today, not cosmetics.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- removes a process-global singleton mutation that silently undercuts the typed-config effort across the whole agent-pipe. (1 tasks)
- **AGY-1140**: Delete the global `os.environ = _StrippedEnviron` monkeypatch; strip quotes at read via a typed accessor  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the `os.environ =` assignment no longer exists (drift-gate grep negative added), env reads go through the typed accessor, a parity golden shows identical resolved values against the current stripped mapping, and mypy + pytest are green.
  - *Why:* Every module and subprocess inherits a mutated environment mapping with async/thread-surprising behavior, `os.environ` cannot be statically typed, and any typed settings model built on top of it is built on sand.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- removes the last model-reachable shell/template injection surface in agent-pipe, distinct from the mios_codemode path already covered. (1 tasks)
- **AGY-1139**: Sandbox conductor.py: replace create_subprocess_shell with exec+StepSpec and Jinja2 Template with SandboxedEnvironment  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no `create_subprocess_shell` or bare `jinja2.Template` remains anywhere in agent-pipe (new drift-gate grep negative added), `StepSpec` rejects a free-form `cmd`, the injection proptest is green, and `pytest` + `just drift-gate` are green.
  - *Why:* Any prompt that reaches the conductor today can run arbitrary shell on the host as the agent-pipe user; this is the sharpest remaining RCE-class hazard in the AI plane and nothing else in the queue closes it.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- schema-validates the forensic and billing trail without changing a byte of the stored event JSON. (1 tasks)
- **AGY-1135**: Type observability audit/trace/cost as pydantic structured events  (WS-DEBT | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: emitted event JSON is byte-identical to the golden, the three modules are mypy-strict clean, the audit/trace/cost tests are green, and degrade-open is preserved.
  - *Why:* The audit and cost ledgers are the only record of what the agent plane did and what it spent, and an ad-hoc dict can drop a field with nothing noticing.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- the SSOT schema becomes code, so a mistyped key fails loudly instead of projecting a wrong value. (1 tasks)
- **AGY-1077**: Introduce pydantic v2 typed models for the mios.toml sections the tools consume, replacing raw dict .get() plumbing  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `MiosConfig` models cover >=6 sections; `config.load_typed()` round-trips the shipped `mios.toml` without error and raises on a deliberately malformed fixture; >=3 consumers are off raw `.get()`; mypy is clean on the models; `just drift-gate` green.
  - *Why:* Chained `.get()` turns a renamed or mistyped SSOT key into a silent default that flows straight into a Quadlet or `policy.json` -- the failure appears as a misconfigured running system, not as an error.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- the agent-pipe god-module shrinks under typed schemas and real tests (TD-5). (1 tasks)
- **AGY-1704**: Actually extract a health seam OUT of server.py instead of adding a parallel stub  (WS-DEBT-PY | P1 | L)  [BROKEN]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `wc -l server.py` drops by the size of the extracted block; the new module is imported by `server.py` (grep proves a consumer); `health.py` is gone or wired; the replacement test fails if the extracted logic is broken; drift checks 6/11 green.
  - *Why:* the monolith is unchanged while the register records progress, and a duplicate health builder returning fabricated version/port literals is a live wrong-answer hazard if anyone wires it.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- the dispatch monolith is decomposed at genuine seams with tests that bind to real behaviour. (1 tasks)
- **AGY-1705**: Extract the REAL MCP/tool-call dispatch seam, not a fabricated envelope helper  (WS-DEBT-PIPE | P1 | L)  [BROKEN]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mcp_dispatch.py`'s fabricated helper is gone; the dispatch body exists in exactly one module with a real importer; the test fails when that module's behaviour is altered; checks 6/11 green.
  - *Why:* TD-5 debt is unreduced while a dead module and a self-referential test create the appearance of coverage over the highest-traffic path in the agent plane.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- the eval-on-agent-args injection surface is gone from the verb library. (1 tasks)
- **AGY-1074**: Replace `eval "$@"` on agent-controlled args in mios-ai-clear/reset/launch/window with hardened dispatch (TD-1)  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no `eval` on agent- or user-derived strings remains in the four verbs; launch dispatch uses shlex plus array exec; the drift-gate fails on a new `eval` in a libexec verb; existing launch behavior is held by a characterization test; `just drift-gate` green.
  - *Why:* Agent-supplied arguments are an explicitly untrusted boundary, and `eval` on them is the Gemini-CLI-class remote-code-execution bug -- a crafted tool argument today runs arbitrary shell as the verb's user.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- the module-cohesion ceiling becomes a ratcheting fitness function across all 122 tools instead of one subtree. (1 tasks)
- **AGY-1084**: Extend the 800-line module ceiling from agent-pipe to a tree-wide Python drift-gate  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the ceiling check covers all tracked Python tree-wide; the 6 current offenders are grandfathered by explicit SSOT entry; adding a new 801-line `.py` fails the gate; `just drift-gate` green; the SSOT allowlist mirrored in both repos (Law 15).
  - *Why:* Outside agent-pipe nothing stops a new 3000-line tool from landing, so the debt this campaign is paying down regrows in the 122-tool surface faster than it is removed.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- the residual SQL-injection surface the parameterized-postgres gate does not cover is closed. (1 tasks)
- **AGY-1070**: Harden sqlite identifier interpolation in the CLIs behind a validated table allowlist  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every identifier splice passes through `safe_ident()` with regex + allowlist validation; a malformed table name raises before `execute()`; `test_mios_cli_sqlsafety.py` gains a rejection case; the drift-gate fails on a new raw f-string identifier; `just drift-gate` green.
  - *Why:* These four call sites are the only remaining path where an attacker-influenced string reaches SQL unvalidated, and the existing gate does not see them, so the class can grow unnoticed.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- the shared resolver becomes one facade, the seam the typed-model and compiled-resolver work plugs into. (1 tasks)
- **AGY-1076**: Fold mios_toml.py, mios_env.py and mios_db_config.py into one typed `mios_tools.config` surface  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `from mios_tools import config` exposes the union API; the three legacy modules are re-export shims or removed with consumers updated; `check-resolver-twin.py` still passes; `just drift-gate` green; SSOT twin surfaces mirrored in both repos (Law 15).
  - *Why:* Three separate shared modules reached 43 different ways is the duplication the operator flagged, and there is no single place to attach types, so a resolver contract change today means auditing 43 import sites.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- the terminal cleanup that makes static typing and import-graphing of agent-pipe actually complete. (1 tasks)
- **AGY-1144**: Retire the 101 _ShimModule re-exports and the two `__import__("mios_...")` string wirings in server.py  (WS-DEBT | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no `_ShimModule` file and no `__import__("mios_...")` call remains, every import references `mios_pipe.*`, `surface.generated.json` parity and the full pytest run are green, and the drift-gate is green.
  - *Why:* While the shims stand, every module has two importable names and two of them are invisible to the type checker, so the migration's benefits are only nominal and new code keeps binding to the legacy names.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- the worst module-cohesion offender is decomposed so typing and coverage can reach the most operationally critical tool. (1 tasks)
- **AGY-1085**: Split mios-daemon (3371 lines) into cohesive sub-800-line modules behind a stable entry-point  (WS-DEBT | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no `mios_tools.daemon` module exceeds 800 lines; the three daemon tests plus find-ranker pass unchanged; `mios-daemon` behaves identically under a characterization test of the start/gate-eval path; the daemon grandfather entry is deleted from SSOT; `just drift-gate` green.
  - *Why:* A 3371-line untyped daemon is unreviewable and untestable as a unit, mypy and coverage cannot usefully reach it, and it is the tool whose failure most directly stalls the autonomous plane.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- turns the TD-5 module-size limit from a stated intent into a build-failing invariant that every later split task decrements. (1 tasks)
- **AGY-1111**: Land the 800-line agent-pipe module ceiling as a seeded, ratcheting drift-gate (TD-5)  (WS-DEBT | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the gate passes today with the seeded allowlist, FAILS on a newly-oversized file, each split PR must delete its own allowlist row, and `[laws]` carries the ceiling in both repos.
  - *Why:* Without a mechanical ceiling the twelve god-modules keep growing and every "split it later" task has no objective finish line.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- types an untrusted external boundary and shrinks it in the same change. (1 tasks)
- **AGY-1134**: Type the federation MCP + http_caps planes and bring http_caps under the ceiling  (WS-DEBT | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the capability document is byte-identical pre/post, http_caps.py is under 800 lines, both modules are mypy-strict clean, the mcp/http_caps tests are green, and http_caps leaves the ceiling allowlist.
  - *Why:* MCP manifests arrive from outside the host and are consumed as untyped dicts, so a malformed remote advertisement is parsed rather than rejected.

### Domain: E-02 Technical-debt retirement: the TD-1..TD-8 register -- validates the routing table at parse time instead of discovering a malformed entry as a mis-route. (1 tasks)
- **AGY-1121**: Type the agent/node registry builders in routing/agentreg with pydantic specs  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the registry `.model_dump()` is byte-identical to the pre-change dict for the sample mios.toml, the module is mypy-strict clean, `test_mios_agentreg.py` is green, and degrade-open is preserved.
  - *Why:* A typo in `[agents.*]` currently surfaces as traffic routed to the wrong endpoint rather than a load-time error.

### Domain: E-03 PowerShell surface -- adds the shellcheck-equivalent layer above the parse gate so the grandfathered PS surface can only improve. (1 tasks)
- **AGY-1539**: Add a PSScriptAnalyzer Error-severity gate with a committed settings file  (WS-TESTGOV | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `Invoke-ScriptAnalyzer -Severity Error` is clean over the tree and gates CI; a seeded Error-level violation fails the gate.
  - *Why:* Parse-clean PowerShell can still be semantically broken (unreachable code, unapproved verbs, unsafe defaults), and with no severity floor the port-pending surface is free to get worse.

### Domain: E-03 PowerShell surface -- freezes current Windows behavior so the two largest PS files can be demoted behind compiled code without regression. (1 tasks)
- **AGY-1553**: Stand up a Pester project with characterization tests for globals.ps1 and build-mios.ps1 pure helpers  (WS-TESTGOV | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `Invoke-Pester` runs green in CI over `globals.ps1` + `build-mios.ps1` helpers; a deliberate behavior change to a covered function fails an assertion; the coverage floor is enforced and ratcheting.
  - *Why:* Porting or refactoring a megabyte of untested Windows build/resolve logic has no safety net -- any behavior change lands silently on operator machines.

### Domain: E-03 PowerShell surface -- puts the Windows-plane resolver under the same output-parity discipline as the bash twin. (1 tasks)
- **AGY-1432**: Add a PowerShell env-snapshot leg and a cross-plane parity gate (globals.ps1 vs userenv.sh)  (WS-GUP | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-env-snapshot.ps1` emits the same sorted format; `check_ps_env_parity` is green where pwsh is present and skips cleanly where absent; a deliberately drifted `MIOS_FORGE_UID` in globals.ps1 fails the gate.
  - *Why:* The bash twin has a lossless gate and the PowerShell twin has none, so the entire Windows plane is free to drift on exactly the UID/GID and port keys the campaign is trying to single-source.

### Domain: E-03 PowerShell surface -- supplies the runner the PS parse/PSSA/Pester gates need in order to exist at all. (1 tasks)
- **AGY-1552**: Add a windows-latest (or pinned pwsh container) CI leg so the PS gates actually execute  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A PS syntax error or a new PSSA Error-severity finding fails the windows leg in CI; the leg is a required `needs` for the build job; both workflows carry it.
  - *Why:* None of the 36 `*.ps1` files -- including 420KB `Get-MiOS.ps1` and 619KB `build-mios.ps1` -- is executed or analyzed in CI today, so the Windows half of the product ships unverified.

### Domain: E-03 PowerShell surface: parse-gate, deduplicate, compile -- collapse the third hand-maintained resolver so Windows and Linux builds read values from one native implementation. (1 tasks)
- **AGY-1008**: Route build-mios.ps1 through a cross-compiled `miosd resolve` and stop dot-sourcing globals.ps1  (WS-LANG-AUTO | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: build-mios.ps1 obtains all MIOS_* values from the native binary on Windows with output matching today's globals.ps1 values, CI produces a cross-compiled miosd artifact, twin-equivalence stays green through the transition, and the drift-gate is green.
  - *Why:* The shell-shim work leaves the PowerShell twin standing, so every new SSOT key must still be hand-added in a third place; until Windows runs the same binary, the parallel-resolver duplication is only two-thirds solved.

### Domain: E-03 PowerShell surface: parse-gate, deduplicate, compile -- lands the parse-gate leg so the grandfathered PS surface has a floor while it awaits port. (1 tasks)
- **AGY-1538**: Add a PowerShell AST-parse gate over every tracked *.ps1  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The AST gate parses every tracked `.ps1` and fails on a seeded syntax error; `check_powershell_lint` appears in `main()` and has a negative in `tests/drift-gate-negatives.sh`.
  - *Why:* ~1MB of load-bearing PowerShell -- including the Windows build driver and the install front door -- can currently be committed syntactically broken and only fail on an operator's machine.

### Domain: E-03 PowerShell surface: parse-gate, deduplicate, compile -- moves the largest remaining PowerShell-as-program surface onto the compiled tier so the agent's GUI control path is typed and tested (Law 14 TARGET-LANGUAGES). (1 tasks)
- **AGY-1311**: Port the Windows computer-use surface (mios-pc-control.ps1 + mios-uia-dump.ps1) to a compiled binary  (WS-PWSH | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A compiled executor replaces both scripts; golden-master tests show byte-identical JSON for every subcommand including the `type` read-back reason codes; the .ps1 files are thin shims (or deleted) with shim parity proven; `cargo`/`dotnet test` and the drift-gate are green.
  - *Why:* 550 lines of untested P/Invoke drive every GUI action the agent takes on Windows; without a golden oracle any reimplementation silently changes click/type semantics, and the read-back verifier that catches "the agent lied about typing" is exactly the logic a blind rewrite would break.

### Domain: E-03 PowerShell surface: parse-gate, deduplicate, compile -- one file owns the shipped PowerShell profile; the installer copies rather than regenerates. (1 tasks)
- **AGY-1299**: Make the tracked powershell/profile.ps1 the sole profile source and stop embedding a heredoc copy  (WS-PWSH | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The installer function contains no full profile body — only the redirector block; the deployed profile hashes equal to tracked `powershell/profile.ps1`; a Pester test asserts that byte-identity; parse-gate green; mirrored per Law 15.
  - *Why:* Two 1000-line copies of the same profile guarantee drift, so a fix committed to the tracked file never reaches installed machines and the two Windows hosts behave differently for no visible reason.

### Domain: E-03 PowerShell surface: parse-gate, deduplicate, compile -- the PowerShell config plane reads SSOT through exactly one resolver, the seam a compiled resolver later slots into. (1 tasks)
- **AGY-1714**: Extract the four-times-duplicated mios.toml resolver into one shared PowerShell module  (WS-PWSH | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `grep -rn 'function Resolve-MiosTomlText\|function Get-MiosTomlValue'` returns exactly one hit each; `build-mios.ps1` and `Get-MiOS.ps1` import the module; the golden-fixture suite shows byte-identical lookups pre/post; parse-gate + drift-gate green; module present in mios-bootstrap.git.
  - *Why:* Four parallel TOML readers means four different answers to "what does SSOT say" — a key added to mios.toml can be visible to the installer and invisible to the builder — and no compiled resolver can land until there is a single seam to back.

### Domain: E-03 PowerShell surface: parse-gate, deduplicate, compile -- the still-shipping PS server stops being exploitable before the compiled port defaults on. (1 tasks)
- **AGY-1302**: Harden the live mios-oscontrol-server.ps1 request boundary: input validation, launch allowlist, source scope  (WS-PWSH | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The server rejects non-allowlisted launch targets, over-length type payloads and off-tailnet source addresses at the request layer; no request field flows into `Invoke-Expression` or an unquoted command; the malicious-input Pester suite passes; parse/analyzer gates green; mirrored per Law 15.
  - *Why:* Anything that reaches this port today can launch arbitrary processes and synthesize keystrokes on the logged-in desktop, and the only current control is a firewall rule that a compromised LAN or misconfigured interface bypasses.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- Law 16's enforcer becomes compiled, with the Python retained as a one-flag rollback. (1 tasks)
- **AGY-1252**: Port check-template-conformance to a Rust crate and demote the Python to a fallback shim  (WS-TEMPLATE | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test` parity is green against the conformance golden snapshots; the drift gate is green with the binary present and SOFT-skips/falls back to Python when absent; the Python only executes as fallback.
  - *Why:* The most load-bearing template fitness function currently runs through shell+python fragility on every build; leaving it there keeps a Law-16 failure one missing interpreter away.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- a characterization oracle exists BEFORE any scaffolder code is rewritten. (1 tasks)
- **AGY-1250**: Capture golden-master fixtures and a byte-parity harness for `mios new` across all registered types  (WS-TEMPLATE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The harness runs green against current mios-new output; editing any template or the generator in a way that changes output fails the harness until the snapshot is reviewed; every registered type has a committed golden fixture.
  - *Why:* Without a characterization oracle the coming Python->Rust scaffolder port is a blind rewrite whose regressions surface only as malformed files scaffolded fleet-wide.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- attacks the highest-count block of exemptions so ONE-TEMPLATE-PER-TYPE actually holds tree-wide. (1 tasks)
- **AGY-1264**: Ratchet down the grandfather list: conform a tranche of the 171 bash tools / 131 python tests  (WS-TEMPLATE | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: ~50 paths removed from the grandfather list; those files pass conformance at ceiling 0; the list is strictly shorter; `just drift-gate` green.
  - *Why:* Bash tools and Python tests are the bulk of the exemption set -- leaving them exempt means the majority of MiOS source is outside the template law no matter how good the templates get.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- cashes in the compiled-checker port as a real operator-UX upgrade. (1 tasks)
- **AGY-1266**: Emit miette-style spanned diagnostics from the Rust conformance checker  (WS-TEMPLATE | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A non-conforming file yields a spanned, help-annotated diagnostic on stderr while the machine-parseable summary line is unchanged; internal errors are matchable `thiserror` variants; golden snapshots updated and green.
  - *Why:* Today an author gets a path and a vague noun and has to hunt the offending line by hand; that friction is why people reach for the grandfather list instead of fixing the file.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- closes the law-to-check registry gap so Law 16's metadata matches its real enforcers. (1 tasks)
- **AGY-1280**: Reconcile Law-16 enforced_by to name both template gates and supply the missing compile-gate negative test  (WS-TEMPLATE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Law 16's `enforced_by` names both checks; a broken-template negative test drives Check 59 RED and is registered so `check_negative_test_coverage` is satisfied; both-repo parity green; `just drift-gate` green.
  - *Why:* A real Law 16 enforcer is invisible to the law's own metadata and to negative-coverage accounting, so the governance registry misreports what is enforced -- and an expected-but-absent negative test is an accounting hole that hides a missing eval.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- extends the AI-hint header convention to artifacts that have no shell header, so Law 16 conformance and AI-hint coverage survive compilation. (1 tasks)
- **AGY-1053**: Preserve AI-hint discoverability for compiled ports via an out-of-band sidecar registry  (WS-LANGX | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a ported binary whose bash source has been deleted keeps checks 5 and 46 green and still appears in the generated AI manifest; the sidecar registry is the SSOT for that tool's hint metadata.
  - *Why:* The AI plane discovers tools by header metadata, so each completed port would silently shrink agent capability and redden two already-green gates -- which in practice blocks deleting the bash at all.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- fixes the root cause of the 430-line grandfather list before any ratchet is attempted. (1 tasks)
- **AGY-1273**: Scope the over-broad [templates.*] match regexes and add a shared vendored/generated exclude  (WS-TEMPLATE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `check-template-conformance`'s `checked_count` drops to MiOS-owned files only; `conformance-grandfathered.list` shrinks after re-derivation; the both-repo parity check and `just drift-gate` are green.
  - *Why:* Unscoped patterns are why the grandfather list is enormous and why vendored/generated artifacts get conformance-claimed as MiOS source -- de-grandfathering without scoping first just conforms files MiOS does not own.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- guarantees the registry and the directory cannot half-land out of sync. (1 tasks)
- **AGY-1277**: Meta-lint the [templates.*] schema and enforce templates-dir <-> registry bijection  (WS-TEMPLATE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A `[templates.X]` with no matching file, a template file with no registry entry, a non-compiling or unanchored `match`, or a bad `comment` enum each turn the gate RED; both-repo parity green; `just drift-gate` green.
  - *Why:* The registry and the directory are two hand-maintained halves that diverge silently, and the incoming cargo-manifest/systemd-timer/quadlet-split additions are precisely the half-landed edits this bijection catches at commit time instead of at `mios new` time.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- lands Law 16 as ADR + registry row + check, with no surface exempt from the meta-audit. (1 tasks)
- **AGY-1268**: Register the template toolchain in [laws.projection_registry] so Law 16 is audited like Law 8  (WS-TEMPLATE | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `check_projection_registry` lists and verifies the template generator + compiler surfaces; deleting either backing check turns the gate RED; the rows are present in both repos.
  - *Why:* The projection registry is the meta-gate that guarantees every projection surface has an enforcer; a template system invisible to it can lose its enforcement silently and nothing notices.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- makes de-grandfathering permanent progress rather than a reversible win. (1 tasks)
- **AGY-1265**: Make the grandfather list a monotonic, never-grow ratchet  (WS-TEMPLATE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Appending any new line to the grandfather list turns the gate RED; removing lines passes; the recorded ceiling decreases as each ratchet tranche lands.
  - *Why:* A ratchet with no pawl is just a suggestion -- without monotonicity the two de-grandfathering tranches get silently undone by the next author who finds appending easier than conforming.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- makes the `generated=true` claim verified rather than asserted. (1 tasks)
- **AGY-1281**: Gate that generated=true templates are byte-reproducible from their generator  (WS-TEMPLATE | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Editing a `generated=true` template so it diverges from generator output turns the gate RED; regenerating restores green; the quadlet-split scaffolds are covered.
  - *Why:* `generated=true` is currently an honor-system label -- one hand-edit or one broad `git add` desyncs a generated template from its source of truth, and the tree keeps shipping the stale copy.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- makes the mirrored template surface Law-15 enforceable instead of trust-based. (1 tasks)
- **AGY-1267**: Add a cross-repo parity gate for the [templates.*] SSOT and the templates directory  (WS-TEMPLATE | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Divergence between the two repos' template surface fails the gate when both checkouts are present; the check SOFT-skips cleanly when the sibling is absent; declared subsets pass.
  - *Why:* Two hand-mirrored copies with no comparator is exactly the drift Law 15 exists to stop -- and template drift means the two repos scaffold different files from the same command.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- makes the round-trip compiler a real validator rather than a decorative pass. (1 tasks)
- **AGY-1276**: Extend the golden compiler to validate every registered type and fail-closed on missing validators  (WS-TEMPLATE | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Every registered type is either validated or explicitly allowlisted-as-unvalidated with a recorded reason; a deliberately broken rust/systemd-unit/quadlet template turns Check 59 RED; toml/yaml with a missing parser fails closed under CI; `just drift-gate` green.
  - *Why:* The "golden round-trip compiler" green-lights the majority of template types without parsing them, and silently passes on Windows or without pyyaml -- so the compiled and structured types the campaign cares most about are the ones least checked.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- makes type resolution deterministic so no file is validated as the wrong language. (1 tasks)
- **AGY-1274**: Declare explicit template match precedence and detect ambiguous multi-matches  (WS-TEMPLATE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Every tracked file maps deterministically to exactly one winning template; a planted conflicting-comment double-match turns the gate RED; scaffolder and checker agree on the winner; `just drift-gate` green.
  - *Why:* A Python tool is currently being validated as bash; the moment the patterns are scoped or reordered the mislabels move, silently changing which files are checked against which syntax.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- one token vocabulary so every generator renders the same templates identically. (1 tasks)
- **AGY-1248**: Unify the template placeholder vocabulary into one SSOT-declared token set  (WS-TEMPLATE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: No template file contains an undeclared `{{token}}`; `mios new <type> <name>` for every registered type emits zero residual `{{...}}`; the new drift-check fails when an undeclared placeholder is introduced; the table is byte-identical in both repos.
  - *Why:* The orphan engine is silently broken (wrong placeholder scheme) and the three schemes drift independently, so scaffolded files ship with literal `{{name}}` in them -- and porting any consumer to Rust would bake the divergence in.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- puts the scaffolder's default VALUES under operator-defined SSOT instead of frozen in code. (1 tasks)
- **AGY-1278**: Hoist mios-new's hardcoded scaffold defaults (ADR next-id, drift-check id, roadmap-ws enums) into SSOT  (WS-TEMPLATE | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios new adr foo` assigns the true next sequential id; enum defaults resolve from `[templates.*]` with literal fallback; a golden fixture pins the computed output; `just drift-gate` green.
  - *Why:* The frozen `0012-` and `id=99` defaults are already wrong today, so every ADR and drift-check scaffolded now needs a manual fix-up that the author has to know about.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- removes an intermittent false-RED that undermines trust in the Law 16 gate. (1 tasks)
- **AGY-1272**: Harden the templates-dir walk so a stray __pycache__ cannot false-RED the gate  (WS-TEMPLATE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Planting `usr/share/mios/templates/__pycache__/x.pyc` leaves `check_templates_compilation` green; `mios new` help lists only real kinds; the characterization test and `just drift-gate` are green.
  - *Why:* This is the documented "stale `__pycache__` pollution fakes SSOT drift" local-verify hazard biting a second gate -- a RED that depends on whether someone ran Python recently trains people to ignore the gate.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- shrinks the exemption set that lets Law 16 be green while most files are unconformed. (1 tasks)
- **AGY-1263**: Ratchet down the grandfather list: conform a ~20-unit tranche of the 75 systemd units  (WS-TEMPLATE | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: ~20 unit paths are gone from `conformance-grandfathered.list`, those units pass `check_template_conformance` with the ceiling still 0, the list is strictly shorter than before, and every change was staged path-explicit.
  - *Why:* The 430-line grandfather list is the escape hatch that makes Law 16 technically-green while the tree is largely unconformed; without a tranche-by-tranche ratchet the law never becomes real enforcement.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- template validation consolidates into the native workspace and off the build gate's python dependency. (1 tasks)
- **AGY-1253**: Port the compile-templates.py golden round-trip compiler to Rust and demote the Python  (WS-TEMPLATE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The Rust compiler reports the same PASS/FAIL set as `tools/compile-templates.py` over the current template set; `check_templates_compilation` is green via the binary and falls back to Python when the cargo output is absent.
  - *Why:* The round-trip compiler is what guarantees every template can render to a valid file; keeping it in Python leaves the build gate dependent on an interpreter and outside clippy/CI coverage.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- the Law 16 fitness function's observable behavior is pinned before it is ported. (1 tasks)
- **AGY-1251**: Capture golden CLI snapshots (stdout/stderr/exit) for check-template-conformance  (WS-TEMPLATE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The fixtures reproduce current pass/fail stdout+stderr+exit byte-for-byte; deliberately removing a header flips the snapshot to the failing case.
  - *Why:* A gate whose output silently changes during a port stops being trustworthy -- and this one is the enforcer of the template law, so a behavior drift here disables enforcement without turning anything red.

### Domain: E-04 One template per file type + the `mios new` scaffolder -- turns Law 16 from an asserted law into an actually-enforced one on every runner. (1 tasks)
- **AGY-1275**: Make the Law-16 conformance gate fail-closed in CI instead of silently no-op'ing  (WS-TEMPLATE | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Removing `mios-ai-tag` or `python3` in a CI-flagged run turns the gate RED rather than green; interactive runs still degrade-open; `just drift-gate` is green with tooling present.
  - *Why:* A Law-level gate that passes while enforcing nothing is worse than no gate -- right now Law 16 has effectively zero enforcement on Windows and on any runner missing the tagger, and the dashboard says green.

### Domain: E-05 Test and CI governance -- closes the workspace so no compiled code can escape the cargo gates. (1 tasks)
- **AGY-1545**: Add check_native_workspace_gated: every crate dir is a workspace member and CI compiles/tests it  (WS-TESTGOV | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Dropping a new crate dir outside `members` fails `check_native_workspace_gated`; removing the `cargo test --workspace` step fails it; a negative test exists.
  - *Why:* A crate outside the workspace is invisible to clippy, fmt, deny and the test run -- exactly how 5 crates shipped ungated, and it will recur on the next crate added.

### Domain: E-05 Test and CI governance -- ends the unmanaged 3.13/3.14 interpreter straddle by making the version a gated fact. (1 tasks)
- **AGY-1097**: Pin requires-python and add a Python 3.14 forward-compat drift-gate  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `requires-python` is pinned to the bake's interpreter; the `-W error` import-smoke of all 122 tools passes on 3.14; CI produces no cpython-313 artifacts; `just drift-gate` green.
  - *Why:* With zero declared version floor a stdlib removal in the next interpreter breaks the bake with no warning, and the mypy task pins types while nothing pins the interpreter those types are checked against.

### Domain: E-05 Test and CI governance -- gives Python the fast static hazard scan bash already gets from shellcheck. (1 tasks)
- **AGY-1536**: Add a ruff lint gate plus a pyproject [tool.ruff] config over the whole Python surface  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `ruff check` is clean on the curated rule set and gates CI; a seeded unused import or a new bandit `S`-rule violation turns the gate red.
  - *Why:* Every dead import, mutable-default and `eval`/`subprocess` hazard in the Python plane is currently invisible to CI, and the eval-injection debt class can silently reappear once fixed.

### Domain: E-05 Test and CI governance -- gives the Rust plane the dependency-surface gate that bash never needed and Rust cannot ship without. (1 tasks)
- **AGY-1426**: Add cargo-deny + cargo-audit supply-chain drift-gates with Cargo.lock as the SSOT  (WS-GUP | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo deny check` and `cargo audit` pass on the committed lockfile; `check_native_supply_chain` is registered and fails on a seeded banned or advisory-carrying crate; the license allow-list is documented.
  - *Why:* Every crate added to the workspace pulls a transitive tree nobody reviews -- an advisory or an incompatible license lands in the shipped image with no signal at all.

### Domain: E-05 Test and CI governance -- gives the agent-pipe a real harness with coverage, the prerequisite for parity testing every migration slice. (1 tasks)
- **AGY-1107**: Replace the run_tests.py glob-runner with pytest + a coverage-floor gate  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `pytest -q` collects and passes the existing suite; the coverage XML is produced; the coverage-floor gate is green and staged by explicit path.
  - *Why:* Without coverage or a real runner, the god-module decomposition has no way to show a slice was actually exercised, and the glob loop reports nothing beyond exit status per file.

### Domain: E-05 Test and CI governance -- gives the compiled tier the same monotonic coverage ratchet the Python plane gets. (1 tasks)
- **AGY-1557**: Add a cargo-llvm-cov coverage gate with a ratcheting floor for resolver-core and miosd  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo llvm-cov` runs in CI; a drop below the committed floor fails the rust-gate; the floor ratchets monotonically upward; local `just gate-rust` reproduces the CI number.
  - *Why:* As bash logic migrates into `resolver-core`/`miosd`, critical paths can land entirely untested while the suite still reports green.

### Domain: E-05 Test and CI governance -- gives the resolver collapse the randomized differential oracle that makes a compiled single implementation provably safe. (1 tasks)
- **AGY-1086**: Prove the shell and Python mios.toml resolvers equivalent with a shrinking proptest differential oracle  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The test generates >=100 random valid `mios.toml` documents and both resolvers produce identical `MIOS_*` projections (or the shrunk case is fixed); the harness runs inside `just drift-gate`; a deliberately divergent key mapping planted in one resolver is caught and reported; the gate is green on the current tree.
  - *Why:* Today equivalence of the three parallel resolvers rests on one hand-written spot check over a single file, so any collapse-to-one-implementation is a leap of faith — a randomized oracle is the missing safety proof and also mechanizes the GUP lossless-diff invariant.

### Domain: E-05 Test and CI governance -- installs the static-typing foundation every later agent-pipe typing task ratchets against. (1 tasks)
- **AGY-1106**: Add pyproject.toml + strict mypy config + an agent-pipe mypy drift-gate  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mypy mios_pipe` runs clean over the allowlisted modules; `just drift-gate` shows `check_agentpipe_mypy` green; the pyproject and drift-check are staged as explicit paths (never `git add -A`); the `[laws]`/gate note is mirrored in both repos.
  - *Why:* Every typing and pydantic task below is unenforceable without a config file to check against, so type hints added now would silently rot instead of being gated.

### Domain: E-05 Test and CI governance -- lands the proptest differential oracle that makes the compiled plane trustworthy rather than merely tested by example. (1 tasks)
- **AGY-1414**: Differential proptest harness running random-valid mios.toml through both the userenv.sh oracle and mios-resolve  (WS-GUP | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the difftest passes over >=256 generated documents with zero divergence, and an intentionally-introduced resolver bug is caught and shrunk to a minimal counterexample; the harness is documented alongside `check-resolver-twin.py`.
  - *Why:* Hand-written examples only cover the shapes someone thought of; the divergences that ship are the ones nobody imagined, and today nothing generates them.

### Domain: E-05 Test and CI governance -- makes the Rust gates reproducible by pinning the compiler, not just the dependencies. (1 tasks)
- **AGY-1547**: Pin a rust-toolchain.toml (channel + clippy/rustfmt/llvm-tools) for CI, local and build-stage parity  (WS-TESTGOV | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo +<pinned> --version` matches across CI and the build stage; clippy/rustfmt/llvm-cov components resolve from the pin; rust-gate is green with no rustup auto-download of a floating channel.
  - *Why:* `Cargo.lock` pins deps but not the compiler, so clippy/fmt/coverage/mutants results differ between a developer's machine and the runner -- gates that pass locally and fail in CI (or worse, the reverse).

### Domain: E-05 Test and CI governance -- makes the compiled tooling a digest-stable build artifact with a pinned lockfile as the reproducibility SSOT. (1 tasks)
- **AGY-1425**: Bake the native SSOT workspace once, deterministically, instead of running cargo inside drift-check bodies  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: one build step compiles the workspace `--release --locked` with a deterministic epoch; no check body invokes `cargo build`; two independent builds produce identical binary digests for the SSOT crates.
  - *Why:* Compiling inside a check makes the gate's runtime depend on a toolchain and network state that the bake does not control -- it is slow, non-reproducible, and can pass on one machine while failing on the runner.

### Domain: E-05 Test and CI governance -- proptest differential oracles make the three-resolver equivalence a property, not a handful of examples. (1 tasks)
- **AGY-1170**: Add a proptest differential gate proving mios-resolver == mios_toml.py == userenv.sh on random valid mios.toml  (WS-RESOLVER | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p mios-resolver differential` runs N proptest cases with all three resolvers agreeing, or shrinks and reports the minimal divergence; a new drift-check runs it in CI; generated `ai.vllm` inputs exercise the short-vs-long alias reconciliation (`MIOS_VLLM_*` vs `MIOS_AI_VLLM_*`).
  - *Why:* The example-based twin checks pass on the inputs someone thought of; port 53, empty-string shadows and stack offsets are exactly the edge cases that slip through and land as a wrong port on a live host.

### Domain: E-05 Test and CI governance -- supplies the one reproducible tool+runtime base that mypy, ruff and pytest-coverage all require. (1 tasks)
- **AGY-1548**: Create pyproject.toml + a pinned hermetic dev-dependency lock for the Python gates  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A clean CI runner installs the exact pinned dev set from the lock; mypy/ruff/pytest all discover their config from `pyproject.toml`; the fast gate no longer performs unpinned best-effort pip installs.
  - *Why:* Unpinned tool installs make every Python gate result runner-dependent -- a lint or type finding can appear or vanish between two runs of identical code.

### Domain: E-05 Test and CI governance -- the compiled generator is proven equivalent to the legacy renderer, not spot-checked. (1 tasks)
- **AGY-1342**: Prove the Rust unit renderer with a Python reference oracle and a proptest differential harness  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p mios-unit-gen` runs the differential suite green over N random unit documents; a deliberately introduced Rust/Python divergence is caught and shrunk to a minimal case; the suite runs in CI.
  - *Why:* Example-based golden tests miss exactly the edge cases that break a renderer port — quoting, list ordering, empty-value drop — and a divergence found after the strangler cut means shipping malformed units to a fleet.

### Domain: E-05 Test and CI governance -- the new compiled tier ships with the vuln and license gating bash never had. (1 tasks)
- **AGY-1347**: Add cargo-deny / cargo-audit supply-chain gating for the native workspace  (WS-SYSTEMD | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo deny check` and `cargo audit` run in CI and fail the build on a banned or vulnerable crate; `Cargo.lock` is committed; the license allow-list is enforced; the existing CI job order still holds.
  - *Why:* Moving system tooling into Rust without dependency gating imports an unaudited transitive tree into the image that produces every systemd unit — the highest-trust build artifact MiOS has.

### Domain: E-05 Test and CI governance -- turns "bash is thin glue only" from a stated policy into a numbered, registered, enforced law (ADR + `[laws]` row + check). (1 tasks)
- **AGY-1543**: Land candidate Law 17 THIN-GLUE-BUDGET + check_bash_thin_glue_budget  (WS-TESTGOV | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A new >200-line non-shim bash script fails `check_bash_thin_glue_budget`; the grandfather roster is shrink-only; Law 17 appears in `mios.toml [laws]` in BOTH repos; a negative test exists.
  - *Why:* Without a size budget the language law is toothless -- new bash programs keep landing legally, and every later port has no defined ceiling to shrink under.

### Domain: E-05 Test and CI governance -- turns AI-plane testing from an unaggregated shell loop into a measurable, monotonically-improving gate. (1 tasks)
- **AGY-1537**: Convert the ad-hoc test_mios_*.py loop to pytest with a ratcheting coverage floor  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `pytest` runs the agent-pipe suite with coverage reporting; a coverage drop below the committed baseline fails CI; the shell for-loop and inline SKIP string no longer exist in the Justfile or workflow.
  - *Why:* A for-loop that swallows exit codes is not a gate -- agent-pipe test strength is currently unmeasured and free to regress.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- Law 13 twin-equivalence becomes a fuzzed invariant instead of a spot check. (1 tasks)
- **AGY-1532**: proptest differential resolver oracle: random mios.toml asserts mios_toml.py and userenv.sh emit identical MIOS_*  (WS-TESTGOV | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test` runs at least 256 proptest cases through both resolvers; a seeded divergence shrinks to a minimal mios.toml and fails; the harness is wired into rust-gate.
  - *Why:* The resolver is the highest-leverage component in the tree -- a single divergent value silently breaks a Quadlet at runtime -- and example-based spot checks systematically miss the edge cases that the GUP lossless-diff gate later depends on.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- a 4-minute fail lane so a broken Rust port never reaches the hour-long bake. (1 tasks)
- **AGY-1518**: Add a fast, cached pre-bake rust-gate CI job running cargo build + test on every PR  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: PRs show a rust-gate check that builds and tests the whole workspace in under 5 minutes with a warm cache; a failing `cargo test` blocks merge; the identical job exists in the Forgejo workflow.
  - *Why:* A compiled-tested-code campaign with no cargo CI is unenforced -- every subsequent port in this workstream assumes this gate exists, and without it a Rust regression is only discovered an hour later at bake time, or not at all.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- a closed workspace so one cargo invocation can gate every line of compiled MiOS code. (1 tasks)
- **AGY-1516**: Consolidate the two Rust workspaces into one and re-home all eight native crates as members  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo metadata --manifest-path tools/native/Cargo.toml --no-deps` lists all 8 crates plus miosd as workspace members; `cargo build --workspace --locked` compiles every one; no Cargo.toml directory in the tree remains outside a workspace.
  - *Why:* Orphaned crates escape every cargo gate, so the entire test/clippy/deny/audit stack this workstream builds is meaningless until the workspace is closed -- five crates are currently uncompiled and untested by CI.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- a differential golden that de-risks demoting the Python bake-planner to fallback. (1 tasks)
- **AGY-1529**: Add a golden parity harness pinning Rust mios-bake-plan to generate-bake-plan.py output  (WS-TESTGOV | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p mios-bake-plan` proves Rust output equals Python output; a `[build.bake]` change honoured by only one implementation fails the test.
  - *Why:* Two live bake-planners already run in the same pipeline with nothing asserting they agree, so a divergence would silently change what gets baked into the published image depending on which binary was present.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- a per-PR security tripwire that fires in seconds, not at bake time. (1 tasks)
- **AGY-1522**: Add a fast cargo-audit RustSec advisory gate to the pre-bake lane  (WS-TESTGOV | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: rust-gate runs `cargo audit` against the committed Cargo.lock and fails on any advisory; a deliberately vulnerable pinned dependency turns the job red.
  - *Why:* Without a fast advisory check, a known-vulnerable dependency can sit in the lockfile across many merges before any slower scan notices, and a security regression discovered at bake time has already cost an hour of runner budget.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- brings mypy to the Python plane so the AI-plane half of the SSOT resolver is machine-checked, not asserted. (1 tasks)
- **AGY-1535**: Add a mypy --strict gate over usr/lib/mios with a shrink-only per-module opt-out baseline  (WS-TESTGOV | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mypy --strict` passes for the ratcheted module set and gates CI; adding a module to the opt-out roster fails; `mios_toml.py` and `mios_env.py` are strict-clean.
  - *Why:* `ast.parse` catches only syntax, so every type-confusion bug in the AI plane ships today; without it the resolver port has no typed contract to port against.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- deterministic Rust formatting so review effort goes to logic, not whitespace. (1 tasks)
- **AGY-1520**: Add a cargo fmt --check formatting gate plus a shared rustfmt.toml  (WS-TESTGOV | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo fmt --all --check` exits 0 on a clean tree and turns CI red on any unformatted hunk.
  - *Why:* Without a formatting gate every strangler-fig port PR carries incidental whitespace churn that hides the real diff and makes byte-parity review harder than it needs to be.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- encodes the port ordering so no fallback shim is deleted before its replacement is proven. (1 tasks)
- **AGY-1282**: Add `just template-gate`: run the toolchain in strangler-fig order with a no-delete-before-parity guard  (WS-TEMPLATE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `just template-gate` runs the four stages in order and is wired into CI; deleting a python producer without a green byte-parity fixture fails the guard; `just drift-gate` green.
  - *Why:* Without one ordered gate and a delete guard, a port can remove the working fallback before the Rust replacement is proven -- and scaffolding breaks for everyone with no obvious culprit.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- faithful port and bug fix stay separable, and the fix feeds the zero-hardcodes campaign. (1 tasks)
- **AGY-1530**: Golden-fixture mios-hardcode-lint (including its unanchored-allowlist bug) ahead of the Rust port  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A trycmd golden captures current hardcode-lint output across all violation classes, the Rust port matches it exactly, and a subsequent reviewed snapshot update encodes the anchored-allowlist fix.
  - *Why:* Porting a buggy tool without characterizing it first makes it impossible to tell a port regression from the pre-existing bug -- and the unanchored allowlist is currently hiding real `:80xx` violations that the zero-hardcodes campaign has to find.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- gives Python the lint/format/async-antipattern gate that Rust already has via clippy/rustfmt. (1 tasks)
- **AGY-1142**: Add a ruff lint + format drift-gate over the 123-module agent-pipe Python tree  (WS-DEBT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `ruff check` and `ruff format --check` run clean over `usr/lib/mios/agent-pipe` modulo the ratcheting ignore baseline, a drift-check enforces both, and the lint leg is wired into `just agent-pipe-check`.
  - *Why:* mypy sees types but not blocking-in-async calls, dead imports or format drift, so the exact antipattern class the runtime tasks are chasing keeps re-entering the async service unnoticed.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- gives the Python plane one ordered entrypoint so its gates run in a defined sequence rather than ad hoc. (1 tasks)
- **AGY-1141**: Add one fast-fail `just agent-pipe-check` gate DAG and wire it into the drift-gate and CI  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `just agent-pipe-check` runs the four gates in fail-fast order, a new drift-check invokes it and degrades open without the venv, the CI job exists, and the aggregate is green.
  - *Why:* Without one ordered target the per-tool gates run inconsistently between local and CI, so a contributor can land code that passes locally and fails the bake, and the WS-DEBT tasks have no defined sequencing backbone.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- gives the Rust plane the CI lint gate the shell plane never got. (1 tasks)
- **AGY-1404**: Add cargo build/test/clippy/fmt Just targets plus `check_native_lint` (the missing shellcheck-equivalent)  (WS-GUP | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `just native-lint` is green; `check_native_lint` appears in the drift-gate check list and fails a deliberately warning-ridden crate in `tests/drift-gate-negatives.sh`; clippy runs with `-D warnings`.
  - *Why:* The tech-debt map flags "no shellcheck CI", and every crate landing after this one would otherwise accrue unlinted `unwrap`/`panic` in system-critical paths with nothing to catch it.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- gives the Rust plane the shellcheck-equivalent MiOS has never had. (1 tasks)
- **AGY-1458**: Add mios-hardcode-lint to the Rust workspace and gate it with clippy -D warnings, fmt, cargo-deny/audit  (WS-ZEROHC | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo build`, `clippy`, `fmt`, `deny` and `audit` all pass for the crate under `-D warnings`; `unwrap`/`panic`/`todo` are denied and absent from the source; the crate is a workspace member sharing `Cargo.lock`; the gate steps run and are green.
  - *Why:* MiOS has no shellcheck CI at all; a compiled crate landing without clippy, fmt and supply-chain checks just relocates the unlinted surface from Python into Rust and adds a dependency tree nobody audits.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- gives the Rust tier one governed workspace with a pinned lockfile as its reproducibility SSOT. (1 tasks)
- **AGY-1116**: Complete the tools/native Cargo workspace and gate it with cargo-deny/cargo-audit  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo metadata` lists all 8 crates as members, `cargo deny check` and `cargo audit` pass and are wired as a gate, `Cargo.lock` is committed and staged explicitly, and the gate exists in both repos.
  - *Why:* Five crates currently ship with no lint, no lock and no advisory scan, and the incoming pyo3 ports would land into that same ungoverned space.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- gives the compiled tier the linting discipline the shell tier never got. (1 tasks)
- **AGY-1117**: Wire clippy -D warnings, rustfmt --check and cargo test as one Rust drift-gate  (WS-DEBT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo fmt --check`, `cargo clippy -- -D warnings` and `cargo test` all pass across both workspaces as ONE green drift-gate that goes red on a deliberately planted warning.
  - *Why:* MiOS has no shellcheck CI and no Rust lint gate either, so a panic/unwrap in a system verb can reach an image with nothing objecting.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- gives the growing Rust tier the dependency-integrity gate bash never had. (1 tasks)
- **AGY-1271**: Commit Cargo.lock as reproducibility SSOT and add a cargo-deny/audit supply-chain gate  (WS-TEMPLATE | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `Cargo.lock` is committed; `cargo deny check` + `cargo audit` run as a gate, green on the clean tree and RED on a banned-license or advisory-flagged dep; the gate SOFT-skips when the tools are not installed.
  - *Why:* Every crate added right now widens an unaudited transitive dependency surface with no lockfile in the tree -- so builds are not reproducible and a known-vulnerable or non-FOSS dep can land unnoticed.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- makes "every Python surface carries a characterization test" machine-enforced instead of true only for agent-pipe, so compiled/ported code has a parity oracle to be trusted against. (1 tasks)
- **AGY-1560**: Extend the sibling-test ratchet from agent-pipe to `tools/*.py` and `usr/libexec/mios/*.py` via a shrink-only grandfather baseline  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: adding a new untested `tools/` or `libexec` `.py` module trips the check; growing the grandfathered baseline fails; agent-pipe behavior is unchanged; `just drift-gate` and the negatives run green.
  - *Why:* 155 of MiOS's Python files -- two of its three Python surfaces -- can be edited or rewritten today with zero test obligation, so any port or refactor there has no failure signal at all.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- makes the Rust plane actually buildable and lint-gated so every downstream compiled-resolver task is verifiable. (1 tasks)
- **AGY-1151**: Register the 5 orphaned native crates as workspace members and add a fmt/clippy build-gate  (WS-RESOLVER | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `members[]` lists all 8 crate dirs; `cargo build --workspace` is green; `check_native_workspace_clean` is in the dispatch array and passes `just drift-gate`; `check_ssot_lint_equivalence` no longer depends on `|| true` to hide a missing build target.
  - *Why:* The crate WS-RESOLVER must extend does not compile as a workspace member and the ssot-lint twin gate is a silent no-op today, so the tree reports green on a check that never ran.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- one consolidated workspace with a single pinned Cargo.lock as the reproducibility SSOT for the whole native tier. (1 tasks)
- **AGY-1050**: Consolidate the two divergent Cargo workspaces (src/mios-rs/miosd + tools/native) under one root with shared workspace.dependencies  (WS-LANGX | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: one workspace root builds miosd and every native crate against a single `Cargo.lock`; shared deps are declared exactly once; `cargo test` and the drift-gate are green.
  - *Why:* Two workspaces double the build, cache and lint surface, let miosd's dependency versions drift from the native tier, and block both the single-stage Containerfile build and a workspace-wide version-sync gate.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- one workspace, one lockfile, one clippy/audit posture that every Rust port inherits. (1 tasks)
- **AGY-1068**: Consolidate the 8 tools/native crates into ONE cargo workspace with a committed Cargo.lock and cargo-deny/audit gates  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo build --workspace` builds all 8 crates from `tools/native/`; `cargo deny check` and `cargo audit` pass and run in CI; `cargo clippy --workspace -- -D warnings` is clean; exactly one `Cargo.lock` is committed; `just drift-gate` green.
  - *Why:* Five compiled tools currently build outside the workspace with no shared lockfile, no clippy, and no advisory scanning -- the bash they replace at least had shellcheck, so today's ports are less vetted than the scripts.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the FOSS-licensing posture encoded as machine-checked policy rather than as an assumption. (1 tasks)
- **AGY-1521**: Add a cargo-deny supply-chain gate covering licenses, bans, sources and advisories  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo deny check` passes on the current tree and fails on an injected GPL, duplicate, or yanked dependency; the check appears in the drift-gate's main() registration and in Forgejo CI.
  - *Why:* The compiled tier currently has no license or dependency-provenance story at all, so a copyleft-incompatible or yanked transitive crate can enter the shipped image with nothing to stop it.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the Python plane gets the static analysis the shell plane already has. (1 tasks)
- **AGY-1071**: Make ruff lint+format a mandatory Python drift-gate across libexec, lib and tools  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `ruff check` and `ruff format --check` run in CI and in `just drift-gate`; the S/B/E722 rule sets are active; a newly-added bare-except or `eval` fails the gate; the baseline is documented; the gate is green on the current tree.
  - *Why:* The Python half of the tree -- 122 libexec tools plus tools/ -- has zero static analysis today, so every injection, bare-except and dead-import fix in this campaign is a one-off with nothing preventing the next one.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the Python that stays Python gets a type guarantee on the SSOT-critical modules. (1 tasks)
- **AGY-1078**: Add a mypy --strict drift-gate seeded on the resolver, models and projectors  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mypy` runs in CI and `just drift-gate` over the strict include-set with zero errors; the resolver public API is fully annotated; a newly-added untyped function in an in-scope module fails the gate; the include-list ships with a documented shrink plan.
  - *Why:* The modules that decide what gets projected into `policy.json`, the kernel cmdline and the Quadlets are exactly where a wrong type silently corrupts an SSOT projection, and today nothing checks them.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the Rust tier gets the static gate the shell tier never had. (1 tasks)
- **AGY-1486**: Make `clippy -Dwarnings` + rustfmt the compiled plane's missing shellcheck, with panic/unwrap bans  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo clippy -- -D warnings` and `cargo fmt --check` are green and gate both CI and `just drift-gate` across both workspaces; the restriction lints are active in migrated crate roots; adding a stray `.unwrap()` to a verb fails the build; both repos carry the config.
  - *Why:* Ported verbs currently land with no static gate at all, so formatting drift and panic-on-`unwrap` paths enter the signed image unchallenged -- the exact defect class shellcheck would have caught in the bash they replaced.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the compiled resolver proves its env projection is lossless before bash is retired. (1 tasks)
- **AGY-1533**: proptest round-trip: typed serde config to MIOS_* and back is identity for the resolver-core crate  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test` round-trips generated typed configs through MIOS_* and back under proptest asserting identity, with failures shrinking to the minimal offending field.
  - *Why:* Retiring the bash resolver without a losslessness proof means a config field can silently degrade through the env projection, and the failure would only appear as a misbehaving service on a deployed host.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the eval removal at a security boundary is proven safe rather than hoped safe. (1 tasks)
- **AGY-1531**: Characterization golden for agent-pipe verb dispatch and the eval-on-agent-args path before hardening  (WS-TESTGOV | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A committed golden fixes the dispatch mapping for both legitimate and adversarial verbs; the hardened dispatcher passes it with zero `eval`; injection inputs are rejected under test.
  - *Why:* Dispatch is the boundary where untrusted agent arguments meet OS-control verbs, and rewriting it without a characterization oracle risks either reintroducing the injection surface or silently breaking a legitimate verb the agent plane depends on.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the governance surface itself is ported under proof, slice by slice. (1 tasks)
- **AGY-1526**: Capture a goldenfile master of full 98-drift-checks.sh stdout before any check is ported to miosd  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p miosd` diffs miosd output against the golden master; a ported check that changes its wording or drops a line fails until the golden is reviewed and updated.
  - *Why:* The drift-gate IS the enforcement plane -- porting it without a golden master risks silently dropping a check, which would leave a law unenforced while the gate still reports green.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the highest-recurrence drift class is caught pre-bake as a reviewable diff. (1 tasks)
- **AGY-1528**: Snapshot generated Quadlets with insta so digest-drift becomes an accept/review event  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo insta test` snapshots the rendered Quadlet set, removing an `@sha256` pin fails the snapshot, and the accepted `.snap` files are committed.
  - *Why:* This drift recurs constantly and is currently only discovered when the gate goes red mid-build, costing a regenerate-and-restage cycle every time instead of failing fast with a diff that shows exactly which pin was lost.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the one consolidated workspace every later clippy/test/deny gate depends on. (1 tasks)
- **AGY-1403**: Repair the fragmented tools/native Cargo workspace so all eight SSOT crates build as one graph  (WS-GUP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo build --workspace --manifest-path tools/native/Cargo.toml` compiles all 8 crates; `cargo metadata` lists every crate as a workspace member; the updated Cargo.lock is committed by staging explicit paths only.
  - *Why:* No workspace-wide clippy, test or deny gate can exist while five crates are invisible to the root manifest, and the drift-checks paper over it with per-crate builds that mask compile failures.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the one real compiled drift target gets its own regression floor before it grows. (1 tasks)
- **AGY-1527**: Add trycmd fixtures locking the miosd drift-check contract including the backfill-coverage FAIL path  (WS-TESTGOV | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p miosd` exercises both the pass and the fail drift-check paths through trycmd, with exit codes 0/1 and full output pinned.
  - *Why:* miosd is where the entire drift-gate is headed, and it currently has no test of its own -- so any change to its CLI surface or check logic can regress silently, and there is no suite for a later mutation gate to measure.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the one-canonical-name law is hardened against fuzzed SSOT input. (1 tasks)
- **AGY-1534**: proptest mios-ssot-walk for determinism, stable ordering and key-collision freedom  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p mios-ssot-walk` runs the determinism, ordering and collision invariants under proptest, and a synthetic colliding table fails and shrinks to a minimal case.
  - *Why:* The walk is the mechanical half of names-registry codegen, so a nondeterministic or colliding walk would produce a registry that silently maps two distinct SSOT facts onto one env var -- a Law 9 violation that the existing checks only catch for the shapes that happen to exist today.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the per-domain language-enforcement law is machine-checked against a policy actually recorded in SSOT. (1 tasks)
- **AGY-1064**: Settle the Law 14 target-language policy in SSOT so the drift-check matches the campaign's conditional Go allowance  (WS-LANGX | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the language policy is stated in `mios.toml [laws]` + ADR-0011 and the check's behavior matches it (Rust-only, or reading an SSOT allowlist key instead of the inline exception); `just drift-gate` green.
  - *Why:* Today the brief and the gate disagree -- the documented Go escape-hatch is an automatic build failure, so the conflict will surface mid-port as a red gate rather than as a decision.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the pinned lockfile becomes the dependency reproducibility SSOT every audit gate consumes. (1 tasks)
- **AGY-1487**: Commit `src/mios-rs/Cargo.lock` and build miosd with `--locked`  (WS-SBOM | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `src/mios-rs/Cargo.lock` is committed and not ignored; `cargo build --locked` builds miosd; bumping a dependency now requires an explicit lockfile update rather than happening implicitly; cargo-audit/vet/auditable have a fixed set to scan; both repos carry it.
  - *Why:* Without a committed lockfile the shipped daemon is non-reproducible and unauditable -- two bakes of the same commit can embed different dependency versions, and no advisory gate downstream can name what was actually built.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the proptest differential oracle that mechanizes the Global-Unification-Plan lossless-diff invariant. (1 tasks)
- **AGY-1015**: Add a proptest differential oracle proving mios-toml-core == userenv.sh over random mios.toml  (WS-LANGX | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p mios-toml-core` runs >=1000 proptest cases with zero key/value divergence vs userenv.sh; a seeded intentional bug (drop one short alias) shrinks to a minimal reproducing mios.toml; the suite runs in CI before the main drift gate.
  - *Why:* Example-based tests miss the edge-case value divergences that matter — one wrong resolved value silently breaks a Quadlet, which is precisely the recurring SSOT-projection drift class the gate keeps catching after the fact.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the resolver port becomes a measured deviation-from-golden exercise instead of a rewrite. (1 tasks)
- **AGY-1525**: Add insta snapshots of the userenv.sh MIOS_* env projection as the golden the Rust resolver must reproduce  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo insta test` produces a stable MIOS_* projection snapshot, and any resolver change that alters a key or value fails until `cargo insta accept` is run under review.
  - *Why:* A single wrong resolved value silently breaks a Quadlet at runtime with no build-time signal, so porting the resolver without a committed golden risks a fleet-visible regression that nothing in CI would catch.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the reusable golden-master pattern every strangler-fig verb port will copy. (1 tasks)
- **AGY-1524**: Stand up a trycmd CLI-snapshot harness pinning Rust mios-ssot-lint byte-for-byte to 97-ssot-lint.sh  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p mios-ssot-lint` runs the trycmd snapshot; changing the Rust output without updating the golden fails the test; the committed golden matches current 97-ssot-lint.sh output.
  - *Why:* Without an accept/review characterization oracle, every verb port is a hope-based rewrite, and the existing ad-hoc twin-diff cannot be reused by the other 143 libexec tools that still need porting.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the shellcheck-equivalent the Rust plane never had, plus a supply-chain story for the compiled tier. (1 tasks)
- **AGY-1016**: Add cargo fmt/clippy -Dwarnings plus cargo-deny/cargo-audit as native quality drift-gates  (WS-LANGX | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo clippy --workspace -- -D warnings` and `cargo deny check` pass on the repo; both new checks appear in the generated gate index and fail on an injected `unwrap()`/`panic!` or a banned-license crate; the negatives-before-main ordering is preserved.
  - *Why:* The tech-debt map records that MiOS has no shellcheck CI at all; as code moves to Rust, a panic or an unvetted transitive dependency would ship into the image with nothing checking it, and `Cargo.lock` would be a reproducibility SSOT nobody audits.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the strictly-stronger shellcheck the compiled tier needs, tuned so a verb cannot panic on bad config. (1 tasks)
- **AGY-1519**: Enforce cargo clippy -D warnings with restriction lints banning panic/unwrap in system verbs  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo clippy --workspace -- -D warnings` is green and blocks CI on any regression; `clippy::unwrap_used` and `clippy::panic` are denied workspace-wide; miosd/drift.rs contains no unjustified unwrap.
  - *Why:* The tech-debt map records that MiOS has no shellcheck-equivalent for its compiled tier, so panic-on-bad-config bugs that bash never guarded against are shipping unreviewed into binaries that run as system verbs.

### Domain: E-05 Test and CI governance: the quality gates that make compiled code trustworthy -- the version literal is single-sourced and dependency resolution is recorded, not re-resolved. (1 tasks)
- **AGY-1517**: Pin Cargo.lock as a reproducibility SSOT and move crate versions to workspace inheritance  (WS-TESTGOV | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo build --workspace --locked` succeeds with zero lockfile churn; check_version_ssot fails when any member Cargo.toml version differs from mios.toml's mios_version; a grep finds no literal `version = "` in any member manifest.
  - *Why:* A committed lockfile operationalizes SBOM-not-hardcode (dependency versions recorded at build rather than hand-pinned in source) and closes the TD-2 version-duplication drift class that currently lets one crate quietly ship the wrong version string.

### Domain: E-06 Test and documentation harness -- a new SSOT surface is discoverable cold, like `[ports]` and `[services]`. (1 tasks)
- **AGY-1348**: Document the `[units.*]` SSOT surface in the manual, ROADMAP and projection registry  (WS-SYSTEMD | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: ROADMAP carries a populated WS-SYSTEMD entry with task ids; the generated manual documents the `[units.*]` schema and the generator CLI; `[laws.projection_registry].surfaces` lists the unit generator and its check; `check_projection_registry` green.
  - *Why:* An undocumented generated surface drifts straight back to hand-editing, because the next agent has no way to learn that units are a projection at all.

### Domain: E-06 Test and documentation harness -- keeps the snapshot suites authoritative instead of accumulating orphan pending files that mask real drift. (1 tasks)
- **AGY-1550**: Add check_no_pending_snapshots + a single `just test-accept` golden-refresh entrypoint  (WS-TESTGOV | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A committed `*.snap.new` trips the check; `just test-accept` is the sole refresh path and leaves the tree clean; drift-gate + negatives green.
  - *Why:* A stale accepted snapshot silently blesses the exact regression the golden was created to catch, and there is currently no way to tell an accepted golden from an abandoned one.

### Domain: E-06 Test and documentation harness -- makes characterization goldens deterministic so the byte-parity strategy for the Rust port is trustworthy. (1 tasks)
- **AGY-1549**: Add a shared golden-output normalizer (scrub $ROOT/timestamps/PIDs; pin LC_ALL/TZ/SOURCE_DATE_EPOCH)  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The same producer run twice from two different runner paths yields byte-identical normalized output; the goldenfile-98 and insta snapshot tasks consume the shared normalizer; no committed golden contains a raw absolute path, timestamp or PID.
  - *Why:* Without it every golden this workstream creates is flaky-red on path/time differences, and a flaky parity net gets disabled -- taking the safety out of the whole bash->Rust migration.

### Domain: E-06 Test and documentation harness -- makes the negatives harness real mutation testing rather than a name-substring check. (1 tasks)
- **AGY-1556**: Add check_negatives_are_effective: each test_ fn must inject, assert-FAIL, restore, assert-PASS  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A stubbed always-pass `test_` fn trips `check_negatives_are_effective`; all 89 existing negatives satisfy the structural contract; drift-gate green.
  - *Why:* An inert negative gives false assurance that a fitness-function is guarded -- the gate can silently lose its ability to fail and the harness still reports full coverage.

### Domain: E-06 Test and documentation harness -- records the decision and proves, by test, that every migration slice degrades open. (1 tasks)
- **AGY-1428**: Write the compiled-resolver ADR and the toggles-all-off reversibility negative tests (AGY-479..730 lineage)  (WS-GUP | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the ADR is committed in both repos; a toggles-all-off negative test proves bit-for-bit bash-path equivalence to the golden; ROADMAP reflects the compiled continuation; the full drift-gate suite is green in both toggle states.
  - *Why:* An untested rollback path is an assumption, not a contract -- and an unrecorded migration leaves the next agent unable to tell which resolver is authoritative or why.

### Domain: E-06 Test and documentation harness -- turns "skipped here, runs there" from an unverified claim into a gated fact. (1 tasks)
- **AGY-1555**: Add check_skip_list_covered: prove every pre-bake-skipped agent-pipe test runs in the venv build-job gate  (WS-TESTGOV | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Removing a skipped test from the venv step trips `check_skip_list_covered`; mismatched GitHub/Forgejo skip sets fail; drift-gate + negatives green.
  - *Why:* Eight agent-pipe tests -- covering redaction, admission, vector and gateway paths -- may be running nowhere at all, and the two publishers already disagree about which are skipped.

### Domain: E-06 Test and documentation harness: negative self-tests, coverage, doc integrity -- a negative test must exercise the shipped gate, not a reimplementation of it. (1 tasks)
- **AGY-1711**: Rewrite the 64/65/66 negative-tests to inject into real fixtures and call the real checks  (WS-TEST | P1 | M)  [BROKEN]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each test runs `bash automation/38-drift-checks.sh check_<name>` against an injected fixture and asserts non-zero, then asserts zero on restored HEAD; deleting any of checks 64/65/66 makes the harness FAIL; `automation/tests/test-drift-gates.sh` no longer exists.
  - *Why:* the current harness proves nothing about the three safety nets while occupying the slot where real proof would live -- the definition of a false green.

### Domain: E-06 Test and documentation harness: negative self-tests, coverage, doc integrity -- every test that exists actually runs, and coverage only goes up. (1 tasks)
- **AGY-1079**: Wire the scattered libexec test_*.py into a pytest + coverage drift-gate with a ratcheting floor  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `pytest usr/libexec/mios` runs all 10 test files inside the drift-gate; `--cov-fail-under` enforces a floor matching today's measurement; adding a large untested tool trips `check_module_test_coverage`; `just drift-gate` green.
  - *Why:* Eight of the ten existing libexec test files never execute in CI, so they can rot to failing without anyone knowing -- and the Rust ports are supposed to characterize against them.

### Domain: E-06 Test and documentation harness: negative self-tests, coverage, doc integrity -- makes "every gate proves it can fail" mechanical instead of hand-listed. (1 tasks)
- **AGY-1541**: Ratchet check_negative_test_coverage to auto-derive its required set from the gate registry  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Adding a new `check_*` with no negative test fails `check_negative_test_coverage`; the required set is derived from defined checks rather than a hand list; exemptions live in a shrink-only roster.
  - *Why:* The 42-item list is already stale relative to 123+ checks, so an unknown number of fitness-functions today have never been proven capable of failing.

### Domain: E-06 Test and documentation harness: negative self-tests, coverage, doc integrity -- makes the test layout mirror the package so collection, coverage and the sibling-test gate all agree. (1 tasks)
- **AGY-1145**: Relocate the 157 flat test_mios_*.py into a mirrored tests/ tree and repoint the sibling-test drift-check  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: all 157 tests live under `tests/` mirroring `mios_pipe`, the sibling-test drift-check resolves the mirrored layout, pytest collects and passes the full suite, and the drift-gate is green.
  - *Why:* The flat directory forces subprocess-per-file execution and `sys.path` hacks, and the location-coupled drift-check actively blocks any package reorganization until it is repointed.

### Domain: E-06 Test and documentation harness: negative self-tests, coverage, doc integrity -- proves the Law 16 gate can actually FAIL, on the exact path the build uses. (1 tasks)
- **AGY-1269**: Add a generative end-to-end conformance negative test to the drift-gate harness  (WS-TEMPLATE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The negative test shows a corrupted template caught by the real conformance gate and a clean scaffold of every registered type passing; it runs in the negatives phase before the main gate.
  - *Why:* The compiler self-check and the live conformance gate can drift apart, and when they do the gate reports green on files the scaffolder is producing wrong -- a green gate that enforces nothing.

### Domain: E-06 Test and documentation harness: negative self-tests, coverage, doc integrity -- so an arriving agent reads the current topology instead of re-deriving the retired one. (1 tasks)
- **AGY-1402**: Sync ADR-0010/0011, the in-file AI-hints and the auto-memory to name miosd  (WS-DOTFILES | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: ADR-0010/0011 and the projector file headers describe miosd rather than mios-theme-render; the `[migration]` toggle is documented; no doc claims the Python engine is authoritative.
  - *Why:* Stale ADRs and AI-hints pointing at a deleted engine send both operators and future agents down the wrong path, which is how a "migrated" surface quietly gets a second projector re-added.

### Domain: E-07 The drift-gate as the enforcement plane -- `mios-ssot-regen` becomes a trustworthy regenerator whose failures are visible. (1 tasks)
- **AGY-1029**: Absorb mios-ssot-regen orchestration into a miosd ssot-regen subcommand with real exit aggregation  (WS-LANGX | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd ssot-regen` regenerates the same ai/v1 manifests plus roadmap and gate indices with byte-identical output versus the bash, but exits non-zero if any generator fails (no silent `|| true`); drift-gate green; ratchet decremented.
  - *Why:* A generator can fail today and the orchestrator still reports success, so a broken projection is committed and only surfaces later as a red drift-gate with no clue which generator produced it.

### Domain: E-07 The drift-gate as the enforcement plane -- a check flags only what it claims to flag, so its green means something. (1 tasks)
- **AGY-1694**: REFINEMENT -- Fix the emission check to its true intent instead of naive-emitting ~500 vars  (WS-NAME | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: 0 GENUINE referenced-but-not-emitted remain, categories A-D no longer appear in the output, the userenv twins stay identical (drift-27), and there is a negative test per category -- a Cat-A `_cfg_num` var, a Cat-B sentinel and a Cat-D `.ps1` var each proving they are correctly NOT flagged, plus a Cat-E var proving a real orphan IS flagged until emitted.
  - *Why:* naive-emitting ~500 vars to silence the check would bloat every shell's environment with values that are already SSOT-sourced, permanently break the deliberate absent-value test sentinels, and convert a real invariant into noise nobody reads.

### Domain: E-07 The drift-gate as the enforcement plane -- a hand-edited unit fails exactly like a drifted quadlet. (1 tasks)
- **AGY-1340**: Run mios-unit-gen in the build and enforce it with a `check_units_generated` drift-gate  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The build phase regenerates units from SSOT; `mios-unit-gen --check` runs bare and deterministically and turns RED on a deliberate hand-edit; `check_units_generated` appears in the gate index and in `main()`; the negatives-before-main-gate CI ordering still holds; drift-gate green.
  - *Why:* A generator with no gate is decorative — without this, the first hand-edit to a generated unit is silently overwritten on the next build or silently persists, and 'derive, don't duplicate' stays an unenforced convention.

### Domain: E-07 The drift-gate as the enforcement plane -- closes a gate that is currently blind to most crates, including miosd. (1 tasks)
- **AGY-1051**: Generalize the version-sync drift-check to walk every Cargo workspace member instead of a hardcoded 3-path list  (WS-LANGX | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: setting any crate, including miosd or a newly-added port crate, to a non-SSOT version makes the check fail; the check is green on a correct tree.
  - *Why:* A hand-maintained manifest list rots as ports add crates, so the exact gate meant to catch version drift is the thing carrying the drift; miosd's version is unchecked today.

### Domain: E-07 The drift-gate as the enforcement plane -- closes the fail-open hole that lets security and law checks pass by being un-runnable. (1 tasks)
- **AGY-1101**: Convert the drift-gate's degrade-open python3/tool skips into hard failures for security and law checks  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CI runs with `MIOS_DRIFT_REQUIRE_TOOLS=1`; removing the interpreter or `mios_tools` turns the security/law checks RED rather than skipped; benign optional checks still degrade-open; `just drift-gate` green.
  - *Why:* A security gate that silently passes when its runtime is missing enforces nothing — the whole Python-hardening campaign is void if the gate policing it can be no-op'd by an absent interpreter in one CI image change.

### Domain: E-07 The drift-gate as the enforcement plane -- decouples the gate from projector implementation language so ports become atomic. (1 tasks)
- **AGY-1100**: Introduce a stable mios-generate dispatch so the drift-gate stops hardcoding python3 tools/generate-*.py  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The gate and build invoke `mios-generate <name>` rather than raw `python3 generate-*.py`; swapping a projector's backing implementation requires no gate edit; every projector `--check` gate passes through the dispatcher; `just drift-gate` green.
  - *Why:* Without this indirection each of the ~8 Rust-port tasks must patch `98-drift-checks.sh` itself, and a mid-port language straddle can leave the gate validating the old implementation while the build ships the new one.

### Domain: E-07 The drift-gate as the enforcement plane -- eliminates the highest-frequency false-green class so a green gate means the checks actually ran. (1 tasks)
- **AGY-1554**: Add check_no_silent_tool_skips: gated checks must fail closed under MIOS_DRIFT_REQUIRE_TOOLS=1  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: With `MIOS_DRIFT_REQUIRE_TOOLS=1` and python3/tomllib/shellcheck stubbed absent, the affected checks FAIL rather than skip; the negative proves the fail-closed path; drift-gate stays green when the tools are present.
  - *Why:* A green drift-gate on a tool-poor runner is a lie -- real violations merge because the check that would have caught them quietly returned 0.

### Domain: E-07 The drift-gate as the enforcement plane -- every generated projection is regenerated-or-red, never quietly stale. (1 tasks)
- **AGY-1566**: Gate AI-hint manifest freshness so `manifest.json` stops carrying stale version snapshots  (WS-FLOAT | P2 | S)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: editing a script without regenerating its manifest trips the new check; every manifest is byte-fresh; grepping the manifests for `v1.32` returns nothing.
  - *Why:* the manifests are the AI-hint layer's view of the tree, so a stale snapshot re-teaches an agent the exact literal the campaign just purged.

### Domain: E-07 The drift-gate as the enforcement plane -- makes the strangler-fig "delete the slice once rerouted" step a machine-enforced fitness function instead of a convention. (1 tasks)
- **AGY-1046**: Add `check_langx_shim_retirement`: a rust-defaulted verb may not keep a fat bash body  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the check passes on the current tree, fails when a rust-defaulted verb still has a fat bash body, and fails when a retired tool reappears carrying logic; the generated gate index lists it; Law 15 mirrored in mios-bootstrap.git.
  - *Why:* Without it, a verb defaulted to Rust can silently keep a divergent bash body that a rollback or a `[migration]` flip re-activates, so the two implementations drift apart unnoticed and the ratchet never actually falls.

### Domain: E-07 The drift-gate as the enforcement plane -- move the last line of defense that aborts insecure images into typed, testable code keyed to the `[laws]` numbering SSOT. (1 tasks)
- **AGY-997**: Port 99-postcheck.sh's 19 build-abort invariants to a native `miosd postcheck` fitness-function suite  (WS-LANG-AUTO | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd postcheck` reproduces all 19 checks with byte-identical pass/fail output against golden fixtures, 99-postcheck.sh is under 15 lines, a deliberately-broken invariant still aborts the build, and `cargo test` plus `just drift-gate` are green.
  - *Why:* This is the largest untargeted build phase and the only thing standing between a broken invariant and a published insecure image; leaving 810 lines of bash as the final gate while everything around it hardens is the biggest coverage hole in the domain.

### Domain: E-07 The drift-gate as the enforcement plane -- one byte-level check per generated artifact, with no hidden coupling constraining the generator. (1 tasks)
- **AGY-1571**: Fold drift-checks 28 and 52 into `check_globals_generated` and delete their literal parsers  (WS-PORTFLOAT | P2 | S)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: 28/52 delegate or are retired with 130 still covering them; `render-globals.py` carries no formatting workaround for either; the negatives still catch a hand-edit to `globals.sh`/`globals.ps1`.
  - *Why:* the coupling already cost two CI round-trips and it blocks AGY-1169, which stays open until the renderer can choose its own output format.

### Domain: E-07 The drift-gate as the enforcement plane -- one definition per architectural Law, consumed by both enforcement call sites, so a Law cannot mean two different things. (1 tasks)
- **AGY-998**: Collapse the Law checks duplicated across 99-postcheck and 98-drift-checks into one native mios-laws module  (WS-LANG-AUTO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each architectural Law is defined in exactly one native module, postcheck and drift both invoke it, deleting either bash copy leaves enforcement byte-identical, and the drift-gate is green.
  - *Why:* Two independent bash implementations of the same Law already differ in edge cases, so the answer to "does this tree obey Law 6?" depends on which gate you ask — the precise duplicated-parallel-logic smell the campaign exists to remove.

### Domain: E-07 The drift-gate as the enforcement plane -- one gating check proves the compiled resolver has not diverged from either legacy twin during the migration window. (1 tasks)
- **AGY-1171**: Extend check_resolver_twin_equivalence/parity to a three-way crate==python==bash assertion  (WS-RESOLVER | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: check-resolver-twin.py asserts crate==python==bash when the binary exists and python==bash otherwise; `check_resolver_twin_equivalence` stays gating and green; `check_resolver_twin_parity` includes the crate in its AI-set diff.
  - *Why:* During the migration window three resolvers are live at once; without the third leg in the existing gate, a crate-only divergence ships unnoticed on hosts that have the binary.

### Domain: E-07 The drift-gate as the enforcement plane -- one globally-identifiable number per pipeline element so OCI layer = stage = step = check. (1 tasks)
- **AGY-428**: Number drift-gate checks inline with the scripts under one global 0-99 system  (WS-NUMBER | P2 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a single numbering scheme spans scripts, stages and checks; gate output shows a check's number matching the stage it guards; inserting a new check leaves existing numbers unchanged.
  - *Why:* With four counters, a red "(57)" in the log cannot be traced to the build stage that produced the drift without reading the source, which slows every gate failure triage.

### Domain: E-07 The drift-gate as the enforcement plane -- remove the incomplete-tree false-drift class that repeatedly reddens the gate during the OCI bake. (1 tasks)
- **AGY-994**: Replace build.sh's git-reset + reproject dance with `miosd drift --prepare` keyed on $ROOT/$CTX  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd drift --prepare` reprojects the three gitignored SSOT files unconditionally from mios.toml, drift-checks 92/93/95 pass in both the incomplete-tree bake and the pristine-checkout CI job, build.sh invokes it as a single step, and nothing depends on `git reset` succeeding.
  - *Why:* This exact sequence is a documented, recurring bake failure: when git misbehaves in the incomplete work tree the projections are stale and the gate reports drift that does not exist, burning full bake cycles on a phantom.

### Domain: E-07 The drift-gate as the enforcement plane -- retires gates that exist only to police a duplication the compiled resolver removes. (1 tasks)
- **AGY-1427**: Fold the two resolver-twin gates into one golden-anchored check_resolver_parity and delete the scaffolding  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: one `check_resolver_parity` replaces both twin checks; `check-resolver-twin.py` no longer exists; drift-gate-index ordinals stay dense (`check_pipeline_numbering` green); parity holds in both toggle states.
  - *Why:* Carrying two twin-equivalence gates past the cutover means every future resolver change must satisfy three overlapping definitions of correctness, and the gate index keeps growing with checks that guard nothing.

### Domain: E-07 The drift-gate as the enforcement plane -- starts porting the checks themselves to native Rust so the gate stops being fragile bash, without a risky big-bang cutover. (1 tasks)
- **AGY-1459**: Wire the Rust mios-hardcode-lint into drift-gate 98 as a strangler shim with a dual-run parity window  (WS-ZEROHC | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `check_no_hardcode` runs the Rust binary when built and the Python tool otherwise; the parity window logs zero divergence across the repo; flipping the `[migration]` toggle switches implementation without a rebuild; drift-gate green under both settings.
  - *Why:* A hard cutover of a gate check has no rollback short of reverting a build; without the dual-run window and the SSOT toggle, any behavioral gap in the new binary reds (or worse, greens) the whole tree with no way to bisect which implementation was at fault.

### Domain: E-07 The drift-gate as the enforcement plane -- the 'silently dead on first boot' class becomes a gate failure, not a field report. (1 tasks)
- **AGY-1352**: Add `check_preset_roster_complete`: no orphan enable lines, no undeclared MiOS unit  (WS-SYSTEMD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Deleting any `mios-*.service` preset line, or renaming a unit without updating the preset, turns the gate RED naming the exact unit; adding the missing decision returns it green; the check is registered in both the negatives suite and the main gate.
  - *Why:* The documented `mios-ai-firstboot` incident is precisely this orphan/undeclared-unit class; the existing dangling-ref task covers `Wants=`/`After=` inside units, leaving the enablement-roster-vs-unit-files axis completely ungated.

### Domain: E-07 The drift-gate as the enforcement plane -- the last un-generated unit surface gets a numbered, gated invariant instead of a convention. (1 tasks)
- **AGY-1344**: Register Law 17 UNITS-FROM-SSOT in `[laws]` with its enforcing checks wired  (WS-SYSTEMD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `[laws]` contains id=17 with the correct `enforced_by` mapping; the law renders in the generated manual; the cross-repo parity checks 22 and 27 are green; drift-gate green.
  - *Why:* A rule enforced only by two checks nobody has tied to a law is bypassable by anyone who deletes the checks; laws with a single numbering SSOT are how Laws 1-16 stopped regressing, and the unit surface has no such anchor today.

### Domain: E-07 The drift-gate as the enforcement plane -- the numbering SSOT is machine-enforced, not maintained by convention. (1 tasks)
- **AGY-429**: Gate the unified numbering against duplicates and gaps  (WS-NUMBER | P3 | S)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the check flags an injected duplicate number and an injected gap, and is green on the clean tree.
  - *Why:* The unified scheme from AGY-428 decays back into four counters the first time two people pick the same free number and nothing objects.

### Domain: E-07 The drift-gate as the enforcement plane -- the regeneration ordering constraint becomes executable rather than documented. (1 tasks)
- **AGY-1575**: Enforce `tools/sync-generated.sh` in CI instead of trusting contributors to run the renderers in order  (WS-PORTFLOAT | P2 | S)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a deliberately stale manifest fails the new step with the precise file list; the step is green on a synced tree; both workflows carry it.
  - *Why:* stale-artefact failures cost more CI round-trips than any real defect during the port campaign, and each one arrives as five separate unhelpful "X is stale" gate messages.

### Domain: E-07 The drift-gate as the enforcement plane -- turn "minimize loose scripts" into an enforced fitness function that can only move one direction. (1 tasks)
- **AGY-1017**: Add a monotonic bash-tool ratchet drift-check over usr/libexec/mios  (WS-LANGX | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the check prints live count vs ceiling and passes at baseline; adding one new bash tool under `usr/libexec/mios` makes it fail; each later port lowers the ceiling by one with the gate staying green; per Law 15 the SSOT key is mirrored in mios-bootstrap.git if that repo carries the surface.
  - *Why:* Without a ratchet, the campaign is reversible by accident: a single new hand-written bash tool erases a port's progress with nothing flagging it, and the 145-script surface never provably shrinks.

### Domain: E-08 Global Unification Plan -- collapses enforcement of the ~79 version-dupe pairs into one compiled gate so a version is declared once. (1 tasks)
- **AGY-1418**: Expand Rust mios-version-check to subsume the whole check_version_ssot surface, then demote the bash check  (WS-GUP | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust binary raises every violation `check_version_ssot` can raise (verified by seeding a mismatch in each surface) and the bash check delegates under the toggle with its own path still green; negatives cover os-release and Cargo.toml drift.
  - *Why:* The version family is the largest value-dupe cluster in the tree and its only enforcement is a sprawling bash function nobody can safely extend -- so new version surfaces get added ungated.

### Domain: E-08 Global Unification Plan -- delivers the auto-derived minimal key library that the ~200 manual userenv.sh tuples were always standing in for. (1 tasks)
- **AGY-1424**: Emit a generated minimal key-library from mios-resolve and delete userenv.sh's hand-maintained tuples  (WS-GUP | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `key-library.generated.tsv` is produced by mios-resolve and consumed by `97-ssot-lint.sh`; the manual `_ssot_lint_ports_dummy` array is gone from both userenv.sh copies; ssot-lint and var-closure are green.
  - *Why:* Hand-maintained key tuples go stale the moment a key is added elsewhere, and today the lint's own allowlist is one of them -- so the linter's notion of the namespace silently diverges from the resolver's.

### Domain: E-08 Global Unification Plan -- eliminates a third, ungated serialization of the namespace so the lossless invariant covers what services actually read. (1 tasks)
- **AGY-1431**: Bring `/etc/mios/install.env` under the one resolver with a lossless parity and quoting-safety gate  (WS-GUP | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: install.env is provably a projection of the resolved namespace (parity check green); a planted `$`-bearing or space-bearing value fails the quoting-safety invariant; the check is registered in `main()`.
  - *Why:* install.env feeds systemd units and podman at first boot -- if the namespace collapses while install.env tracks a stale SSOT, services read values the resolver stopped emitting, and the lossless gate reports green throughout.

### Domain: E-08 Global Unification Plan -- makes the lossless invariant hold in CI, which every later namespace-collapse step depends on. (1 tasks)
- **AGY-1421**: Normalize root paths in mios-env-snapshot so a differing `$ROOT`/`$HOME` can never false-drift the lossless gate  (WS-GUP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `env-baseline.txt` contains no host-specific absolute prefixes; `check_resolved_env_lossless` passes from two different `$ROOT`/`$HOME` locations; a negative test proves a genuine value change still fails; both userenv.sh copies stay byte-identical.
  - *Why:* A baseline embedding its capture host's path is a latent CI-red that will block every future resolver change the first time the gate runs off that machine.

### Domain: E-08 Global Unification Plan -- pins the differential oracle that every lossless resolver-port step diffs against. (1 tasks)
- **AGY-1559**: Characterization golden locking mios-env-snapshot root-path/PID/timestamp normalization  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A leaked absolute path, PID or timestamp in the snapshot fails the golden; the live snapshot equals the golden across two different runner paths; drift-gate green.
  - *Why:* If snapshot normalization drifts, every downstream byte-parity gate fails non-deterministically and the GUP losslessness invariant stops being provable at all.

### Domain: E-08 Global Unification Plan -- produces the ground-truth shrink map without which no key can be safely retired. (1 tasks)
- **AGY-1429**: Build the three-set namespace census and an orphan-consumer / dead-key drift-gate  (WS-GUP | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `namespace-census.tsv` is generated and committed; `check_namespace_census` is registered in `main()` and green; a deliberately planted `MIOS_TYPO_XYZ` read in a `*.service` fails the gate; `cargo test` and `just drift-gate` green.
  - *Why:* With no way to distinguish a live key from a dead one, every shrink is a guess -- and a consumer referencing an unresolved alias fails silently at runtime instead of at the gate.

### Domain: E-08 Global Unification Plan: collapse the 2523-key MIOS_* namespace to one-value-derived -- collapses one of the three parallel resolvers into a typed schema and mechanizes the lossless-diff gate. (1 tasks)
- **AGY-1125**: Replace kernel/config's ad-hoc readers with a typed settings model proven byte-equal to userenv.sh  (WS-DEBT | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the typed resolver's `MIOS_*` projection is byte-identical to userenv.sh across the corpus, the module is mypy-strict clean, the no-raw-`MIOS_TOML` gate (check 51) is still green, and new keys exist in both repos.
  - *Why:* Three resolvers reading one SSOT means a wrong value silently reaches a Quadlet, and nothing today proves the agent-pipe arm agrees with the shell one.

### Domain: E-08 Global Unification Plan: collapse the 2523-key MIOS_* namespace to one-value-derived -- extends the one-value-derived rule to the one repo every other GUP task ignores. (1 tasks)
- **AGY-1437**: Law-15: mirror the derivation-table SSOT into mios-bootstrap.git and audit its hardcoded namespace literals  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no un-fallback-guarded namespace literal remains in `bootstrap.ps1` or `bootstrap.sh`; the shared SSOT surface is byte-identical across `mios.git` and `mios-bootstrap.git`; every commit stages explicit paths only (never `git add -A`).
  - *Why:* Law 15 requires shared SSOT surfaces to be verified and mirrored in BOTH repos; the namespace collapse is exactly such a surface, so bootstrap silently keeps serving retired spellings after the waves land.

### Domain: E-08 Global Unification Plan: collapse the 2523-key MIOS_* namespace to one-value-derived -- keeps the byte-exact lossless diff trustworthy on the cross-platform checkout the resolver is actually developed in. (1 tasks)
- **AGY-1436**: Enforce LF/no-BOM/trailing-newline determinism for the Rust resolver, golden fixtures and env-baseline on a Windows checkout  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a deliberately CRLF/BOM-injected fixture is normalized on ingest and produces unchanged resolved output; a CRLF-committed baseline FAILS the new normalization assertion; the drift-gate is green on both an LF checkout and a CRLF checkout.
  - *Why:* The resolver is explicitly cross-platform and this very tree lives on Windows; a compiled resolver reading files byte-for-byte will false-drift on CRLF/BOM, and the bash tools only ever escaped this partially via `LC_ALL=C`.

### Domain: E-08 Global Unification Plan: collapse the 2523-key MIOS_* namespace to one-value-derived -- makes alias retirement provably safe by knowing which aliases Python is load-bearing on. (1 tasks)
- **AGY-1439**: Map and guardrail the ~738 direct os.environ['MIOS_*'] short-alias reads in the Python consumers  (WS-GUP | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the consumer map cross-references the census retire-candidate column; the highest-risk direct alias reads resolve through the typed accessor; a newly introduced raw alias read is flagged by the lint; drift-gate green.
  - *Why:* 738 alias-bound reads are the tripwire that turns a safe-looking retirement wave into a runtime regression that presents as an empty config value rather than a crash.

### Domain: E-08 Global Unification Plan: collapse the 2523-key MIOS_* namespace to one-value-derived -- makes the losslessness invariant that guards every collapse step auditable instead of overridable by one env var. (1 tasks)
- **AGY-1435**: Replace the MIOS_ENV_BASELINE_BUMP=1 blanket whitewash with a reviewed baseline-regen tool + an added/removed changes manifest  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `env-baseline.txt` can only be regenerated through `just baseline-regen`; a bump whose `env-baseline.changes.tsv` disagrees with the real added/removed set FAILS `check_resolved_env_lossless`; the full drift-gate is green.
  - *Why:* A lossless gate whose only bypass is an unaudited env var is not lossless. Mid-collapse, an accidentally dropped key ships silently and the regression surfaces later as a missing runtime value with no commit to bisect to.

### Domain: E-08 Global Unification Plan: collapse the 2523-key MIOS_* namespace to one-value-derived -- removes the last place the namespace is described by hand instead of projected. (1 tasks)
- **AGY-1440**: Generate naming-unification.md FROM the derivation table so the human-facing key registry stops being hand-maintained  (WS-GUP | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `naming-unification.md` is produced by the generator and `--check` exists; a hand-edit to the doc FAILS the new drift-check; the regenerated doc is staged by explicit path; drift-gate green.
  - *Why:* A naming doc the registry generator explicitly ignores is a guaranteed divergence surface -- agents and operators read it as authoritative while the real derivation has already moved.

### Domain: E-08 Global Unification Plan: collapse the 2523-key MIOS_* namespace to one-value-derived -- this is the demolition step that turns the GUP machinery into a measurably smaller namespace. (1 tasks)
- **AGY-1438**: Execute the staged, lossless-gated alias RETIREMENT waves that actually shrink the 2523-key namespace  (WS-GUP | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the namespace key count measurably drops wave over wave; each wave's baseline diff equals exactly its intended removals; the lossless, census and bijection gates are green after every wave; each wave reverts independently.
  - *Why:* Without a gated demolition campaign the GUP ships tooling and the duplication the operator flagged stays on disk -- 2523 keys of hand-maintained surface that every new consumer keeps binding to.

### Domain: E-08 Global Unification Plan: collapse the MIOS_* namespace to one-value-derived -- converts the authoritative resolver from hand-maintained code to SSOT-derived data. (1 tasks)
- **AGY-1407**: Make `mios_toml.py::get_aliases` read the derivation table instead of its if/elif ladder  (WS-GUP | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `get_aliases` contains no per-section if/elif ladder; `names.generated.txt` and `env-baseline.txt` regenerate byte-identical; `check_names_registry`, `check_resolver_twin_equivalence` and `check_resolved_env_lossless` are all green.
  - *Why:* Until the authoritative resolver consumes the table, the table is unproven documentation and the compiled crates would adopt rules nothing validates.

### Domain: E-08 Global Unification Plan: collapse the MIOS_* namespace to one-value-derived -- every SSOT key has exactly one live consumer, and version facts are declared once. (1 tasks)
- **AGY-1573**: Wire or delete the inert `[migration]` and `[versions]` SSOT tables  (WS-PORTFLOAT | P2 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every key in both tables has a consumer a grep can find, or the tables no longer exist; a newly added inert top-level table fails the gate.
  - *Why:* inert SSOT is worse than absent SSOT -- an operator flips `use_rust_resolver_*` in the configurator, nothing changes, and trust in the one config surface is gone.

### Domain: E-08 Global Unification Plan: collapse the MIOS_* namespace to one-value-derived -- installs the losslessness safety net that every later resolver rewrite is measured against. (1 tasks)
- **AGY-1405**: Freeze the resolver output as versioned golden-master fixtures before any port  (WS-GUP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a cargo test snapshot-compares a live `mios-env-snapshot` run to `env-baseline.txt` and passes byte-identical; the `.snap` fixtures are committed via explicit path staging; the note records the insta review flow.
  - *Why:* The resolver is untested shell plus Python emitting 2475 keys; without a frozen golden, any port silently changes a key nobody notices until a service reads the wrong value at boot.

### Domain: E-08 Global Unification Plan: collapse the MIOS_* namespace to one-value-derived -- one compiled library so the derivation logic cannot re-diverge across tools. (1 tasks)
- **AGY-1408**: Grow mios-ssot-walk from a stub into the one shared native walk + derivation library  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: mios-ssot-walk exposes `walk`/`process_val`/`alias_lookup` with `cargo test -p mios-ssot-walk` green; the crate is a workspace member; `alias_lookup` reproduces the `alias-derivation.tsv` rows.
  - *Why:* The empty stub is exactly why `generate-names-registry` shipped its own incomplete `alias_for`; without a real shared lib every new compiled tool re-implements the walk and re-introduces the divergence.

### Domain: E-08 Global Unification Plan: collapse the MIOS_* namespace to one-value-derived -- the structural core: one table defines every dotted-path -> `MIOS_*` derivation. (1 tasks)
- **AGY-1406**: Extract the get_aliases prefix-family and per-key rules into ONE declarative derivation-graph table  (WS-GUP | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `alias-derivation.tsv` exists and, parsed by a check script, reproduces the EXACT alias set `get_aliases` emits for every path in `names.generated.txt` (503 rows) with zero diff; the file is mirrored in both repos.
  - *Why:* Three divergent copies of the same derivation logic mean the Rust and Python name registries already disagree, and no compiled resolver can be written until there is one authoritative statement of the rules.

### Domain: E-09 One value, one name -- makes the de-dup fitness function fast, typed and panic-free so it stays permanently enforced. (1 tasks)
- **AGY-1423**: Compile the forbid-new-value-duplicate rule into mios-ssot-lint reading value-aliases.tsv  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: mios-ssot-lint reproduces `check_no_duplicate_value_key`'s verdicts against seeded dup and allowlisted cases, runs under `clippy -D warnings` with no unwrap/panic, and the gate delegates to it under the toggle.
  - *Why:* The rule currently lives as a Python heredoc inside bash -- slow, untypeable, untestable in isolation, and one of the surfaces the minimize-loose-scripts directive targets.

### Domain: E-09 One value, one name -- removes a 3x name multiplication so each port has a single representation across the namespace. (1 tasks)
- **AGY-1420**: Collapse the ports triple-emission (`MIOS_PORT_x` / `MIOS_x_PORT` / `MIOS_PORTS_x`) to a canonical+alias minimum  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: emitted names per port are reduced to the referenced minimum with the remainder declared derive/keep-distinct; `check_var_closure` green; the env-baseline shrink reviewed; `check_container_ports` and `check_no_bare_port_literals` still green.
  - *Why:* Three names per port means three chances for a consumer to read the one that a future refactor stops emitting, and it inflates the very namespace the GUP is trying to shrink.

### Domain: E-09 One value, one name -- turns the campaign's keystone fitness function from decorative into enforcing. (1 tasks)
- **AGY-1422**: Make check_no_duplicate_value_key actually call `_violation` instead of unconditionally passing  (WS-GUP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the check raises `_violation` on an undeclared value-dup and is green on the current tree; a seeded undeclared dup key fails in `tests/drift-gate-negatives.sh`; allowlisted pairs still pass.
  - *Why:* A gate that can never fail is worse than no gate -- the whole de-duplication campaign is currently reporting success while new duplicate keys land unimpeded.

### Domain: E-09 One value, one name: the full de-duplication campaign -- collapses the three parallel SSOT resolvers into one crate so the Law-13 twin-parity drift class ends by construction (TD-3). (1 tasks)
- **AGY-1047**: Add a pyo3 face on mios-toml-core and retire the mios_toml.py + userenv.sh resolver twins  (WS-LANGX | P2 | XL)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `python3 -c 'import mios_toml; ...'` returns structures identical to the retired pure-Python resolver across the proptest corpus; the shell, python and rust faces all derive from the one crate; `check_userenv_parity` is removed with a recorded justification; drift-gate green; Law 15 mirrored in both repos.
  - *Why:* Three hand-maintained resolvers held together by a parity gate is the duplication the operator flagged: every SSOT schema change must be made three times, and any miss surfaces only as a red gate rather than as a compile error.

### Domain: E-09 One value, one name: the full de-duplication campaign -- exactly one monitor executor exists and cannot be reintroduced. (1 tasks)
- **AGY-1698**: Actually delete the diverged monitor twin and gate against its return  (WS-DEDUP | P1 | M)  DONE
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `MiOS-Monitor.py` is absent from HEAD and disk; the new check fails when a twin file is restored; `replace.py`/`replace_indent.py` no longer exist; one dependency-bootstrap path serves both entry points; gate green.
  - *Why:* a stale second monitor that has drifted five fixes behind is worse than a byte-identical copy -- operators can run the old one and see wrong state, and nothing stops it coming back.

### Domain: E-09 One value, one name: the full de-duplication campaign -- finish the strangler-fig by actually removing the duplicated bodies, not just adding a native one. (1 tasks)
- **AGY-1009**: Delete the twin resolvers and replace the twin-equivalence check with a defer-to-native check  (WS-LANG-AUTO | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the duplicated resolver bodies are deleted or reduced to generated shims, the twin-equivalence check is replaced by a defer-to-native check, no phase references a removed file, both repos are updated, and the drift-gate is green.
  - *Why:* A native resolver that coexists with the twins costs more than it saves — four implementations plus a babysitting check — and the duplication the campaign set out to remove survives until the bodies are actually gone.

### Domain: E-09 One value, one name: the full de-duplication campaign -- stops the agent's advertised identity being authored a second time alongside the config it describes. (1 tasks)
- **AGY-1126**: Generate the AI manifest from SSOT via a pydantic model  (WS-DEBT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the served manifest is byte-identical pre/post, the module is mypy-strict clean, every manifest field traces to a mios.toml key, and `test_mios_ai_manifest.py` is green.
  - *Why:* A hand-written manifest drifts from the configuration it claims to describe, so federated peers are told capabilities the image may not ship.

### Domain: E-10 One canonical name -- closes the named canonical-walk/consumer mismatch so no capability carries a second name (Law 9). (1 tasks)
- **AGY-1417**: Unify the emitted `MIOS_AI_VLLM_*` vs consumed `MIOS_VLLM_*` mismatch through the derivation table  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: exactly one canonical vllm/sglang key family remains per concept; `check_var_closure` is green; no consumer references a dropped alias; the env-baseline diff is reviewed and intentional.
  - *Why:* An emitter and a consumer that disagree on a key name is a silent-empty bug class -- the inference lane reads an unset variable and falls back rather than failing.

### Domain: E-10 One canonical name -- guarantees key injectivity so no two SSOT facts can collapse onto one env name. (1 tasks)
- **AGY-1433**: Add a namespace bijection / collision invariant gate over the derivation table  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `check_namespace_bijection` is registered and green on the current tree; a planted colliding alias fails it; intentional shared aliases (e.g. `MIOS_HOSTNAME` from `identity.hostname` vs `user.hostname`) live in an explicit allowlist rather than being tolerated silently.
  - *Why:* A two-paths-to-one-name collision is a data-loss bug -- one operator setting overwrites another with no error -- and the value-duplicate check cannot see it.

### Domain: E-10 One canonical name -- makes `names.generated.txt` a complete registry so the one-canonical-name check has the full alias surface to police. (1 tasks)
- **AGY-1430**: Reconcile the two divergent alias-derivation implementations behind a get_aliases parity gate  (WS-GUP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `names.generated.txt` includes the identity/locale/portal/a2a/ai/ports/sidecar aliases it omits today; `check_alias_derivation_parity` is registered and green; the regenerated registry is staged by explicit path.
  - *Why:* Two hand-maintained alias derivations that disagree mean the registry -- and anything built on it, including the orphan census -- reports a namespace that does not exist.

### Domain: E-10 One canonical name: the unified names/keys registry -- closes the referenced-but-unemitted key-library drift class the epic names explicitly. (1 tasks)
- **AGY-1574**: Clear the `check_var_closure` "referenced but NOT emitted" backlog and flip the check from SOFT to hard-fail  (WS-PORTFLOAT | P2 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the closure report is empty and the check hard-fails; introducing a newly referenced-but-unemitted variable turns the gate RED.
  - *Why:* a soft warning printing 180 lines every run is not a gate -- real key-library regressions are already hiding inside that noise.

### Domain: E-10 One canonical name: the unified names/keys registry -- makes one resolver the generator-of-record so the other two stop being maintained by hand. (1 tasks)
- **AGY-1105**: Promote mios_toml.py to the canonical resolver that EMITS the shell/PS twins, retiring the hand-synced copies  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `userenv.sh` and `globals.ps1` are generated from `mios_toml.py`; check 27 is a regenerate-and-diff check; no hand-maintained resolver copy remains in the tree; both repos are updated; proptest parity and `just drift-gate` green.
  - *Why:* The proptest only proves the three resolvers currently agree — it does nothing to stop the next key from being added to one and forgotten in the other two, which is the triplicate-maintenance cost the operator flagged.

### Domain: E-10 One canonical name: the unified names/keys registry -- makes the compiled generator a faithful projector of the same registry the Python one emits. (1 tasks)
- **AGY-1409**: Rewrite the Rust generate-names-registry onto the shared lib and kill its incomplete `alias_for`  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust generator's output is byte-identical to `tools/generate-names-registry.py`'s output and to the committed `names.generated.txt`; the crate is a workspace member with a passing trycmd snapshot.
  - *Why:* Two generators for one registry currently produce different names, so whichever one runs decides what `names.generated.txt` says -- a live divergence sitting under the check that is supposed to guarantee one canonical name.

### Domain: E-10 One canonical name: the unified names/keys registry -- proves all THREE resolver twins emit the identical `MIOS_*` projection from one `mios.toml`. (1 tasks)
- **AGY-1551**: Add a three-way resolver equivalence CI job executing globals.ps1 under pwsh against the python and shell twins  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CI runs `globals.ps1` under pwsh and asserts its full `MIOS_*` set equals the python + shell twins; a seeded divergence in a NON-port key trips `check_globals_env_equivalence`; negative + drift-gate green.
  - *Why:* Every non-port, non-image key in the PowerShell resolver can drift undetected today, so a Windows host can resolve a different SSOT than the Linux host built from the same `mios.toml`.

### Domain: E-10 One canonical name: the unified names/keys registry -- single-sources the sets that decide which keys are emitted, so the Rust and Python resolvers cannot disagree about the namespace. (1 tasks)
- **AGY-1152**: Promote mios-ssot-walk from a 12-line stub to the typed SSOT of the section-partition constants  (WS-RESOLVER | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: lib.rs exports the three reconciled constant arrays plus predicates; `cargo test -p mios-ssot-walk` includes the mios_toml.py set-equality test; the `meta/laws` stub list no longer exists; the crate compiles under `-Dwarnings`.
  - *Why:* The crate designated as the compiled resolver library ships partition sets that contradict the real resolver, so every function ported on top of it would emit the wrong key set from day one.

### Domain: E-11 Unified config surface: mios.toml, the configurator and the Portal are one door at :8640/ -- closes the last hand-edit gap where the operator's single config door can persist an invalid value. (1 tasks)
- **AGY-1131**: Split routing/portal.py and schema-validate Portal config writes  (WS-DEBT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a malformed Portal config write is rejected with 422 + field span, both files are under 800 lines, `test_mios_portal.py` and surface-parity are green, and the ceiling allowlist entry is removed.
  - *Why:* Today the one operator-facing config door accepts an invalid value and writes it, which then propagates through every SSOT projection downstream.

### Domain: E-11 Unified config surface: mios.toml, the configurator and the Portal are one door at :8640/ -- the installer opens the SSOT-resolved door on both platforms. (1 tasks)
- **AGY-1700**: Fix the configurator port resolution and revert the unrequested `.ps1` special-target regression  (WS-CONFIG | P1 | S)  [BROKEN]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Linux `config` route prints a URL with a resolved port and no literal `8640` remains in that path; `monitor`, `update` and `repos` reach their own handlers on Windows; `Get-MiosSsotValue` resolves at runtime; no-browser hosts get the offline configurator HTML.
  - *Why:* today the installer's config route opens a portless URL on Linux and hijacks three working targets on Windows with a command-not-found call -- the single config door is unreachable from the installer on both platforms.

### Domain: E-12 ZERO-HARDCODES -- endpoints in units derive from SSOT instead of freezing stale literals into generated files. (1 tasks)
- **AGY-1349**: Reconcile hardcoded `Environment=` service URLs in migrated units against `[ports]`/`[services.webtools]`  (WS-SYSTEMD | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Every `Environment=` endpoint in the generated AI-plane units resolves from SSOT or carries a justified internal-port note; the searxng/firecrawl/crawl4ai disagreements are reconciled or documented; no unaccounted bare service URL remains; drift-gate green.
  - *Why:* A worker pointing at `:8888` when searxng canonically moved to `:8899` is live breakage today, and generating the units as-is would freeze those wrong values in as the SSOT-blessed answer.

### Domain: E-12 ZERO-HARDCODES -- removes a hand-maintained literal family from the resolver fallback path so there is a key to float TO. (1 tasks)
- **AGY-1419**: Generate the globals.{ps1,sh} identity and UID/GID fallback literals from mios.toml instead of authoring them twice  (WS-GUP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every uid/gid/user/subuid literal in globals.{ps1,sh} is generated from mios.toml with no hand-authored `else {N}`; `check_globals_ports` fails a seeded uid drift; the mios.toml change is mirrored into mios-bootstrap.git per Law 15.
  - *Why:* A service uid changed in mios.toml but not in the two globals fallbacks yields containers whose files are owned by the wrong account on any host where the resolver degrades to defaults.

### Domain: E-12 ZERO-HARDCODES -- systemd stops being the unscanned blind spot where floated ports regress to constants. (1 tasks)
- **AGY-1341**: Extend the bare-port-literal check to systemd units (ListenStream / ExecStart / Environment)  (WS-SYSTEMD | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The check FAILS on a synthetic unit containing a bare mapped port and PASSES on the floated tree; allowlist exemptions are honored; it is registered in the gate index; drift-gate green after the socket and AI-plane migrations.
  - *Why:* Without a unit-scoped gate, every port floated by the migration tasks can be quietly re-hardcoded by the next contributor, and the `[ports]` SSOT goes back to being advisory for the systemd surface.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- `usr/lib/mios` is the gate-red zone and must carry no port constants, including in the hottest path of the agent pipe. (1 tasks)
- **AGY-1469**: Lift the hardcoded llama.cpp lane ports across mios_pipe/** onto the shared SSOT resolver, module by module  (WS-ZEROHC | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no lane-port integer literal remains outside an env-default in these modules; the existing agent-pipe tests pass; check_no_bare_port_literals is green; endpoints resolve to the same values as before via env.
  - *Why:* server.py was floated but the kernel/routing modules that actually BUILD the request URLs were not, so moving a lane in mios.toml still leaves every real dispatch pointed at the old port.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- a `:-` fallback that disagrees with SSOT is a latent wrong-port bind, not a safe default. (1 tasks)
- **AGY-1476**: Correct the mios-ttyd-launch fallbacks to the SSOT ttyd ports and strip the stale :7681/:7682 comment literals  (WS-ZEROHC | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the launcher's `:-` fallbacks equal the SSOT ttyd_bash/ttyd_powershell values; no 7681/7682 literal remains in the ttyd units or launcher except an explicit SSOT-matching fallback; drift-gate green.
  - *Why:* Any host that starts ttyd without the env populated binds 7681/7682 instead of 8681/8682 today -- a silent wrong-port terminal -- and the stale comments will red the systemd lint the moment it scans them.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- a float without a gate is a temporary state; the guard is what makes it permanent. (1 tasks)
- **AGY-1473**: Add a tailnet-IP (100.64.0.0/10) regression fitness function so floated tailscale IPs cannot creep back  (WS-ZEROHC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a stray `100.x.y.z` literal that is not the SSOT value reds the gate; the SSOT `win_tailscale_ip` value itself does not; the check is green on the real tree.
  - *Why:* The CGNAT range is currently invisible to the lint, so the tailscale IP the campaign just floated can be re-pasted anywhere tomorrow and no gate will say a word.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- a floated var must render identically on every host, so the two hand-maintained renderer allowlists must be one set. (1 tasks)
- **AGY-1466**: Reconcile the two divergent render allowlists and gate their parity with check_render_allowlist_parity  (WS-ZEROHC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the two allowlists are verified equal-set; check_render_allowlist_parity is registered and green; adding a placeholder to only one list reds the gate; the K3S and OPENCODE naming is reconciled.
  - *Why:* The K3S name mismatch and bash-only OPENCODE entry are an already-present, already-shipped bug proving the duplication diverges silently; without the gate every new floated var can land in one list only and behave differently per host.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- a unit that both sources install.env AND re-pins the same value is a live drift source that must resolve to one place. (1 tasks)
- **AGY-1468**: Float the redundant MIOS_PORT_AGENT_PIPE and the llama.cpp lane-hint literals in mios-agent-pipe.service  (WS-ZEROHC | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: rendering the unit through 34-render-quadlets on a default host yields byte-identical port values (8640/11436/11450); no bare 8640/11436/11450 literal remains outside a `:-` fallback; drift-gate green.
  - *Why:* Today an operator can change the agent-pipe port in mios.toml and the unit keeps 8640 -- the AI front door named by `MIOS_AI_ENDPOINT` silently ignores the SSOT.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- a zero-hardcodes gate that hardcodes its own port table cannot be the enforcement plane for the rule. (1 tasks)
- **AGY-1470**: Derive check_no_bare_port_literals' banned lane-port list from the [ports] SSOT instead of hardcoding it  (WS-ZEROHC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: banned_ports is computed from the mios.toml `[ports]` lane-internal keys; moving a lane value in mios.toml moves the ban with it; the check is green; 11436 is now covered.
  - *Why:* The list is already stale -- igpu 11436 can be hardcoded anywhere in the tree today and the gate will not notice -- and every future lane move silently widens that hole.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- adds the SSOT keys the operator's representative six did not cover, so the gate-red cluster is fully literal-free. (1 tasks)
- **AGY-1447**: Float the hermes-worker/llm-heavy backend + browser-CDP ports and register their missing SSOT keys  (WS-ZEROHC | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `11441`/`9222`/`9223` exist as `[ports]` keys in both repos; the three consumers render to identical byte values; `mios-hardcode-lint` reports zero port literals on those lines; drift-gate green.
  - *Why:* The heavy-lane backend and the dual CDP browser ports are live consumer literals in the same gate-red files; leaving them means `check_no_hardcode` stays red after the rest of the cluster is floated.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- clears the densest single-file literal cluster in the gate-red zone and proves the internal-key scheme end to end. (1 tasks)
- **AGY-1446**: Float the hermes-worker.service retrieval-endpoint cluster (searxng / crawl4ai / firecrawl / worker-port literals)  (WS-ZEROHC | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the rendered `hermes-worker.service` resolves to the identical byte values (8888/11235/3002/8643) as today; `mios-hardcode-lint` reports no port literal in the file; the unit still parses under systemd; `check_no_hardcode` is green.
  - *Why:* This file is the exact false-friend trap -- its `:8888`/`:3002`/`:11235` are INTERNAL siblings, not the published `:8899`/`:8302`/`:8235` -- so leaving it hand-numbered is both the biggest remaining literal cluster and the most likely place a careless float breaks retrieval.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- clears the first genuine violation the anchored lint uncovers inside `usr/lib/mios`. (1 tasks)
- **AGY-1455**: Retire or float the dead SurrealDB DB_URL localhost:8000 that the allowlist anchor exposes  (WS-ZEROHC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: post-anchor `mios-hardcode-lint` reports no `localhost:8000` in `db.py`; either the dead constant is removed with no broken importers (agent-pipe tests pass) or it is floated to a real SSOT port; `server.py` is aligned.
  - *Why:* A retired SurrealDB relic still sitting in the agent-pipe import path is both a live gate violation and a trap for the next reader, who has no signal that `:8000` no longer exists.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- close the unanchored-allowlist class that spuriously exempts real `:80xx` violations. (1 tasks)
- **AGY-1463**: Anchor every remaining bare-port exempt_pattern and document the false-friend pairs inline in both repos  (WS-ZEROHC | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every bare-port exempt pattern is anchored in both repos; the false-friend comment block is present; `mios-hardcode-lint` still PASSes the intentionally-exempt canonical ports (:8640/:8642/:4317) while no longer exempting their numeric neighbours.
  - *Why:* The same unanchored-substring defect that let `localhost:80` mask real violations lives in every one of these entries, so the lint currently under-reports and the campaign cannot trust its own green.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- collapses one derived value copy-pasted into four units back to a single SSOT source. (1 tasks)
- **AGY-1450**: Float the pg_isready loopback+8432 cluster across the four Postgres-touching units  (WS-ZEROHC | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: all four units render to `127.0.0.1` / `8432` byte-identical; `mios-hardcode-lint` reports zero port/IP literals across them; `pg_isready` still passes on boot; drift-gate green.
  - *Why:* pgvector is the sole agent datastore and its address is authored four times; moving it once means editing four files and hoping, which is exactly the drift class the campaign exists to remove.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- creates the SSOT home the IP literals must float TO, so the campaign has a key rather than an exception. (1 tasks)
- **AGY-1443**: Add the [network] SSOT keys (loopback / bind_all / win_tailscale_ip) and derive MIOS_PG_BIND_ADDR from them  (WS-ZEROHC | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `MIOS_NETWORK_LOOPBACK`/`BIND_ALL`/`WIN_TAILSCALE_IP` resolve in a userenv dump; `MIOS_PG_BIND_ADDR` still emits `127.0.0.1` by default and `0.0.0.0` when `listen_loopback=false`, now sourced from SSOT; the twin-equivalence drift-check is green; both repos' `mios.toml` carry the keys.
  - *Why:* Loopback, bind-all and the tailnet IP are the most-repeated raw literals across the unit and quadlet trees; until they have one SSOT home, every IP-float task below has nowhere legitimate to point.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- encode the internal!=published false-friend rule as machine-checked policy instead of human vigilance. (1 tasks)
- **AGY-1462**: Add check_internal_ports_distinct as a fitness function asserting every [ports].*_internal differs from its published sibling  (WS-ZEROHC | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the check runs in the gate and PASSes on current SSOT; setting `searxng_internal=8899` (equal to published) reds it; the pairing map is read from TOML, not embedded in the check; the check carries an ADR-0012 number.
  - *Why:* Today nothing stops an editor from "tidying" firecrawl 3002 into 8302 and silently collapsing an internal bind onto its published port -- a runtime break discovered only in production rather than at build time.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- enforces the internal-vs-published disambiguation the new `[ports]` keys exist for. (1 tasks)
- **AGY-1449**: Float mios-cockpit-link.service's 127.0.0.1:9090 proxy target to loopback + cockpit_internal  (WS-ZEROHC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the rendered unit resolves to `127.0.0.1:9090` byte-identical; `mios-hardcode-lint` reports no literal; the cockpit-link proxy still forwards to host cockpit; drift-gate green.
  - *Why:* 9090 is the precise `cockpit_internal` false friend (internal 9090 vs published 8090); left as a literal, a future port renumber conflates the two and the proxy silently points at the wrong listener.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- every named false-friend needs an SSOT key to float TO, including forgejo 3000 != 8300. (1 tasks)
- **AGY-1471**: Add [ports].forge_internal=3000 and float the localhost:3000 git-origin literals in the Forgejo firstboot producers  (WS-ZEROHC | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the forge_internal key is present; the rendered producers resolve to `:3000`; no active `localhost:3000` literal remains outside a `:-` fallback; drift-gate and check_container_ports are green with 3000 recognized as an internal false-friend.
  - *Why:* The false-friend list explicitly names forgejo 3000 != 8300 to preserve, yet nothing in the campaign adds the key or floats the firstboot git-origin references that hardcode it -- so the one place a Forgejo port move would break is the one place still hand-written.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- exercises the new `bind_all` key on a published listener in an execution path. (1 tasks)
- **AGY-1451**: Float mios-agents.service's code-server bind 0.0.0.0:8800  (WS-ZEROHC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the rendered unit resolves to `0.0.0.0:8800` byte-identical; `mios-hardcode-lint` reports no literal; code-server still binds; drift-gate green.
  - *Why:* A bind-all plus published-port literal on a live `ExecStart` is exactly the gate-red class; it also leaves the operator unable to re-scope the code-server listener from the one config surface.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- finishes the loopback consolidation onto one shared `MIOS_NETWORK_LOOPBACK` key. (1 tasks)
- **AGY-1452**: Float the remaining loopback-host literals in hermes-dashboard.service and mios-opencode-gateway.service  (WS-ZEROHC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: both units render to `127.0.0.1` byte-identical; the unit-scanning `mios-hardcode-lint` reports no IP literal; dashboard and opencode-gateway still bind loopback; drift-gate green.
  - *Why:* These are the last two loose raw loopback IPs in the unit tree; leaving them means the loopback consolidation is incomplete and the lint stays red once the unit scan is enabled.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- guard the one failure mode the float campaign itself creates, so floating a port never becomes a mis-bind. (1 tasks)
- **AGY-1465**: Add check_no_residual_placeholders so a floated unit can never ship an unexpanded ${MIOS_*} to systemd  (WS-ZEROHC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: check_no_residual_placeholders is registered and green; leaving one un-allowlisted `${MIOS_PORT_FOO}` in a test unit turns the gate red; `just drift-gate` passes on the real tree.
  - *Why:* This is the highest-severity hazard the campaign introduces and nothing guards it today -- grepping 98-drift-checks.sh for residual/unrendered/placeholder returns zero hits -- so an unrendered placeholder ships as a hard runtime mis-bind, not a lint smell.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- kills the "ListenStream cannot take a variable" excuse that shields a whole class of socket units. (1 tasks)
- **AGY-1448**: Float the cockpit socket-render drop-ins (ListenStream 0.0.0.0:8090 and 0.0.0.0:8091)  (WS-ZEROHC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the post-render `listen.conf` and socket contain literal `0.0.0.0:8090` / `0.0.0.0:8091`, byte-identical to today; `mios-hardcode-lint`'s unit scan reports no literal on the placeholder lines; cockpit still binds on boot.
  - *Why:* These two sockets are the canonical cited reason floating "can't be done" for socket units; while the myth stands, every future socket ships hand-numbered and the gate carries a permanent exemption.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- makes the gate-red unit and quadlet trees visible to the lint so every float below is verifiable. (1 tasks)
- **AGY-1442**: Extend mios-hardcode-lint's _CODE_EXT to systemd units so usr/lib/systemd/system stops being an unscanned blind spot  (WS-ZEROHC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the lint scans `.service`/`.socket`/`.container`/`.timer`/`.conf`; a fixture unit with a bare `ListenStream=0.0.0.0:8090` is REPORTED while `${MIOS_NETWORK_BIND_ALL}:${MIOS_PORT_COCKPIT}` PASSes; `check_no_hardcode` exercises the unit tree.
  - *Why:* The operator named `usr/lib/systemd/system/**` as gate-red, but the lint literally cannot see it -- every unit float in this workstream would land unverified and could silently regress.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- makes the only routable-IP literal in the tree operator-defined rather than baked. (1 tasks)
- **AGY-1454**: Route Setup-MiOSLanPortProxy.ps1's doubled 100.79.3.50 tailscale fallback through [network].win_tailscale_ip  (WS-ZEROHC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the `.ps1` contains no bare `100.79.3.50` (it reads `$script:MIOS_NETWORK_WIN_TAILSCALE_IP`); the `tailscale ip` probe still wins when tailscale is present; `globals.ps1` exposes the key with `100.79.3.50` as its documented default; the script still runs on a host without tailscale.
  - *Why:* A specific tailnet address baked twice into a shipped Windows helper means any operator on a different tailnet silently gets the wrong proxy target with no config surface to correct it.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- one SSOT value must resolve identically on Linux and Windows, so the PowerShell resolver twin cannot lag the keys the campaign introduces. (1 tasks)
- **AGY-1460**: Mirror the six new internal-port and three [network] keys into the globals.ps1 resolver twin and fix its crawl4ai URL  (WS-ZEROHC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: globals.ps1 exposes every new port + network var with the correct default; the userenv.sh-vs-globals.ps1 twin-equivalence drift-check is green; `MIOS_CRAWL_SERVICE_URL` resolves against 11235.
  - *Why:* The three parallel resolvers must move in lockstep or the twin-equivalence gate reds the moment the vendor keys land -- and until then the PowerShell side hands out a crawl4ai URL that points at a port nothing is listening on.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- ports that survive only because the nohc allowlist exempts them are hardcodes with a permission slip. (1 tasks)
- **AGY-1472**: Add cdp_primary/cdp_worker SSOT keys and float the dedicated Chromium launcher units plus mios-hermes-browser  (WS-ZEROHC | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the cdp_primary/cdp_worker keys exist; the rendered units bind 9222/9223; the launcher fallback matches SSOT; no active 9222/9223 literal remains outside a `:-` fallback; drift-gate green.
  - *Why:* The existing browser-CDP task only covers hermes-worker.service's consumer env, leaving the two launcher units and the libexec launcher that actually OWN those ports uncovered -- a whole cluster that can drift from SSOT unnoticed.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- registers the genuinely-missing SSOT port keys so floating cannot collapse an internal port into its published sibling. (1 tasks)
- **AGY-1444**: Add the [ports] internal false-friend keys (cockpit/searxng/crawl4ai/firecrawl internal, igpu, win_llm_light)  (WS-ZEROHC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `tomllib` parses both `mios.toml` files; `MIOS_PORT_SEARXNG_INTERNAL=8888` and its five siblings resolve; `_ssot_lint_ports_dummy` lists all six; `automation/97-ssot-lint.sh` is green; the published sibling values are unchanged.
  - *Why:* Internal is not published. Without dedicated keys the cluster-float tasks would rewrite `3002` as `8302` (and `11235` as `8235`), silently breaking the hermes-worker retrieval path in a way only a live crawl would reveal.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- removes the last dense IP cluster in the quadlet tree and settles a live internal-vs-published contradiction. (1 tasks)
- **AGY-1453**: Float the mios-webtools quadlet IP/CDP/redis cluster and reconcile the crawl4ai 8235-vs-11235 mismatch  (WS-ZEROHC | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `redis_internal` and `browser_cdp` keys exist in both repos; all webtools quadlets render byte-identical (`127.0.0.1`/`9222`/`6380`/`11235`); `check_container_ports` and `mios-hardcode-lint` are green; the webtools pod still starts.
  - *Why:* The webtools pod is where the 8235-vs-11235 false friend actually bites today -- the healthz Label points one way and `MIOS_PORT_CRAWL4AI` another, so the pod's own health contract is internally inconsistent.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- repairs the lint bug that silently disarms the NO-HARDCODE gate, making the entire campaign enforced rather than advisory. (1 tasks)
- **AGY-1441**: Anchor the mios-hardcode-lint localhost:80 / :443 allowlist patterns so they stop masking the whole :80xx range  (WS-ZEROHC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `exempt_patterns` are anchored in both repos' `mios.toml`; running `mios-hardcode-lint` over a fixture line containing `http://localhost:8090` now REPORTS the `:8090` hardcode where it previously PASSed; the coupled float edits keep `check_no_hardcode` in `automation/98-drift-checks.sh` green.
  - *Why:* This one substring bug exempts every published `:80xx` port (cockpit, cockpit_link, open_webui, adguard_ui, guacamole) from the NO-HARDCODE gate -- the gate reports green today while the violations it exists to catch sit in the tree.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- restores the NO-HARDCODE (Law 7) gate's actual coverage by fixing the allowlist bug that lets `:8080`/`:8033` slip through. (1 tasks)
- **AGY-1040**: Port mios-hardcode-lint to Rust and anchor the allowlist regexes that spuriously exempt real port literals  (WS-LANGX | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust linter reports an identical violation set to the Python on the fixture repo for the date-in-comment / date-in-string / header-risk / port-IP classes, EXCEPT that previously-mis-exempted ports are now flagged; `MIOS_HARDCODE_LINT_SOFT=1` remains advisory; the drift-gate is green after the newly-surfaced violations are floated; Law 15 mirrored in mios-bootstrap.git.
  - *Why:* The unanchored allowlist silently exempts hardcoded canonical ports, so the NO-HARDCODE law reports green while real violations accumulate; the scanner is also hot Python on the drift-check path.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- shared SSOT surfaces move in both repos together (Law 15) or CI hard-fails the moment the vendor keys land. (1 tasks)
- **AGY-1467**: Mirror the new [network] + [ports.*_internal] keys into mios-bootstrap.git and reconcile check_bootstrap_ports_drift  (WS-ZEROHC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: both repos' mios.toml carry the same `[network]`/`[ports.*_internal]` keys; check_bootstrap_ports_drift is green; a tomllib parse plus a `wc -l` sanity check of the bootstrap file succeeds.
  - *Why:* This is a blocking dependency rather than cleanup -- the bootstrap-ports drift-check hard-fails CI the instant the vendor keys land, so the whole float campaign stalls behind it.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- stops tomorrow's hardcoded color from re-opening the hole today's migrations are closing. (1 tasks)
- **AGY-1395**: Add a hex-literal-leak gate: no `#RRGGBB` outside templates, fixtures and an explicit allowlist  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the gate red-flags a newly hardcoded `#hex` anywhere outside templates/fixtures/allowlist; the current tree passes once the hyprland and surfer folds land; `cargo test` and `just drift-gate` are green.
  - *Why:* Without a leak gate the projector-is-SSOT invariant decays exactly the way the zero-hardcodes campaign documents, and two live fallbacks already prove the hole is real, not theoretical.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- supplies the build-time substitution plumbing without which every unit-level float is inert text. (1 tasks)
- **AGY-1445**: Register the new port/network vars in the 34-render-quadlets envsubst + bash-fallback allowlists  (WS-ZEROHC | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a unit shipping `${MIOS_PORT_SEARXNG_INTERNAL:-8888}` renders to `8888` after the phase runs; the bash-fallback path (envsubst absent) produces identical output; the drift-gate render checks are green.
  - *Why:* Every unit float in this workstream is a no-op until its placeholder is allowlisted -- the rendered image would ship a literal `${MIOS_PORT_...}` string into a `ListenStream=` and the service would fail to start.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- the closure step: the allowlist itself becomes a projection of SSOT, not a hand-curated list. (1 tasks)
- **AGY-1475**: Generate the nohc_allowlist bare-port exempt_patterns from the [ports] loopback keys and diff-gate them  (WS-ZEROHC | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: exempt_patterns is generated from `[ports]` and diff-gated; moving a loopback port in `[ports]` regenerates the allowlist; committed-vs-generated compare green.
  - *Why:* Anchoring fixes the regex shape but leaves the list hand-curated, so it keeps accumulating orphans like `:8283` and duplicates like `:9222` and silently diverges from the real port table.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- the gate that polices hardcodes must itself learn the false-friend set from mios.toml rather than from two literals. (1 tasks)
- **AGY-1461**: Derive check_container_ports' internal-port skip set from SSOT so newly floated 3002/8888/11235/9090 stop being re-flagged  (WS-ZEROHC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: check_container_ports passes on the floated webtools/hermes-worker/cockpit quadlets; a bare `8888` with no placeholder still reds the gate; the 8080/3002 special case is gone, replaced by an SSOT-derived internal-port set.
  - *Why:* Without this, the very floats WS-ZEROHC introduces turn an already-green gate red -- the campaign would be blocked by its own progress, and derive-don't-duplicate would be violated inside the enforcement plane itself.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- the tree must default to SCANNED, with exemptions enumerated per file rather than per directory. (1 tasks)
- **AGY-1474**: Narrow the blanket exempt_files globs that hide usr/libexec, usr/share/mios and firstboot from the port/IP scan  (WS-ZEROHC | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the `.*/usr/libexec/.*` and `.*/usr/share/mios/.*` blanket globs are removed or replaced by an enumerated minimal file list; mios-hardcode-lint is green over the newly-scanned tree; both repos are mirrored.
  - *Why:* Zero-hardcodes reports green today largely because a regex hides 273 tools and the very firstboot producers this campaign names -- the blanket globs are the structural blind spot the whole effort exists to remove.

### Domain: E-12 ZERO-HARDCODES: float every remaining literal out of code -- turn a heredoc of booleans, fcontexts and port rules into a `[selinux]` SSOT table rendered by compiled code. (1 tasks)
- **AGY-1003**: Port 38-selinux + 37-k3s-selinux to `miosd render-selinux` and float the hardcoded policy lists into SSOT  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the semanage-import stream and the fcontext/port lists derive from SSOT and match golden byte-for-byte, a missing `semanage` degrades open, both phases are shims behind the toggle, and the drift-gate is green.
  - *Why:* A hardcoded policy heredoc is a live Law 7 NO-HARDCODE violation and an untargeted build phase at the same time: an operator cannot change an SELinux boolean or port label through the one config surface, only by editing a shell script.

### Domain: E-13 Ports are allocated from SSOT, not hand-assigned -- closes the last user-visible surface where a port literal is maintained by hand. (1 tasks)
- **AGY-1568**: Render `usr/share/applications/mios-svc-*.desktop` from SSOT ports instead of hand-editing them  (WS-PORTFLOAT | P1 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every `.desktop` port derives from `[ports]`; `--check` is clean on a synced tree; both a hand-edit to any launcher and a `[ports.categories]` base change are caught; the negative injects port-agnostically with no literal in the test.
  - *Why:* a wrong launcher port is what the operator clicks first, and four of them shipped broken with nothing able to detect it.

### Domain: E-13 Ports are allocated from SSOT, not hand-assigned -- proves the multi-stack offset that lets two MiOS hosts share one LAN. (1 tasks)
- **AGY-1578**: Add an end-to-end `stack_id` offset test across all three port surfaces  (WS-PORTFLOAT | P3 | S)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the offset is asserted on all three surfaces and a deliberate regression in any single one fails the test.
  - *Why:* multi-stack co-existence is a shipped feature that is currently unverified, and one of its three implementations was silently a no-op.

### Domain: E-13 Ports are allocated from SSOT, not hand-assigned -- the last place a port literal legitimately differs from SSOT becomes documented and gated rather than folklore. (1 tasks)
- **AGY-1579**: Reconcile in-container port fallbacks with the host allocation and record the rule in SSOT  (WS-PORTFLOAT | P3 | M) **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every `:-N` fallback in a Quadlet is either the SSOT value or a documented upstream default; the rule is stated in SSOT and enforced by a gate.
  - *Why:* a reader cannot currently tell an intentional upstream-default fallback from a stale literal, so both are copied forward and neither is checked.

### Domain: E-13/Law 8 Ports, laws, pipeline, verbs and units have exactly ONE generated answer, and a reader landing on a booted host has somewhere to start. (1 tasks)
- **AGY-1586**: Generate the five derived reference docs and the missing `/usr/share/doc/mios/` entry point  (WS-DOCGEN | P1 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: all six files are generated, gate 152 covers them, and every port/law/stage number in them equals the SSOT value.
  - *Why:* a reader cannot get a straight answer to "what port is X on", "how many laws are there" or "what does build step N do"; every doc that answers directly is wrong, and one agent-facing contract file states a law that does not exist.

### Domain: E-14 Float latest globally -- one declared value, every downstream version derived, so a single SSOT bump propagates without a second hand edit. (1 tasks)
- **AGY-1563**: Establish ONE version SSOT and convert every consumer to a derivation (the k3s→k8s cascade, generalized)  (WS-FLOAT | P1 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a test that bumps the k3s tag in a temp copy of the SSOT and diffs derived outputs shows the k8s repo minor, the Quadlets and the manifests all moved with ZERO other edits; the 3-way py/sh/ps1 resolver-equivalence checks stay green.
  - *Why:* today `MIOS_K3S_VERSION` exists but most versions have no single home, so each bump is a manual multi-file sweep that silently half-lands and ships a mismatched repo.

### Domain: E-15 SBOM and supply-chain hardening -- converts reproducibility from a property that should hold into an enforced, continuously verified invariant. (1 tasks)
- **AGY-966**: Add a rebuild-and-compare-digest gate that fails when two builds of one commit diverge  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The gate rebuilds and compares; an intentionally injected wall-clock file makes it fail and names the offending path; a clean tree passes; the job is documented as scheduled to bound runner cost.
  - *Why:* Reproducibility silently rots — one new phase embedding a timestamp or hostname undoes AGY-965 with nothing to notice.

### Domain: E-15 SBOM and supply-chain hardening -- enforces ADR-0003, that a resolved version is build-recorded SBOM data and never a hand-authored SSOT literal. (1 tasks)
- **AGY-1434**: Census and collapse the ~79 version-dupe pairs rooted in `image.sidecars.*` to one SBOM-derived source  (WS-GUP | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the version-family census is committed; duplicated per-sidecar version literals derive from one SBOM-recorded source; `check_version_family_collapse` is green; the full drift-gate is green.
  - *Why:* Nothing today collapses the per-component version family -- `mios-version-check` only validates the single top-level `mios_version` -- so a sidecar bump must be hand-edited in several places and any missed copy pins an image to a stale version.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- "resolved and recorded at build" becomes an enforced fitness function instead of a convention. (1 tasks)
- **AGY-1500**: Gate ADR-0003: every floating binary download must record a binaries.tsv row  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the gate enumerates every download site and fails on an unrecorded binary fetch; the exempt list is SSOT-defined; adding a new un-recorded `curl|sh` fails the build; drift-gate and negatives green; both repos carry it.
  - *Why:* Most fetched binaries in the image are absent from the SBOM manifest, so the published provenance record understates what actually shipped and ADR-0003 reproducibility does not hold.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- Python dependencies become build-resolved SBOM data with an advisory gate, matching the cargo side. (1 tasks)
- **AGY-1072**: Pin and audit the Python third-party dependency surface with a constraints lock + pip-audit gate  (WS-DEBT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every third-party import appears in the dependency manifest; a pinned `constraints.lock` is generated at build; `pip-audit` runs in CI and fails on a known-vuln advisory; the lock's contents appear in the generated SBOM; `just drift-gate` green.
  - *Why:* `cryptography`, `fastapi` and `huggingface_hub` are attack-surface-heavy, currently float unversioned and unaudited, and are invisible to the SBOM -- so a published image cannot answer which Python versions it actually shipped.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- Secure Boot trust custody becomes an operator SSOT input projected into the build, not a MiOS constant. (1 tasks)
- **AGY-1496**: Make MOK key generation and enrollment operator-defined via `[security.secureboot]`  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: both scripts read CN, key bits, validity and cert path from `[security.secureboot]` with literal fallbacks; changing the CN in SSOT visibly changes the generated cert; no private key material enters `mios.toml`; drift-gate green; both repos carry it.
  - *Why:* An operator deploying MiOS cannot today name their own signing identity or key policy without editing shipped automation, which is precisely the hand-edited-config class the SSOT north star forbids.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- allowlisting moves from path identity to content identity, making the image an immutable execution environment. (1 tasks)
- **AGY-1493**: Set fapolicyd `integrity=sha256` and derive the trust DB from built image content  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `fapolicyd.conf` ships `integrity = sha256` on both the `/usr/lib` and `/etc` paths; the trust DB derives from image content; a binary overlaid at a trusted path is denied execution; a drift-check asserts the setting; both repos carry it.
  - *Why:* Path-only allowlisting means fapolicyd currently approves whatever occupies a trusted path, so an overlay or `/var` tamper defeats the entire immutable-execution premise the image is built on.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- byte-identical digests across publishers are the precondition for the equal-publisher release topology. (1 tasks)
- **AGY-1483**: Make the image build reproducible via a git-derived SOURCE_DATE_EPOCH and timestamp rewrite  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: two independent CI builds of the same commit produce byte-identical image digests; SOURCE_DATE_EPOCH is derived from git commit time; base images are digest-pinned; both forges patched; Law 15 mirrored.
  - *Why:* Today the two forges provably cannot publish the same digest for the same commit, so the 'bit-for-bit equal publishers' invariant is unenforceable and nobody can independently reproduce a shipped image.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- close the four unpinned upstream fetches that make the image non-reproducible and the digest-compare gate unusable. (1 tasks)
- **AGY-1005**: Pin and checksum the network-fetch bakes (66-quickshell, 68-kvmfr, 69-lookingglass, 73-model-prep) through `miosd fetch-verify`  (WS-LANG-AUTO | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each bake fetches a pinned ref and verifies a recorded checksum, a tampered or moved source fails the build, two independent builds fetch identical bytes, the SBOM records the resolved refs, and the drift-gate is green.
  - *Why:* Four phases clone or curl a moving upstream with no verification, so today's image cannot be rebuilt to the same bytes and a compromised upstream would be baked in silently — the rebuild-and-compare-digest gate can never pass until this is fixed.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- close the largest unpinned dependency surface in the bake and honor Law 12 BAKE-NOT-FETCH. (1 tasks)
- **AGY-1006**: Make the 72-hermes-agent shared Python venv reproducible with hash-locked, fully-offline wheels  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the venv installs only from vendored wheels with `--require-hashes` and no network access, two builds produce an identical package set recorded in the SBOM, the venv contents are digest-stable, and the drift-gate is green.
  - *Why:* An unpinned pip resolve means the AI plane's dependency set differs between any two builds and a compromised PyPI package lands with no signal — it is simultaneously the biggest reproducibility hole and the biggest supply-chain hole in the bake.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- convert signing effort into actual boot integrity for the immutable host. (1 tasks)
- **AGY-1480**: Generate a real sigstoreSigned policy.json from [security.sigstore] instead of insecureAcceptEverything  (WS-SBOM | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: with `policy_mode=sigstoreSigned` the generated policy.json carries a sigstoreSigned rule keyed to the MiOS repo and mios-cosign.pub; `generate-cosign-policy.py --check` passes; `skopeo copy` admits a signed image and rejects an unsigned one under the policy; drift-gate green; mirrored in both repos.
  - *Why:* An immutable OS that trusts every image has no boot integrity at all -- the strongest property of the bootc model is currently switched off by a one-line default.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- dependency assurance rises from advisory-only to human trusted-review. (1 tasks)
- **AGY-1504**: Initialize cargo-vet trusted-review for both Rust workspaces  (WS-SBOM | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo vet` is initialized for both workspaces with imported audit sets, runs in CI, and flags a newly-added unaudited crate; exemptions are committed and reviewable; both repos carry it.
  - *Why:* Advisory and license gates only catch what someone already reported -- an unreviewed new crate entering the OS build plane passes both today.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- digest capture becomes build-resolved provenance instead of an in-code ref list plus a fallback literal. (1 tasks)
- **AGY-1022**: Port mios-resolve-latest to a Rust OCI-digest + SBOM recorder that reads refs from SSOT  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust tool resolves the same ref set from SSOT with no ref array in code, and writes a byte-identical `MiOS-SBOM.csv` line versus the bash for a stubbed digest; the skopeo-absent path degrades open; the golden test is green.
  - *Why:* The bash hardcodes both the sidecar ref list and a fallback sha256 literal, so adding a sidecar to SSOT silently fails to appear in the SBOM and a stale pinned digest can be recorded as provenance.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- every published image is guaranteed to carry the provenance record that reproducibility is defined by. (1 tasks)
- **AGY-1514**: Make a non-empty SBOM a fail-closed publish gate while bake stays degrade-open  (WS-SBOM | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A PUBLISH build with a missing or empty SBOM/TSV fails the gate; the bake step still degrades open; local and non-publish builds are unaffected.
  - *Why:* Degrade-open silently ships images with no SBOM at all, which means the attach-SBOM-attestation and scan-the-attested-SBOM tasks downstream have nothing to attest or scan; a presence gate at publish is the missing floor under the entire SBOM control stack.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- gives the compiled projector the dependency-provenance and error-UX story bash never had. (1 tasks)
- **AGY-1389**: Gate the projector crate with cargo-deny/cargo-audit and give it spanned miette diagnostics  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo deny check` and `cargo audit` run as drift-gate steps and pass; a deliberately malformed hex in mios.toml produces a spanned miette diagnostic naming the line; Cargo.lock is committed; `just drift-gate` green.
  - *Why:* The projector is becoming a compiled dependency-carrying binary in the boot path with zero advisory scanning and zero license policy, and its failure mode today is an opaque error string that tells an operator nothing about which mios.toml line broke.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- install-time wheel integrity for the highest-trust runtime in the image. (1 tasks)
- **AGY-1513**: Hash-pin the agent-plane and finetune pip installs with --require-hashes  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Both pip installs run with `--require-hashes` against committed hash-locked files; a tampered wheel is rejected at install time; the new drift-gate check fails if any requirement lacks a hash.
  - *Why:* The agent plane is the most privileged runtime in MiOS -- it drives OS-control verbs -- yet it currently pulls Python dependencies with zero integrity pinning, and pip-audit only reports known CVEs while doing nothing whatsoever against a substituted wheel.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- keeps application whitelisting intact while the libexec fleet turns into non-rpm binaries. (1 tasks)
- **AGY-1052**: Enroll native /usr/libexec/mios binaries into fapolicyd file-trust so ComposeFS execution is not denied  (WS-LANGX | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the fapolicyd trust db lists every native `/usr/libexec/mios` binary; a boot smoke-test executes each one with no fapolicyd denial; the drift-check fails when a binary is missing from the trust drop-in; gate green.
  - *Why:* A ported binary that fapolicyd blocks is strictly worse than the bash it replaced -- it fails closed at exec on exactly the hardened installs MiOS targets, and nothing today would catch it before boot.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- make the `:latest`-intent -> observed-version record a typed build artifact feeding the SBOM rather than scattered shell appends. (1 tasks)
- **AGY-987**: Emit the build version-manifest from a structured `mios-build` API instead of TSV-append shell  (WS-LANG-AUTO | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd record-version` and `miosd capture-quadlet-digests` produce the same manifest rows and columns as today's shell, common.sh's `record_version` is a wrapper over the binary, the build's version manifest is generated by the compiled path, and the drift-gate is green.
  - *Why:* Version provenance is the backbone of SBOM-not-hardcode, yet it is assembled by ad-hoc TSV appends from dozens of phases with no schema — a malformed or dropped row corrupts the provenance record with no error and no way for the SBOM to detect it.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- makes "reproducible = baked manifest + SBOM" true, with every legitimate pin justified rather than assumed. (1 tasks)
- **AGY-1565**: Give image refs `:latest` INTENT with digests resolved at BUILD, and record the offline-vendored pin exception in an ADR  (WS-FLOAT | P2 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every sidecar's float-or-pin decision is recorded in the ADR; the baked SBOM manifest holds the resolved digests; no `@sha256` is hand-typed anywhere in the SSOT.
  - *Why:* hand-pinned digests in SSOT go stale invisibly and are the root of the recurring Quadlet-digest-drift class, while blind floating would break byte-reproducible offline install.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- no credential ever reaches a published layer, so "signed" also means "clean". (1 tasks)
- **AGY-1510**: Gate both CI publishers on a gitleaks scan of the git tree AND the exported OCI rootfs  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The gitleaks gate runs in both CI publishers and in the drift-gate; a deliberately planted test secret turns all three red; the three shipped public keys are allowlisted and do not trip it.
  - *Why:* A token baked into a layer or committed into the SSOT is an immediate supply-chain compromise that signing cannot detect -- a correctly signed image with an embedded secret is still poisoned -- and Law-15 dual-repo work multiplies the chance of an accidental credential commit while the control is entirely absent.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- nothing unverified executes inside the build that produces the signed image. (1 tasks)
- **AGY-1507**: Delete `curl|sh` from the bake and float the Sigstore toolchain from SSOT  (WS-SBOM | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no pipe-to-shell installer remains anywhere in the bake path; syft and cosign versions/digests resolve from `[security.toolchain]`; `check_no_curl_pipe_sh` is green and each tool is recorded to `binaries.tsv`.
  - *Why:* `curl|sh` runs attacker-controllable code with no integrity check inside the build that produces the signed image, undermining the signing chain at its root, and the hardcoded fallback versions violate ADR-0003 besides.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- one authoritative Secure Boot codepath instead of three hand-maintained divergent ones. (1 tasks)
- **AGY-1511**: Fold the three duplicate MOK/secure-boot scripts into one compiled mios-mok verb  (WS-SBOM | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A single `mios-mok` binary exposes gen/enroll/status subcommands; the three scripts are gone (or reduced to <=3-line shims); the drift-gate is green and the binary's output is byte-identical to the captured golden.
  - *Why:* Three divergent MOK codepaths are a correctness hazard with a hard failure mode -- an enroll that disagrees with the key it was generated against bricks Secure Boot on the target machine -- and the retirement/cleanup half is what the two MOK porting tasks set up but never finish.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- promote the SBOM from an in-tree file to verifiable OCI provenance attached to the published digest. (1 tasks)
- **AGY-989**: Port 90-generate-sbom.sh to `miosd sbom` and publish the SBOM as a signed cosign attestation  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd sbom` reproduces the same CycloneDX + SPDX artifacts and still exits 0 with syft or egress missing, CI attaches the SBOM as a cosign attestation on the image digest, and `cosign verify-attestation --type spdx` succeeds against a published image.
  - *Why:* An SBOM that only exists inside the image proves nothing to a consumer verifying the pulled ref; without an attestation the ADR-0003 provenance loop stays open and no puller can check what they actually received.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- provenance means SBOM + baked manifest, which requires the SBOM to travel WITH the image. (1 tasks)
- **AGY-1481**: Attach the Syft SBOM to the published digest as a signed cosign attestation on both forges  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cosign verify-attestation --type spdx <published digest>` returns the SBOM predicate on both forges; the CI step is green; ADR-0003 references the attestation; Law 15 mirrored.
  - *Why:* An SBOM nobody outside the build can pull is not provenance -- a consumer of the published image has no verifiable inventory of what they just booted.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- put the image-integrity seal under compiled code plus a gate that detects posture regression. (1 tasks)
- **AGY-1004**: Port 77-composefs-verity to `miosd seal-composefs` with a `--check` integrity verify mode  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd seal-composefs` reproduces the sealing steps with parity against golden, `--check` fails when the verity posture regresses, the phase is a shim behind the toggle, and `cargo test` plus the drift-gate are green.
  - *Why:* Composefs/fs-verity is what makes `/usr` tamper-evident, yet nothing verifies the seal actually got applied — a silently-unsealed image would ship and boot looking completely normal.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- reproducibility becomes a measured CI fact rather than an asserted property. (1 tasks)
- **AGY-1515**: Add a CI determinism job that bakes twice and diffs the resulting image manifests  (WS-SBOM | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Two back-to-back bakes produce identical manifest digests (or a diffoscope report showing only allowlisted deltas), and the job has been promoted from report-only to required.
  - *Why:* An unverified SOURCE_DATE_EPOCH claim is exactly the aspirational security assertion this campaign exists to convert into something gated; without the verification half, the SLSA/provenance story rests on an untested assumption.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- restore the equal-publisher invariant by making Forgejo-published digests as verifiable as GitHub's. (1 tasks)
- **AGY-1477**: Add cosign signing to the Forgejo publisher so both forges sign every pushed tag  (WS-SBOM | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: build-mios.yml pushes then signs each published tag; `cosign verify` succeeds against a Forgejo-published digest; grep for cosign in build-mios.yml is non-empty; drift-gate green; the change is present in both repos.
  - *Why:* Half the fleet's images are unverifiable today, so the release-topology promise that GitHub and Forgejo are equal bit-for-bit publishers is false wherever it matters most -- at signature verification.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- runtime integrity is continuously attested, not just verified once at publish and once at firstboot. (1 tasks)
- **AGY-1512**: Add a greenboot required.d self-attestation check that auto-rolls-back a tampered running image  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A tampered or unsigned running image fails the greenboot required check and triggers a rollback to the previous deployment; a correctly signed image passes; the check reads its identity constraints from SSOT with no literals.
  - *Why:* Signing at publish plus verifying at firstboot leaves every subsequent boot completely unattested, so a machine tampered with after install stays green indefinitely; the greenboot-health and firstboot-policy tasks each cover one end and neither closes the loop.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- signatures must land in a format the image-policy enforcement layer can actually read. (1 tasks)
- **AGY-1479**: Pin CI cosign to v2.x legacy-attachment format so bootc/rpm-ostree policy can discover the signatures  (WS-SBOM | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CI signs with cosign v2.x; the pushed digest carries a `.sig` sigstore attachment rather than a v3 referrers bundle, verifiable by rpm-ostree/containers-image policy; both workflows are pinned; drift-gate green; Law 15 mirrored.
  - *Why:* Until this lands every downstream verification silently fails on format grounds, so the strict-policy work built on top of it would appear to work while enforcing nothing.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the Python half of the image gets the same dependency-vuln screening as the Rust half. (1 tasks)
- **AGY-1488**: Add a pip-audit gate over the agent-plane venv and the python libexec fleet  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: pip-audit runs in CI over the agent venv/requirements and fails on a known-vulnerable pin; the offline bake warns and continues; the report lands in `artifacts/sbom`; both repos carry it.
  - *Why:* The 122-tool python plane plus the FastAPI agent front door is the largest unaudited dependency surface in the image, and a vulnerable transitive pin reaches the operator's machine today with nothing between it and them.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the attestation is continuously consumed, closing the loop on `:latest`-intent reproducibility. (1 tasks)
- **AGY-1503**: Add a scheduled vuln scan that verify-pulls the attested SBOM and scans the digest  (WS-SBOM | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the scheduled workflow verify-pulls the SBOM attestation and scans it with grype/trivy; a seeded CVE fails or reports; it runs against the digest rather than a tag; the Forgejo sibling or shared workflow exists.
  - *Why:* A published image ages into vulnerability silently -- nothing rechecks the shipped bits between bakes, so the SBOM is written and never read.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the base package layer is signature-verified, so the signing chain has a verified root. (1 tasks)
- **AGY-1505**: Enforce RPM package + repo GPG verification from an SSOT `[security.rpm]` policy  (WS-SBOM | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no generated `.repo` sets `gpgcheck=0` outside the SSOT allowlist; `check_rpm_gpgcheck` is green in `just drift-gate`; the vendored-mirror bake installs RPM-signature-verified packages.
  - *Why:* `gpgcheck=0` means the RPM layer accepts unsigned packages -- the largest untargeted supply-chain surface in the image, and every cosign/SBOM control downstream is moot while the base package layer is unverified.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the boot chain has no unsigned-module gap left between UKI and userspace. (1 tasks)
- **AGY-1508**: Fail-closed signing of out-of-tree kernel modules under Secure Boot  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: in enforce mode the bake fails on any unsigned out-of-tree module; the drift-gate lists and verifies every baked `.ko` signature; kvmfr is signed in the standard bake with byte-parity against the old shell signer.
  - *Why:* Secure Boot plus UKI signing is worthless if out-of-tree modules load unsigned -- and in the failure case that exists today the module instead vanishes silently, breaking Looking Glass with no build error.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the compiled tier needs the dependency-surface gate that bash never had. (1 tasks)
- **AGY-1484**: Add a cargo-deny gate (licenses, advisories, bans) covering every native crate in both workspaces  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo deny check` passes for both workspaces covering every member crate; a deliberately GPL or duplicated dependency fails it; CI and `just drift-gate` both run it; config mirrored in both repos.
  - *Why:* Five native crates are outside the workspace members list and therefore outside every gate, and no license or advisory check exists at all -- a banned-license or vulnerable transitive dep can ship into the image today with nothing to stop it.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the compiled tier's dependency set is continuously checked against RustSec, not merely locked. (1 tasks)
- **AGY-1485**: Gate both Rust workspaces on `cargo audit --deny warnings` over committed lockfiles  (WS-SBOM | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo audit` runs green in CI and in `just drift-gate` over both lockfiles; injecting a known-vulnerable dependency version turns the gate red; a failed advisory-DB fetch warns and continues instead of failing the build; both repos carry the change.
  - *Why:* Build scripts and proc-macros execute arbitrary code during `cargo build`, so today every crate pulled into the OS build plane is unscreened against published advisories and a known-CVE dependency can ship inside `miosd` with nothing to notice.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the digests recorded at bake are actually enforced where the artifacts land. (1 tasks)
- **AGY-1509**: Verify bound-image digests at firstboot before the 47GB whale pull  (WS-SBOM | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: firstboot pulls the whales by their bake-recorded digest and verifies signatures when the SSOT flag is on; a digest mismatch aborts the pull; the tag-pull degrade-open path still works when the flag is off.
  - *Why:* The firstboot tier is a live TOCTOU hole -- digests are captured at bake but the two biggest artifacts are re-pulled unverified on the operator's machine, exactly where a registry MITM does the most damage, and the producer never consults the policy that was installed for it.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the largest ingested artifact in the OS is signature-verified and digest-recorded like everything else. (1 tasks)
- **AGY-1506**: Verify and digest-pin the base image at build, recording it to provenance  (WS-SBOM | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the bake resolves and records the ucore-hci digest and builds FROM that digest; a build-host policy rejects an unsigned or foreign base image; `bound-images.tsv` carries the base-image row.
  - *Why:* An unpinned, unverified `FROM` tag is a silent whole-OS substitution vector: two bakes can produce different systems from the same commit, and the single largest ingested artifact is currently the least verified thing in the tree.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the shipped artifact itself carries what it was built from, so it can be re-scanned later. (1 tasks)
- **AGY-1501**: Build miosd and the native tools with cargo-auditable to embed the dependency manifest  (WS-SBOM | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: miosd and the native tools are built with cargo-auditable; `cargo audit bin` reads the embedded manifest out of the shipped binary; Containerfile and CI updated; the provenance row is recorded; both repos carry it.
  - *Why:* A CVE published after the bake cannot be checked against an already-deployed host today -- the binary on disk is opaque about its own dependencies.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the signature policy extends past the host boundary to everything pulled at runtime. (1 tasks)
- **AGY-1498**: Enforce cosign signature + attestation at k3s admission for runtime sidecars  (WS-SBOM | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a rendered admission policy enforces cosign identity + attestation on k3s image pulls; an unsigned test image is rejected and a MiOS-signed one admitted; the policy is SSOT-templated and toggled off by default; drift-gate green; both repos carry it.
  - *Why:* Host-plane signing stops at the boundary, so k3s can pull an unsigned inference sidecar onto a fully-verified host today -- reopening precisely the substitution gap signing exists to close.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the signed UKI's security properties become a fitness function, not an assumption. (1 tasks)
- **AGY-1495**: Assert the required security kargs so `enforcing=1` cannot drop out of the signed UKI cmdline  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the gate fails when a required security karg is absent from the rendered cmdline; the required set is SSOT-defined; `enforcing=1` presence is explicitly asserted; drift-gate and negatives green; both repos carry it.
  - *Why:* Projection parity only proves the cmdline matches its generator -- an edit that drops `enforcing=1` or `lockdown=` today ships a signed UKI with SELinux permissive and every gate stays green.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- the sigstoreSigned policy.json actually gates `bootc upgrade` instead of sitting inert. (1 tasks)
- **AGY-1499**: Bootstrap on-disk signature-policy enforcement at firstboot, gated on the SSOT flag  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a firstboot producer bootstraps enforce-container-sigpolicy gated on `policy_mode=sigstoreSigned`; an unsigned `bootc upgrade` is refused on an enforcing host; the producer no-ops cleanly when disabled; drift-gate green; both repos carry it.
  - *Why:* A strict `policy.json` on disk enforces nothing until enforcement is switched on once, so today a host with the strictest possible policy still accepts an unsigned upgrade.

### Domain: E-15 SBOM and supply-chain hardening as compiled, gated policy -- two independent publishers of the 'same' digest are only trustworthy if each build is independently attributable. (1 tasks)
- **AGY-1482**: Emit signed SLSA build provenance for the published image, recording which forge built the digest  (WS-SBOM | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a signed SLSA provenance attestation is attached to the published digest on both forges; slsa-verifier or `cosign verify-attestation --type slsaprovenance` resolves it; the predicate names the building forge; Law 15 mirrored.
  - *Why:* Without provenance there is no non-falsifiable record of HOW a digest was built, so an operator cannot tell a legitimate Forgejo build from an injected one.

### Domain: E-16 The bake plane / release topology -- makes the declared GitHub == Forgejo equality mechanically true for the gate set, not just the build. (1 tasks)
- **AGY-1546**: Mirror every test/lint gate into .forgejo and add check_ci_workflow_parity  (WS-TESTGOV | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `check_ci_workflow_parity` fails a step-removed mutated Forgejo copy and passes the parity'd pair; both workflows enumerate an identical gate-step set; `just drift-gate` + negatives green.
  - *Why:* The two publishers are declared bit-for-bit equal but already differ, so every gate added to GitHub becomes a false-green hole on the Forgejo side.

### Domain: E-16 The bake plane: what is present in the image -- the baked image must actually contain a working agent plane, not a venv that merely appears installed. (1 tasks)
- **AGY-1569**: Vendor `aiohttp` and the full hermes-agent dependency closure into the offline wheels dir, and fail the phase when it is incomplete  (WS-PORTFLOAT | P1 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the phase builds the venv with no network and emits no WARN; deliberately deleting one wheel fails the phase; the bake log reports 0 warned for this step.
  - *Why:* the agent plane is the product, and a WARN-not-FAIL path means every published image today carries a hermes venv that cannot make an HTTP request.

### Domain: E-16 The bake plane: what is present in the image, and can a stock runner hold it -- consolidate group baking into the crate that already owns the plan.d projection. (1 tasks)
- **AGY-1023**: Fold mios-bake-group into the mios-bake-plan crate as a native bake-group subcommand  (WS-LANGX | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-bake-plan bake-group heavy` selects the same images and appends a byte-identical `bound-images.tsv` line as the bash for a mocked pull; `MIOS_BAKE_BOUND_IMAGES=0` skips identically; the workspace builds; golden test green.
  - *Why:* The bake path is the disk-fragile CI machinery that fails with podman exit 125 on layer commit; splitting its logic across a bash tool and a Rust sibling that already parses plan.d means every fix has to be made twice.

### Domain: E-18 Generate the 168 systemd units from SSOT -- broadens generator type coverage across the passive unit families at near-zero risk. (1 tasks)
- **AGY-1330**: Migrate the 5 .path units to generated [units.*.path]  (WS-SYSTEMD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: All 5 `.path` units render byte-identical to golden; `mios-unit-gen --check` reports the path family in sync; drift-gate and `cargo test` green.
  - *Why:* These watchers trigger the bootc switch and permission repairs; while they stay hand-authored their watched paths are invisible to SSOT and a stale path silently disables the trigger with no gate to notice.

### Domain: E-18 Generate the 168 systemd units from SSOT -- converts unit hardening from an episodic audit into a continuously enforced, mios.toml-thresholded gate (NS-6, governance as policy-as-code). (1 tasks)
- **AGY-1325**: Add a systemd-analyze security ratchet as a fitness-function drift-check  (WS-SYSTEMD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `check_unit_security` FAILS on a synthetic unconfined unit and PASSES on the hardened tree; the score threshold and exempt roster are read from mios.toml; the gate index is regenerated and staged; the drift-gate is green on Linux CI.
  - *Why:* Nothing currently stops a new unit from shipping with zero confinement, so the ~40 unconfined services keep multiplying and the hardening the migration delivers is unmeasurable and unprotected.

### Domain: E-18 Generate the 168 systemd units from SSOT -- demonstrates the base+overrides DRY payoff on real services, collapsing ~7 near-duplicate files to one declaration. (1 tasks)
- **AGY-1332**: Migrate the GPU-detect service family to one templated generator base  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: All 7 GPU units and the nvidia drop-in render byte-identical to golden from shared SSOT; adding a hardening key to the base propagates to all seven; drift-gate and `cargo test` green.
  - *Why:* Seven hand-copied detectors drift apart on every edit -- a hardening or ordering fix applied to one vendor's unit and forgotten in the others is the exact failure mode, and multi-vendor GPU support depends on them behaving identically.

### Domain: E-18 Generate the 168 systemd units from SSOT -- elevation in generated units is explicit, justified and auditable rather than incidental. (1 tasks)
- **AGY-1339**: Gate privileged/root service generation behind a justified `[security.privileged_units]` roster  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Privileged units render from SSOT and appear on `[security.privileged_units]` with justifications; adding a root service that is not on the roster makes the generator exit non-zero; the roster check is registered in the gate index; drift-gate green.
  - *Why:* Root units are the highest-blast-radius surface in the image, and a generator with no privilege policy makes privilege creep a one-line accident that no reviewer or gate would notice.

### Domain: E-18 Generate the 168 systemd units from SSOT -- encodes the Law-12 (BAKE-NOT-FETCH) firstboot contract once so a single hand-edit cannot brick boot across a fleet. (1 tasks)
- **AGY-1333**: Migrate the *-firstboot.service family with degrade-open and timer pairing enforced  (WS-SYSTEMD | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: All firstboot units render byte-identical to golden; generated units retain their `ConditionPathExists` sentinels and optional `EnvironmentFile`; `check_firstboot_degrade_open` and `check_dag_integrity` pass; drift-gate and `cargo test` green.
  - *Why:* These 11 units run on every first boot of every deployed host; one that fails closed on a fetch error takes the machine down, and the sentinel/timer/degrade-open shape is currently re-typed by hand in each file with only a backend-script gate watching.

### Domain: E-18 Generate the 168 systemd units from SSOT -- establishes the deviance oracle without which no strangler-fig unit migration can prove parity. (1 tasks)
- **AGY-1321**: Capture byte-exact golden-master snapshots of all 161 hand-maintained units before migration  (WS-SYSTEMD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test -p mios-unit-gen` reproduces the 161-file baseline with zero unexpected diffs; deliberately mutating one unit makes the test FAIL; the regen workflow is documented in the crate README.
  - *Why:* 161 units have no tests at all, so a generator rewrite would ship silent boot regressions across the whole fleet with nothing to compare against -- and once units start moving to SSOT, the pre-migration bytes are unrecoverable.

### Domain: E-18 Generate the 168 systemd units from SSOT -- floated SSOT values in units resolve at runtime by construction, closing the loop between the generator and the env producers. (1 tasks)
- **AGY-1362**: Make the generator emit the EnvironmentFile that backs every floated `${MIOS_PORT_*}`, and gate the contract  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Every generated unit referencing a floated `MIOS_*` carries the `EnvironmentFile` that supplies it and that var is emitted by the resolver; a fixture floating an unbacked var fails the gate; drift-gate green.
  - *Why:* The port-float tasks all assume the var exists at runtime; an unbacked float expands to EMPTY, so the socket binds nothing or `ExecStart` runs a truncated command — a hard break that no current check catches.

### Domain: E-18 Generate the 168 systemd units from SSOT -- generated units keep firing only on the platform they were written for. (1 tasks)
- **AGY-1355**: Preserve `Condition*`/`Assert*` substrate gating in the schema with a round-trip fidelity check  (WS-SYSTEMD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Every `Condition*`/`Assert*` directive in the 161 golden units appears identically in the generated units; deliberately dropping a `ConditionVirtualization` in a fixture turns the check red; drift-gate green.
  - *Why:* Losing a `ConditionVirtualization=wsl` or `=microsoft` gate makes a unit run on bare metal or QEMU where it bricks boot (226/NAMESPACE, per the preset's own `mios-wsl-early` warning) — a correctness axis the sandbox and port-float tasks do not touch.

### Domain: E-18 Generate the 168 systemd units from SSOT -- generates the highest-value runtime surface from SSOT and clears the densest cluster of hardcoded ports in the `.service` tree (Law 7 NO-HARDCODE). (1 tasks)
- **AGY-1334**: Migrate the AI-plane service units with ${MIOS_PORT_*} float  (WS-SYSTEMD | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: AI-plane units render from SSOT; every `ExecStart`/`Environment` port carries a `${MIOS_PORT_*}` placeholder resolving to the `[ports]` value; no bare AI-plane port literal remains in the `.service` tree; drift-gate and `cargo test` green.
  - *Why:* Repointing the canonical `:8642`/`:8643` front door in mios.toml today leaves these units on the old literals, so the ONE OpenAI `/v1` contract (NS-2) silently breaks with services listening where nothing connects.

### Domain: E-18 Generate the 168 systemd units from SSOT -- make the least-privilege sandbox posture a machine-enforced ratchet so no newly-added unit can silently regress it. (1 tasks)
- **AGY-995**: Add a native `systemd-analyze security` fitness-function drift-gate over every long-running unit  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the check scores every long-running unit, passes on the current tree, exempts only the privileged roster, fails a deliberately-added unit missing the required directives, runs under `just drift-gate`, and both repos carry the exemption roster.
  - *Why:* "Confine every unit" is currently an aspiration enforced by reviewer attention alone; one unhardened unit added in a hurry gives a compromised service the full host, and nothing in CI would notice.

### Domain: E-18 Generate the 168 systemd units from SSOT -- makes one `[firewall.open_ports]` selector the single declaration of what MiOS exposes, driving both the boot-time unit and the build-time firewall config. (1 tasks)
- **AGY-1329**: Collapse the three parallel firewall port lists into one SSOT-derived generator  (WS-SYSTEMD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Adding one key to `[firewall.open_ports]` changes both the boot-time service and the build-time firewall config with zero hand-editing; the `.service` renders byte-identical (modulo the SSOT-driven list) to golden; drift-gate green.
  - *Why:* Three divergent copies of the exposed-port list mean a port can be opened at build but closed at boot (or the reverse) -- a live security and availability hazard where the firewall state depends on which of three files was last edited.

### Domain: E-18 Generate the 168 systemd units from SSOT -- makes the hardened posture the emitted default so no generated unit can regress into the unconfined majority. (1 tasks)
- **AGY-1324**: Bake deny-by-default sandbox directives into the generator's Service renderer  (WS-SYSTEMD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Generating a minimal `[units.*]` service yields every baseline hardening key; a unit listing an override omits/relaxes exactly that key and nothing else; the hermes-worker equivalent renders byte-identical to its golden snapshot; unit tests cover the default+override matrix.
  - *Why:* About 40 shipped services run unconfined today, and every hand-authored unit added since has depended on an author remembering to harden it -- a posture that has demonstrably not held and that the generator can fix permanently in one place.

### Domain: E-18 Generate the 168 systemd units from SSOT -- moves the install-ordering DAG itself into SSOT where the After/Wants/Requires graph can be validated centrally. (1 tasks)
- **AGY-1327**: Migrate the 11 .target units to generated [units.*.target] grouping  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: All 11 targets render byte-identical to golden; the DAG grouping is declared exactly once in `[units.*.target]`; the dangling-ref gate is green; drift-gate and `cargo test` green.
  - *Why:* Targets are how MiOS selects a machine role (compute/controller/desktop/headless/k3s), and that role graph is currently 11 hand-edited files where a typo produces a role that silently starts nothing.

### Domain: E-18 Generate the 168 systemd units from SSOT -- no generated unit ships that systemd itself cannot load, so mechanical generation is safe to trust. (1 tasks)
- **AGY-1360**: Gate every generated unit through `systemd-analyze verify` so structural breakage fails the build, not the boot  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A fixture unit with a bad directive or a dangling `Requires=` fails the gate and prints the `systemd-analyze verify` output; a clean generation passes; the check SOFT-skips off-Linux and hard-gates in CI/bake.
  - *Why:* Today a subtly-malformed generated directive surfaces only as a boot-time load failure on a deployed host — the most expensive place to find it — and generating 168 units mechanically multiplies that exposure.

### Domain: E-18 Generate the 168 systemd units from SSOT -- no unit in the DB plane is hand-maintained and none ships unconfined. (1 tasks)
- **AGY-1335**: Generate the pgvector/backup/embed-backfill unit family from `[units.*]` with the DB port floated  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The DB-adjacent units render byte-identical to golden from SSOT with the pg port floated, backup service+timer are paired in one `[units.*]` block, and `cargo test` plus `just drift-gate` are green.
  - *Why:* These units front the sole agent datastore yet carry a hardcoded 8432 and zero confinement — a port move breaks backups silently, and any compromise of a backup oneshot runs with full filesystem write.

### Domain: E-18 Generate the 168 systemd units from SSOT -- no unit silently loses its hardening, enforced as a check rather than a convention. (1 tasks)
- **AGY-1492**: Add a systemd sandbox fitness function over every long-running unit  (WS-SBOM | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the linter/gate flags any non-exempt Service unit below the directive floor; the privileged roster and documented deviations are exempt via SSOT; adding a bare new unit fails the gate; negatives-before-main ordering preserved; `just drift-gate` green; both repos carry it.
  - *Why:* An immutable image is only as hardened as its services -- 74 of 84 units run today with no confinement floor, and the next daemon someone adds widens the attack surface with nothing to object.

### Domain: E-18 Generate the 168 systemd units from SSOT -- one enablement authority, not a build-time preset and a runtime case statement that can disagree. (1 tasks)
- **AGY-1353**: Unify role-apply's runtime enablement with the generated `.target` units via `[units.*].roles`  (WS-SYSTEMD | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `role-apply` drives enablement from the SSOT-generated role map; a characterization test shows each archetype enables an identical unit set before and after; the `.target` `Wants=` and the role map both derive from one `[units.*].roles` source; drift-gate green.
  - *Why:* Otherwise the target-migration task ships `.target` files whose grouping silently diverges from what `role-apply` actually enables at boot — two authorities for the same fact, and the runtime one wins invisibly.

### Domain: E-18 Generate the 168 systemd units from SSOT -- one render authority, so nothing re-mutates a generated unit after the build. (1 tasks)
- **AGY-1359**: Retire the deploy-time `34-render-quadlets.sh` envsubst pass once values float at generation time  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `34-render-quadlets.sh` reports zero rewrites across all generated units; the phase is removed or reduced to legacy-only with no runtime placeholder left unrendered; boot-time smoke and drift-gate green.
  - *Why:* Two authorities rendering the same placeholders means the deploy-time pass can silently rewrite a correctly generated unit; the demote-33 task retires the AUTHORING path but leaves this separate RENDER path live.

### Domain: E-18 Generate the 168 systemd units from SSOT -- only units MiOS actually ships enter the `[units.*]` roster, so generation does not immortalize corpses. (1 tasks)
- **AGY-1364**: Retire dead unit files together with their preset lines and SSOT blocks so the generator roster equals the live set  (WS-SYSTEMD | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Each removed unit has no remaining unit file, preset line, SSOT block or inbound `Wants=`/`Requires=`; the generator's `[units.*]` roster equals the live shipped set; drift-gate + `systemd-analyze verify` green; changes staged by explicit path.
  - *Why:* Migrating dead units into the generator would carve them permanently into SSOT and keep shipping inert `[containers.*]` blocks that mislead every future reader about what MiOS runs.

### Domain: E-18 Generate the 168 systemd units from SSOT -- parameterized units survive generation as templates, not as flattened instances. (1 tasks)
- **AGY-1357**: Model templated `@` instance units and preserve systemd `%`-specifiers in the generator  (WS-SYSTEMD | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Generated `@`-template units are byte-identical to golden with every `%`-specifier intact; declared instances such as `user@1000.service` are enabled via the generated preset; `cargo test` + drift-gate green.
  - *Why:* A naive per-unit renderer either resolves `%i` at build time (producing one wrong frozen instance) or drops the template entirely; the GPU-detect-family task covers a static family, so nothing else guards specifier semantics.

### Domain: E-18 Generate the 168 systemd units from SSOT -- proves the generator handles the port-float requirement, closing a bare-port-literal hole that feeds the zero-hardcodes campaign (Law 7 NO-HARDCODE). (1 tasks)
- **AGY-1328**: Float ListenStream from [ports] and migrate the socket unit family  (WS-SYSTEMD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The socket `ListenStream` carries a `${MIOS_PORT_*}` placeholder resolving to 8091 at deploy; generator output matches golden; no bare `:8091` or `ListenStream=[0-9]` literal remains in the socket family; drift-gate green.
  - *Why:* Changing the cockpit-link port in mios.toml today leaves the socket listening on the old 8091, so SSOT and the running listener disagree -- and the `.d` drop-in makes the same literal wrong in two places.

### Domain: E-18 Generate the 168 systemd units from SSOT -- puts the `/var` persistence contract (NS-1) into SSOT and completes the passive-unit families before the Service migrations. (1 tasks)
- **AGY-1331**: Migrate the 4 .mount units to generated [units.*.mount]  (WS-SYSTEMD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: All 4 `.mount` units render byte-identical to golden; the generator handles the `.mount` type; drift-gate and `cargo test` green; `check_no_mkdir_in_var` still passes.
  - *Why:* The `/var` persistence topology is what survives a `bootc upgrade`, yet it lives in four hand-edited files the operator cannot inspect from the config surface -- and a wrong `Where=` costs the persisted data on the next boot.

### Domain: E-18 Generate the 168 systemd units from SSOT -- resource tuning becomes a one-line operator change instead of an edit across 46 override directories. (1 tasks)
- **AGY-1337**: Model the 46 drop-in `.d/*.conf` override fragments as `[units.*.dropins]` and generate them  (WS-SYSTEMD | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: All 46 fragments render byte-identical to golden from `[units.*.dropins]`, resource limits are SSOT-typed rather than free text, regenerating after a single SSOT edit changes only the intended fragment, and `cargo test` + drift-gate are green.
  - *Why:* Drop-ins are the densest hand-maintenance tax in the unit surface — tuning the daemon's 800% CPU burst today means finding and editing one of 46 scattered `.conf` files with no schema, no validation and no gate.

### Domain: E-18 Generate the 168 systemd units from SSOT -- stands up the compiled façade behind which hand-authored units get replaced one family at a time. (1 tasks)
- **AGY-1322**: Scaffold the compiled mios-unit-gen crate (serde/miette/thiserror) in the native workspace  (WS-SYSTEMD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo build -p mios-unit-gen`, `cargo fmt --check`, and `cargo clippy -p mios-unit-gen -- -D warnings` all pass; `mios-unit-gen --selftest` exits 0; the crate is a workspace member.
  - *Why:* Every unit family migrated after this inherits typed diagnostics and clippy gating for free; skipping the discipline up front means retrofitting it across a dozen families later, and the Rust plane still lacks the shellcheck-equivalent bash already has.

### Domain: E-18 Generate the 168 systemd units from SSOT -- the cross-platform unit surface projects from one SSOT instead of a hand-copied Windows fork. (1 tasks)
- **AGY-1356**: Generate the Windows/WSL quadlet variants from the same SSOT with a Law 15 cross-repo parity gate  (WS-SYSTEMD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The Windows quadlets are generated from SSOT byte-identical to a golden capture; image/port/network parity vs the Linux quadlet is drift-gated; the SSOT change is present in both repos; `:latest`+SBOM intent is preserved with no hand-pinned digest.
  - *Why:* MiOS is explicitly cross-platform, yet the Windows quadlet tree is an ungenerated hand copy that silently diverges from the Linux SSOT — the exact divergence class this campaign exists to eliminate, and no other task touches it.

### Domain: E-18 Generate the 168 systemd units from SSOT -- the enablement SSOT stops being a 271-line hand-maintained list. (1 tasks)
- **AGY-1351**: Generate the system and user `90-mios.preset` enablement rosters from `[units.*].enable`  (WS-SYSTEMD | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-unit-gen --emit-preset` produces byte-identical system and user preset files vs the committed golden; `cargo test` parity is green; `just drift-gate` is green; the preset is regenerated during the build and staged by explicit path.
  - *Why:* The preset's own comments (lines 212-225) record the `mios-ai-firstboot` incident where dropped enable lines left the AI plane silently DEAD on first boot — it is the most fragile surface in this domain and nothing generates or validates it.

### Domain: E-18 Generate the 168 systemd units from SSOT -- the first strangler slice, proving the generator reaches byte-parity on real shipped units. (1 tasks)
- **AGY-1326**: Migrate the 10 timer units to generated [units.*.timer] with SSOT-declared cadence  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: All 10 timers render byte-identical to golden; `mios-unit-gen --check` reports the timer family in sync; drift-gate and `cargo test` green.
  - *Why:* Until one real family renders byte-identical, the generator is unproven and no higher-risk service migration can be justified -- and every cadence stays a hand-edited literal the operator cannot see or tune from the config surface.

### Domain: E-18 Generate the 168 systemd units from SSOT -- the generated ordering DAG is provably acyclic, so SSOT-driven units cannot deadlock boot. (1 tasks)
- **AGY-1361**: Detect After/Requires/Wants ordering cycles inside mios-unit-gen before any unit is rendered  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A fixture with a deliberately-introduced cycle fails generation with the cycle path printed; the real SSOT generates a clean topo order; `cargo test` covers the cycle and self-dep cases; drift-gate green.
  - *Why:* The existing tasks fix one known stale ref (`mios-ai.target Wants=`) and gate dangling refs, but nothing validates acyclicity — the failure mode that HANGS boot (systemd breaks a cycle arbitrarily) rather than merely 404ing a unit.

### Domain: E-18 Generate the 168 systemd units from SSOT -- the last hardcoded-port host services become a projection, with a clean host-unit vs container-quadlet split. (1 tasks)
- **AGY-1336**: Generate the web-plane host-side helper services (cockpit-link, ttyd, dashboard-issue) from SSOT  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Web-plane host services render from SSOT with ports floated, no ttyd/cockpit-link port literal remains in `usr/lib/systemd/system`, no file is emitted by both generators, and `cargo test` + drift-gate are green.
  - *Why:* These helpers are where the port-float sweep currently stops — hardcoded 8681/8682/8091 in units means changing a port in `mios.toml` produces a half-moved service, and the generator ownership boundary stays undefined.

### Domain: E-18 Generate the 168 systemd units from SSOT -- the pods SSOT stays authoritative for BOTH downstreams (Quadlets and k3s), not just the one the generator touches. (1 tasks)
- **AGY-1365**: Gate that generated pods project faithfully to k3s so the cluster path cannot silently diverge  (WS-SYSTEMD | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Changing a pod's membership or port in SSOT without re-projecting k3s FAILS the gate; a consistent regeneration passes; the check SOFT-skips without podman; drift-gate green on Linux/CI.
  - *Why:* The generator work touches only the Quadlet side, so today a pod change lands in systemd while the k3s manifests keep the old membership/port — a silent third divergence surface, exactly what this campaign is meant to eliminate.

### Domain: E-18 Generate the 168 systemd units from SSOT -- the user manager scope stops being an entirely hand-maintained island. (1 tasks)
- **AGY-1358**: Generate the user-scope quadlets and the user-preset (rootless user-manager scope)  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: User-scope quadlets and the user-preset generate byte-identical to golden; install targets are `default.target`/`graphical-session.target` rather than `multi-user.target`; drift-gate green.
  - *Why:* Every other migration task is system-scope, so the user manager — different install targets, no root, its own preset file — would be left hand-maintained and would silently receive system-scope defaults if generated carelessly.

### Domain: E-18 Generate the 168 systemd units from SSOT -- the whole `usr/lib/systemd/system` surface becomes a projection, the WS-SYSTEMD end-state. (1 tasks)
- **AGY-1338**: Generate the oneshot infra tail (perms/init/WSL/flatpak families) with shared unit bases  (WS-SYSTEMD | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The oneshot tail renders byte-identical to golden, shared bases visibly collapse the repeated `After=`/`Condition=` blocks, every referenced `/usr/libexec/mios` backend still resolves on the built image, and `cargo test` + drift-gate are green.
  - *Why:* This tail is the bulk of the 84 services; while it stays hand-authored the campaign cannot claim the unit surface is SSOT-derived, and each new perms/WSL unit is another copy-pasted file nobody validates.

### Domain: E-18 Generate the 168 systemd units from SSOT -- turns 161 hand-authored files into projections of one typed source (Law 8 SSOT-PROJECTION, NS-3). (1 tasks)
- **AGY-1323**: Define the [units.*] typed SSOT schema in mios.toml, mirroring the [containers.*] nested convention  (WS-SYSTEMD | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-unit-gen` deserializes `[units.*]` into typed structs and emits a miette span error on a bad shape; the ~5 encoded units render byte-identical to their golden snapshots; both repos' mios.toml parse under `tomllib` with a sane `wc -l`.
  - *Why:* Without one schema there is nothing for the generator to read, and every unit stays a hand-edited file whose values (ports, ordering, hardening) are invisible to the operator's single config surface.

### Domain: E-18 Generate the 168 systemd units from SSOT -- unit generation adds a projection, never a THIRD parallel declaration of service identity. (1 tasks)
- **AGY-1363**: Bind generated `User=`/`Group=` to the existing `[services.*]` uid/gid table so identity has exactly one source  (WS-SYSTEMD | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Generated units derive `User=`/`Group=` solely from `[services.*]`/`[accounts]`; a mismatch between a unit's owner and the `[services.*]` uid fails the gate; no unit re-declares a uid; drift-gate green.
  - *Why:* The campaign exists to kill parallel definitions (the operator flagged the triple-resolver smell); letting `[units.*]` carry its own identity would recreate exactly that divergence and desync units from `sysusers.d`, producing units that run as a uid the system never created.

### Domain: E-18 Generate the 168 systemd units from SSOT -- zero un-generated artifacts remain under `usr/share/containers/systemd`. (1 tasks)
- **AGY-1350**: Bring the two `.image` quadlets under generate-pod-quadlets.py coverage  (WS-SYSTEMD | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Both `.image` quadlets render from `[images.*]` byte-identical to the committed files; `--check` covers them; `check_pod_quadlets` is green; no hand-maintained `.image` file remains.
  - *Why:* Two hand-maintained files in an otherwise-generated directory are the ones that drift — they are edited directly, skip the SSOT, and are invisible to the quadlet drift-check.

### Domain: E-18 One SSOT declaration drives every consumer -- a placement constraint stops being hand-maintained in two scheduler dialects. (1 tasks)
- **AGY-1595**: Project [blade.requires] to k3s nodeSelectors and Pacemaker location rules  (WS-BLADE | P1 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every service in `[blade.requires]` yields a k3s selector or a Pacemaker location rule; a new capability added to SSOT appears in both without editing either scheduler's config; a drift-check fails when a hand-written constraint exists that SSOT did not produce.
  - *Why:* two schedulers with hand-maintained constraints drift silently, and the drift only surfaces as a workload that mysteriously will not schedule.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- clevis/LUKS TPM binding is SSOT-projected and provably gated, per Law 8. (1 tasks)
- **AGY-1701**: Turn `check_clevis_luks` into a real regenerate-and-diff gate  (WS-RUNTIME | P1 | M)  DONE
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: deleting the generator turns the gate RED; a broken SSOT read turns the gate RED; a committed golden artifact exists and a second generator run diffs clean; no `MIOS_OLLAMA_*` token remains in `referenced_names.txt`.
  - *Why:* the gate is currently green by construction, so the entire clevis/LUKS SSOT read can be broken (or the projector deleted) with zero signal -- and a purged legacy token has crept back into the names registry.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- clevis/LUKS TPM binding must be SSOT-wired and drift-gated rather than shipped as dead code. (1 tasks)
- **AGY-1478**: Collapse the two divergent LUKS SSOT tables onto [security.luks] and make the recovery keyslot unconditional  (WS-SBOM | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: both tools read `[security.luks]`; mios-luks-enroll enrolls a recovery keyslot unconditionally and rejects `recovery=false`; no consumer references `[security.disk_encryption]`; drift-gate and negatives are green; the SSOT is mirrored in both repos.
  - *Why:* Disk-unlock enrollment is dead code reading a table that does not exist, so operators believe they have TPM-bound encryption they do not have -- and the one escape hatch, a recovery keyslot, is optional enough to brick a fleet after a firmware update.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- greenboot health COVERAGE is gated so every critical service has a check and a rollback path. (1 tasks)
- **AGY-1703**: Repair the greenboot coverage check: undefined `_fail`, shadowed function, hardcoded service list  (WS-RUNTIME | P0 | M)  [BROKEN]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: removing a greenboot check script for a listed service turns the gate RED (not exit 127); check-54's original assertions still run; `critical_services` is read from mios.toml; `hermes` appears in the list and has a health script; `just drift-gate` exit 0.
  - *Why:* this is a live P0 -- the drift-gate itself crashes with exit 127 on exactly the condition it exists to detect, and it silently deleted a previously-working check while doing so.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- greenboot health coverage becomes SSOT-derived and actually covers the AI plane. (1 tasks)
- **AGY-1494**: Derive greenboot's critical-service list from SSOT and probe Hermes :8642 at boot  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `check_greenboot` derives its service list from `[greenboot].critical_services` with no hardcoded triple; a `required.d` check probes Hermes `:8642`; editing the SSOT list visibly changes what the gate enforces; greenboot rolls back on a failed AI-plane boot; drift-gate and negatives green; both repos carry it.
  - *Why:* The gate asserts a service list copied by hand into the checker, so it drifts from the real SSOT the moment either side changes -- and with no AI-plane probe a broken publish boots "healthy" with a dead front door.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- greenboot health coverage extends from the AI plane to the generated unit surface, so a bad publish rolls back. (1 tasks)
- **AGY-1345**: Add a greenboot required.d check that the SSOT-generated core units actually come up  (WS-SYSTEMD | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The new required.d check asserts the generated core units are enabled/loadable with its list derived from SSOT; masking a core unit trips the check in a VM boot test; the check is wired and executable through `78-greenboot.sh`.
  - *Why:* A generator regression today rolls forward across the fleet — boot-counted rollback is the only mechanism that catches a broken generated unit after the image is already published.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- greenboot health coverage that is memory-safe and cannot false-fail a fleet into rollback. (1 tasks)
- **AGY-1025**: Port the greenboot AI-plane required health check to a static Rust binary  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust check returns the identical exit code to the bash for the all-up, one-down, unit-disabled and port-unresolved fixtures; a non-zero exit still triggers greenboot rollback; the golden trycmd fixtures are green.
  - *Why:* This check decides whether a freshly-upgraded host keeps its new image or rolls back; a shell probe that mis-parses an unresolved port can roll an entire fleet back on a false negative, and greenboot itself is moving to Rust for bootc.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- make boot-counted rollback actually detect a broken update instead of rubber-stamping it. (1 tasks)
- **AGY-990**: Give greenboot real required.d health-checks (Hermes /v1 + core Quadlets) backed by `miosd healthcheck`  (WS-LANG-AUTO | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `required.d` contains a Hermes + core-Quadlet health-check backed by `miosd healthcheck`, a simulated Hermes-down marks the boot red and exercises the rollback path in a unit test or harness, 78-greenboot.sh stays thin enable/chmod, and the drift-gate is green.
  - *Why:* Hollow greenboot checks defeat the entire boot-counted rollback promise: signing, UKI and composefs are worthless if a broken update boots "green" and the fleet has no way back.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- multi-vendor GPU CDI (ROCm/Intel alongside NVIDIA) is SSOT-driven, not unconditional. (1 tasks)
- **AGY-1702**: Make `[gpu.vendors]` drive the CDI toolkit install and gate it  (WS-RUNTIME | P1 | M)  DONE
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: disabling a vendor in `[gpu.vendors]` demonstrably skips its toolkit install; the new check greps non-empty for the per-vendor CDI projection and fails when a vendor is enabled with no spec; the block sits under its own heading; gate green.
  - *Why:* every image currently carries AMD and Intel CDI toolkits whether or not the operator wants them, inflating the bake that the publish runner must hold, and no gate notices when vendor selection stops working.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- one audited health-check crate so every critical service has a real check and a rollback path. (1 tasks)
- **AGY-1026**: Port the remaining greenboot required.d/wanted.d checks into the shared Rust greenboot crate  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each ported check returns the identical exit code to its bash predecessor across pass/fail/skip fixtures; required-vs-wanted rollback semantics are preserved; the bash-tool ratchet ceiling drops by the number ported; golden tests green.
  - *Why:* A dozen scripts each re-implement the `/dev/tcp` probe idiom slightly differently, so a fix to one probe never reaches the others and boot-integrity self-healing is only as good as the sloppiest copy.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- the mesh projection satisfies Law 8 (emitted by a generator AND guarded by a regenerate-and-diff gate). (1 tasks)
- **AGY-1709**: Add the missing mesh drift-check and give `mios-metal-mesh-gen` a consumer  (WS-MINI | P1 | M)  DONE
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `check_metal_mesh` is registered in `main()` and fails on a hand-edited mesh config; a real file consumes the generator output; all four `[mini.mesh]` keys appear in the rendered surface; a dedicated `agy: AGY-118` commit exists.
  - *Why:* an ungated generator with no consumer is a Law 8 violation that reads as done -- the vTPM and CIDR decisions never reach any surface that runs.

### Domain: E-19 Wire the shipped-but-unwired runtime capabilities -- the split-plane GPU binding is a real projection guarded by a gate that can fail. (1 tasks)
- **AGY-1708**: Make the `[mini]` vfio generator write real bind config and the gate non-tautological  (WS-MINI | P0 | M)  DONE
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the generator writes a vfio bind file containing device ids derived from `[mini]`; hand-editing that file turns the gate RED (not exit 127); all four `[mini]` keys are projected; the three corrections appear in the block or generator.
  - *Why:* P0 because the gate calls an undefined function -- it crashes the whole drift-gate on its own failure path -- and until then it is green tautologically over a generator that projects nothing.

### Domain: E-20 The bootc-native install legs -- the offline bare-metal leg is provably network-free and syntactically able to run. (1 tasks)
- **AGY-1710**: Gate `tools/install.sh` on the oci-archive path and fix the `to-disk` invocation  (WS-DEPLOY | P1 | S)  DONE
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the new check fails when `tools/install.sh` gains a network pull or loses the oci-archive reference; line 71 uses one DEVICE positional plus `--source-imgref`; the kickstart cross-ref exists; `MIOS_METAL_ENABLED` is out of the installer commit's names hunk.
  - *Why:* the one script standing between MiOS and blank hardware is ungated and, as written, would likely fail its single live invocation -- a failure only discoverable on real metal.

### Domain: E-21 One deploy front door: flatten every install path -- one guided installer file over one shared contract, on the path the web one-liner actually fetches. (1 tasks)
- **AGY-1697**: Redo the installer fold in the RIGHT repo and make `build-mios.sh` a real thin redirector  (WS-DEPLOY | P0 | L)  [BROKEN]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: mios-bootstrap.git carries the fold commit; `build-mios.sh` is a redirector under ~100 lines with no inline bootc/FHS logic; a bootc host run selects target `bootc`; `curl | bash` of bootstrap.sh reaches `mios-install.sh` (proven by `--dry-run` output) instead of falling through.
  - *Why:* as landed, the real web installer path is unchanged and a bootc host would be forced into fedora/FHS mode -- a shipped artifact installing the wrong thing, and Law 15's double-repo requirement is unmet.

### Domain: E-21 One deploy front door: flatten every install path -- one prereq resolver keyed off the chosen target, proven by a gate rather than by `bash -n`. (1 tasks)
- **AGY-1699**: Make the installer prereq resolver genuinely target-keyed, including rustup/cargo  (WS-INSTALL | P1 | M)  DONE
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `--dry-run` for two different targets prints two different resolved prereq sets; a build-target dry-run names rustup/cargo; a check fails when the resolver is bypassed; the deliverable is reachable from `C:\MiOS` without depending on an incidentally-present sibling checkout.
  - *Why:* a one-size prereq list installs podman on flash-only hosts and omits the Rust toolchain on build hosts, and with no gate the resolver can silently regress.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- MiOS splices its owned block into foreign operator JSON without ever clobbering a key it does not own. (1 tasks)
- **AGY-1374**: Port the json-merge kind (JSONC strip + array-merge-by-key) to Rust for vscode-colors and windows-terminal  (WS-DOTFILES | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Rust json-merge derive byte-matches both committed `fixture.expected` files; the unparseable-base exit-2 refusal reproduced; `tests/test-theme-merge.py` negative cases pass against the Rust path; `cargo test -p miosd` green.
  - *Why:* json-merge is the highest-risk kind because it writes into files the operator also owns — a wholesale array replace would silently delete their other Windows Terminal schemes, and that bug class is unrecoverable once applied to a live HOME.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- a recorded parity oracle exists, so the projection engine can be rewritten without behavior regressions. (1 tasks)
- **AGY-1367**: Capture golden-master trycmd/insta fixtures of every dotfiles verb and gate output BEFORE any porting  (WS-DOTFILES | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test` replays all captured fixtures green against the existing Python engine; `.snap` and `.trycmd` fixtures committed via explicit `git add` (never `git add -A`).
  - *Why:* The projection engine has no unit tests today, so any port is a blind rewrite — the only safe precondition is a recorded result to measure deviance against.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- a stable verb facade exists so surfaces migrate one slice at a time behind an unchanged CLI. (1 tasks)
- **AGY-1368**: Scaffold the `miosd dotfiles` clap subcommand as the compiled facade that initially execs the Python engine  (WS-DOTFILES | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd dotfiles check|render|diff` produce byte-identical stdout/stderr/exit vs the Python engine (the golden-master trycmd fixtures replay green); `cargo build -p miosd` green.
  - *Why:* Without a stable facade every ported slice would change the caller contract, forcing drift-checks, wrappers and the Justfile to be rewired repeatedly instead of once.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- brings the compositor (the liquid-glass north-star surface) under the one token dialect and under check 25. (1 tasks)
- **AGY-1391**: Fold the build-time Hyprland theme bake into the registry and retire the `@@MIOS_COLOR_*@@` sed dialect  (WS-DOTFILES | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: hyprland.conf is a registered template surface containing no `@@...@@` tokens and no hardcoded hex; 65-bake-hyprland.sh runs no color sed; check 25 gates hyprland.conf; the build stays green with byte-identical output.
  - *Why:* The compositor is a live theme surface using a rival token syntax plus a hardcoded fallback color -- a projection hole the drift-gate cannot see today, while the liquid-glass north star explicitly requires compositor effects to project FROM mios.toml.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- closes the browser-shell color surface, the last un-gated build-time projector. (1 tasks)
- **AGY-1392**: Fold the surfer/webshell XML bake into the registry and delete its hardcoded palette fallbacks  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the surfer shell XML is a registered template surface with no hardcoded hex; 67-bake-surfer.sh renders via the projector; check 25 gates the artifact; webshell output is byte-identical to the current tree.
  - *Why:* The browser shell still ships Catppuccin-era fallback hex that activates whenever the env vars are unset, producing a shell whose colors disagree with the operator's palette -- and no gate would notice.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- closes the last theme consumer that neither reads from nor re-triggers the SSOT. (1 tasks)
- **AGY-1400**: Move wsl-theme-bridge's light/dark mapping into `[theme]` SSOT and make a flip re-project surfaces  (WS-DOTFILES | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the bridge sources interval and gtk/color-scheme mapping from mios.toml `[theme]`; a light/dark flip re-projects theme surfaces; the WSL-only guard and degrade-open behavior are byte-unchanged.
  - *Why:* The one surface that reacts to the host OS carries hardcoded theme names and a magic interval outside the SSOT, so an operator changing their theme in mios.toml gets a WSL session that ignores them.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- drift-check 25 can be rewired to Rust without changing one character of operator-visible failure text. (1 tasks)
- **AGY-1372**: Port the `check` verb (drift compare + orphan-template completeness floor) to Rust with byte-exact diagnostics  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd dotfiles check` output+exit byte-match the Python check on a clean tree AND a seeded-drift tree (trycmd); `cargo test -p miosd` green.
  - *Why:* `check` is the verb drift-check 25 shells out to; any wording or exit-code drift in the port turns a green gate red (or worse, a red gate green) and breaks the enforcement plane the whole campaign leans on.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- eliminates the fourth independent palette resolver so the palette is resolved exactly once. (1 tasks)
- **AGY-1390**: Delete mios-generate-icons' private regex `[colors]` resolver and feed it the engine-resolved palette  (WS-DOTFILES | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-generate-icons` contains no mios.toml or `[colors]` reader of its own; the icon SVG set is drift-gated against a committed golden; `cargo test` and `just drift-gate` stay green with byte-identical SVG output versus the pre-change tree.
  - *Why:* A private regex scanner is exactly the divergent-resolver smell this campaign exists to kill, and this one silently drops the accent/info palette keys the SSOT owns -- so a palette change produces icons that disagree with every other surface.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- ends the strangler-fig with ONE projector in the tree rather than two forever. (1 tasks)
- **AGY-1398**: Terminal step: native status/diff summary in miosd, then delete the Python engine and its wrapper  (WS-DOTFILES | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: miosd renders the status/diff summary and tally natively; both Python files are deleted; no tracked file references them; `cargo test` and `just drift-gate` green with the `[migration]` toggle removed.
  - *Why:* Keeping the Python engine and a stdout-scraping wrapper beside the Rust binary is precisely the duplication this campaign exists to remove, and without a dependency-ordered final delete the tree ships two projectors indefinitely.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- equivalence is PROVEN over generated inputs, not spot-checked, before bash stops being canonical. (1 tasks)
- **AGY-1378**: Demote `mios-dotfiles-render` to a thin Rust-first shim and prove byte-parity with proptest differential testing  (WS-DOTFILES | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: proptest differential (>=256 cases) green with zero divergence; the shim routes to `miosd` under the toggle and to Python when unset; `just drift-gate` green.
  - *Why:* Example-based fixtures only cover the inputs someone thought of; without a generative oracle the port ships with unknown edge-case divergences that surface as corrupted operator config long after cutover.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- every registered surface renders real bytes and is really gated. (1 tasks)
- **AGY-1712**: Give the `[shell]`/`[editor]` surfaces real templates and targets, or remove them  (WS-DOTFILES | P2 | M)  [BROKEN]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the renderer's loaded-surface count equals its gated count; a missing template makes check-25 RED instead of skipping; each surviving surface has a fixture that changes when its template changes; negative-tests exist for the new surfaces and the ssh-merge kind.
  - *Why:* two dead registry entries inflate apparent dotfiles coverage by 2 of 16 surfaces, and the skip-on-missing-template behaviour means any future surface can be added wrong and still report green.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- every registry surface has a compiled `derive_fn`, closing the projection half of the strangler slice. (1 tasks)
- **AGY-1375**: Port the ini-merge, ssh-merge and registry derive kinds to Rust (gitconfig-live, ssh-config, windows-registry)  (WS-DOTFILES | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Rust derive byte-matches all three committed `fixture.expected` files; `tests/test-theme-merge.py` negative cases pass against the Rust path; `cargo test -p miosd` green.
  - *Why:* Until every kind has a compiled derive, the toggle can only route a subset of surfaces, so BOTH engines must stay maintained in parallel — the exact duplication this workstream exists to end.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- freezes the theme projection byte-for-byte before it becomes the compiled render engine. (1 tasks)
- **AGY-1558**: Characterization golden for mios-sync-theme (check-25 [colors] -> surfaces projection) before its port  (WS-TESTGOV | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A change to `mios-sync-theme` output fails the golden compare; the golden covers every `[colors]`-derived surface; the regenerate recipe is deterministic; drift-gate green.
  - *Why:* A drift-gated SSOT producer with no byte-parity net can be refactored or ported into silent color-surface drift across both platforms, visible only on an operator's desktop.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- identity config becomes operator-defined in mios.toml and drift-gated through the one engine. (1 tasks)
- **AGY-1381**: Fold ipa-enroll.env into the dotfiles registry and demote `tools/generate-ipa-enroll-env.py`  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Render byte-matches committed `etc/mios/ipa-enroll.env`; `check_ipa_enroll_projection` green via the engine; the generator is demoted to a shim; both repos mirrored.
  - *Why:* A one-off SSOT->env projector keeps its own default handling (the `MIOS.INTERNAL` realm fallback in particular) outside the resolver, so the operator's enrollment config can diverge from mios.toml with nothing but a bespoke check to notice.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- keeps the Windows half of the projection at parity instead of stranding it on the deprecated Python. (1 tasks)
- **AGY-1394**: Cross-compile miosd for Windows and add a windows-latest CI job for the live-apply path  (WS-DOTFILES | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a windows-target miosd is built and distributed; `cargo test` is green on a Windows CI runner covering registry/WT/vscode apply; `miosd dotfiles apply` on Windows produces the same HKCU and settings.json result as the Python engine.
  - *Why:* The entire reason the merge kinds exist is the Windows live-HOME apply; a Linux-only port would leave the registry/terminal/vscode surfaces on an engine slated for deletion, with no CI proving they still work.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- keeps the shared dotfiles SSOT byte-identical across mios.git and mios-bootstrap.git through the riskiest phase of the migration. (1 tasks)
- **AGY-1399**: Add a Law-15 cross-repo equivalence gate for the registry, templates and fixtures  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the gate detects an injected registry/template/fixture divergence between the two repos; both repos currently pass; the recipe is documented in the migration runbook.
  - *Why:* Law 15 mandates mirroring shared SSOT surfaces, and a per-surface migration is exactly when the two repos skew apart unnoticed -- producing a bootstrap that projects a different theme than the OS.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- makes "every projection routes through the one engine" a machine-checked invariant instead of a campaign intention. (1 tasks)
- **AGY-1388**: Add `check_projector_coverage`: prove no un-migrated standalone projector remains  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the check goes red if any listed artifact has no registry surface OR any producer still renders standalone; both negative tests fail the gate as designed; `just drift-gate` is green on the migrated tree.
  - *Why:* Nothing today stops someone de-registering a surface or reviving a shadow projector; the engine's own orphan-template sweep only sees templates it already owns, so the cross-producer hole is invisible until a surface silently stops updating.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- makes the compiled engine the thing that actually runs at boot and at the operator's prompt. (1 tasks)
- **AGY-1393**: Repoint the three runtime call sites (service unit, `mios dotfiles` verb, completion) at miosd, degrade-open  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: unit, verb and completion all invoke miosd with Python only as degrade-open fallback; boot ordering and SuccessExitStatus are unchanged; `mios dotfiles status/diff/sync` behave identically on a booted MiOS-DEV VM.
  - *Why:* The Rust port is inert until its real invokers call it; these two entry points are the boot oneshot and the operator verb, and neither is covered by the check-25 rewire task -- so the binary could ship complete and never execute.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- makes the drift-gate sound by proving projection is a pure function of the SSOT. (1 tasks)
- **AGY-1401**: Add a determinism gate: render twice under varied TZ/LANG/hash-seed and byte-compare  (WS-DOTFILES | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the twice-render byte-comparison passes under varied TZ/LANG/hash seed; a deliberately injected nondeterminism (e.g. unordered map iteration) fails it; `cargo test` and `just drift-gate` are green.
  - *Why:* A Rust==Python parity proptest does not prove run-to-run stability, so nondeterministic ordering could land in a committed artifact and show up as phantom drift-gate failures nobody can reproduce.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- makes the one global theme refresh a single compiled cross-platform entrypoint. (1 tasks)
- **AGY-1387**: Reimplement the mios-sync-theme global refresh as a shell-free `miosd dotfiles sync`  (WS-DOTFILES | P3 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd dotfiles sync` refreshes every surface plus the bridge byte-identically to the bash script; `mios-sync-theme.service` still starts and exits clean; the shim degrades open with miosd absent; `cargo test -p miosd` green.
  - *Why:* The single most-invoked theme path is bash calling Python calling bash, which cannot run on the Windows half and re-diverges every time a surface is added.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- moves one more standalone renderer behind the single `[dotfiles.registry.*]` engine without losing hardware-conditional behavior. (1 tasks)
- **AGY-1385**: Split the chrony PTP drop-in: projector owns the CONTENT, the service keeps the /dev/ptp0 probe  (WS-DOTFILES | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `check_chrony_ptp_dropin` is green while comparing an engine render (not bash syntax); the drop-in content is byte-derived from SSOT; the ptp0 gate in `mios-chrony-ptp.service` is textually unchanged; both repos carry any added mios.toml key.
  - *Why:* Today a hardware probe and a config projection are welded into one bash script, so the drift-gate can only lint the script rather than verify the output -- and any future SSOT change to NTP settings silently bypasses the projector.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- one compiled resolver every projected surface derives from, starting the collapse of the three parallel resolvers. (1 tasks)
- **AGY-1366**: Build the `mios-config` typed layered SSOT resolver crate (figment) as the compiled peer of `mios_toml.py`  (WS-DOTFILES | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo build -p mios-config` green; a `cargo test -p mios-config` differential test asserts `colors()` and `section()` byte-match the JSON emitted by `python3 usr/lib/mios/mios_toml.py` for the committed mios.toml; the crate is a workspace member.
  - *Why:* Without a compiled resolver every Rust port would re-implement layering ad hoc, and the three divergent resolvers (`mios_toml.py`, the userenv.sh twins, globals.ps1) the operator flagged stay three forever.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- one standalone parallel projector is removed and the settings path is proven to generalize off the theme engine. (1 tasks)
- **AGY-1380**: Fold cockpit.conf into the dotfiles registry and demote `tools/generate-cockpit-conf.py` to a shim  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Render byte-matches committed `cockpit.conf`; `check_cockpit_projection` green via the engine; `generate-cockpit-conf.py` is a thin shim handing to `miosd dotfiles`; both repos mirrored.
  - *Why:* Every standalone generator is a second projector with its own resolver, defaults and formatting rules that can drift from SSOT independently — cockpit.conf is one such file living outside the one engine today.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- projection and runtime side-effect are cleanly split, hardening the composefs/verity root-integrity control. (1 tasks)
- **AGY-1384**: Add a mode-select kind for prepare-root.conf and demote the render half of `automation/77-composefs-verity.sh`  (WS-DOTFILES | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Engine render byte-matches committed `prepare-root.conf` for both `verity` and `yes`; `check_composefs_projection` green via the engine; the remount-mask and `.orig` side-effects remain in bash; both repos mirrored.
  - *Why:* The root-integrity mode currently lives as two heredocs entangled with runtime mutations inside a build script, so changing `composefs_mode` in SSOT does not reliably change what ships — and no one can review the projection independently of the side-effects.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- removes the last hand-written projection living inside the global theme-refresh script. (1 tasks)
- **AGY-1386**: Convert the mios-sync-theme heredoc bridge (theme.json + mios-theme.css) into two registry surfaces  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the engine emits `theme.json` and `mios-theme.css` byte-identical to today's heredoc output; the heredoc is gone from mios-sync-theme; a drift surface gates both files; the registry block is identical in mios.git and mios-bootstrap.git.
  - *Why:* The CSS/QML-facing bridge that every desktop surface reads is currently generated by hex-interpolating Python inside a shell script -- invisible to check 25, and a second place a color can be wrong.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- removes the retired name so exactly one projector name exists in the tree. (1 tasks)
- **AGY-1397**: Delete the mios-theme-render deprecation alias and purge its 21 references (mios-sync-theme still calls it)  (WS-DOTFILES | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the alias file no longer exists; `grep -rn mios-theme-render` returns only intentional history/changelog mentions; mios-sync-theme emits no deprecation warning on a refresh.
  - *Why:* The primary orchestrator calls its own deprecated alias, so every boot-time refresh logs a warning and every reader of the tree sees two names for one engine.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- rollback is a first-class deliverable: one SSOT flip, not a build revert. (1 tasks)
- **AGY-1377**: Add the `[migration]` SSOT toggle so the operator flips Rust vs bash projector per surface with one value  (WS-DOTFILES | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: With `use_rust_projector=false` behavior is byte-unchanged (drift-gate green); flipping true routes every ported verb to `miosd` and the gate stays green; both repos carry the identical `[migration]` block.
  - *Why:* Without a toggle the cutover is an all-or-nothing commit: a regression on the operator's live HOME could only be undone by reverting and rebuilding the image, and no surface-by-surface rollout is possible.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- the boot-integrity projection baked inside the signed UKI is produced by the one compiled, tested engine. (1 tasks)
- **AGY-1383**: Add a kargs-flatten kind and fold `usr/lib/kernel/cmdline` off `tools/generate-uki-cmdline.py`  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The engine's flatten byte-matches committed `usr/lib/kernel/cmdline`; `check_uki_cmdline_projection` green via the engine; `generate-uki-cmdline.py` demoted to a shim; both repos mirrored.
  - *Why:* A mis-ordered or dropped karg in this file silently weakens Secure Boot / SELinux enforcement inside a SIGNED artifact — the failure is invisible at build time and unfixable at runtime without a re-sign.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- the engine can replace a BUILD-PHASE renderer, including one that previously risked baking host-specific config. (1 tasks)
- **AGY-1382**: Fold chrony.conf into the dotfiles registry and demote the render half of `automation/42-chrony-render.sh`  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Render byte-matches committed `chrony.conf`; `check_chrony_projection` green via the engine; `42-chrony-render.sh` is a thin shim; both repos mirrored.
  - *Why:* Today an NTP server list change means editing embedded python inside a build phase, and the build-host `/dev/ptp0` sensitivity is one refactor away from making the image non-reproducible per builder.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- the engine projects typed non-color config, not just hex, so standalone settings generators can fold in later. (1 tasks)
- **AGY-1370**: Port the SETTINGS-surface projector (`section -> @MIOS:section_key@`) to Rust for btop-conf and gitconfig  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Rust render of btop-conf and gitconfig byte-matches the committed artifacts and the golden-master snapshots; `cargo test -p miosd` green.
  - *Why:* The cockpit/ipa/chrony consolidation tasks all reuse the section-scalar path; without it proven in Rust, those parallel Python projectors cannot be demoted and keep multiplying.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- the migrated surface gains a static-analysis gate strictly stronger than the shellcheck it never had. (1 tasks)
- **AGY-1379**: Rewire drift-check 25 to the Rust projector and add cargo fmt/clippy/test gates for the crate  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Check 25 passes via `miosd`; `just drift-gate` runs fmt/clippy/test and FAILS on any warning or unwrap/panic lint; the Python fallback still passes when `miosd` is absent.
  - *Why:* A ported engine with no lint gate regresses the quality story — an `unwrap()` in the live-HOME write path would panic mid-apply, and today nothing in CI would stop that landing.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- the operator-editable surface map becomes a typed schema that fails loudly instead of silently mis-shaping. (1 tasks)
- **AGY-1371**: Deserialize `[dotfiles.registry.*]` into typed Surface structs (serde), replacing `_load_surfaces`  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Rust loads all 14 committed surfaces with identical (name,template,target,section,kind,fixture,policy) tuples; the three exit-3 guards reproduced as trycmd negative fixtures; `cargo test -p miosd` green.
  - *Why:* The registry is the ADR-0009/ADR-0010 operator surface; untyped dict loading admits a class of silent shape bugs where a mistyped `kind` or missing fixture degrades quietly instead of refusing, and every per-surface migration below needs this schema anchor.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- the shared token primitive every surface depends on is compiled and golden-tested first. (1 tasks)
- **AGY-1369**: Port the template derive + `@MIOS:token@` substitution engine to Rust behind the miosd facade  (WS-DOTFILES | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Rust `derive_template` output byte-matches the committed artifacts and the insta snapshots for all six color surfaces; `cargo test -p miosd` green.
  - *Why:* Every other surface builds on this primitive; porting anything else first would mean re-porting against a moving token engine, and it is the leaf with the strongest existing golden coverage.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- the single write path into the operator's real HOME is compiled, panic-free and refuses every unsafe target. (1 tasks)
- **AGY-1376**: Port the live-HOME apply/diff path (HOME-scope + symlink refusal, timestamped RAW backup) to Rust  (WS-DOTFILES | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd dotfiles diff|apply` output, backups and refusals byte-match the Python engine on a synthetic tempdir HOME (trycmd); `cargo test -p miosd` green.
  - *Why:* `apply` is the only code path that mutates the operator's real files; a missed symlink or unquoted-path case here destroys user data irrecoverably, and a wording change silently breaks the wrapper that parses its output.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- the whole template kind (six color + two settings surfaces) can run Rust-first behind the toggle. (1 tasks)
- **AGY-1373**: Port the `render` and `capture` verbs, including the lossy-round-trip refusal, to Rust  (WS-DOTFILES | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `miosd dotfiles render` reproduces every committed artifact byte-for-byte; `capture` round-trip-verifies all six color surfaces; `cargo test -p miosd` green.
  - *Why:* Without render/capture the Rust path can only observe drift, never fix it, so the toggle stays permanently unflippable and the Python engine stays canonical; a CRLF or newline slip here would also mass-drift every committed artifact.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- theme surfaces born FROM `[colors]` SSOT by a compiled renderer rather than an embedded python heredoc. (1 tasks)
- **AGY-1024**: Port mios-sync-theme to a native theme-surface renderer driven by mios-toml-core  (WS-LANGX | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the Rust renderer writes byte-identical `theme.json` + `mios-theme.css` versus the bash for the vendor palette; `--check` prints without writing; drift-check 25 (theme SSOT projection) is green; golden test green.
  - *Why:* An embedded python heredoc inside a bash tool is untestable and unlintable, and it is the single point where every theme surface is derived — a silent divergence there puts drift-check 25 red across the whole desktop.

### Domain: E-22 Dotfiles projection: one engine, every surface, both platforms -- turns a latent runtime `SystemExit(3)` into a caught PR failure and hardens the apply-target safety contract. (1 tasks)
- **AGY-1396**: Promote the runtime registry-schema invariants to a build-time drift-gate  (WS-DOTFILES | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a registry entry with a missing or untracked path, an absolute `apply.target`, or a dotted surface name fails the drift-gate at build time rather than at first run; the current registry passes unchanged.
  - *Why:* An operator editing the registry through the Portal (ADR-0009) can author a surface that stays green in CI and only explodes at runtime -- including an `apply.target` that writes outside HOME.

### Domain: E-23 DB-driven configuration and vector recall -- makes the embed-backfill worker that fills the pgvector columns provably correct at its bounds. (1 tasks)
- **AGY-1124**: Type and expand tests for memory/worker_tools and embed_backfill  (WS-DEBT | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: both modules are mypy-strict clean, tests cover batch bounds and dimension mismatch, and the sibling-test gate is green.
  - *Why:* The backfill path writes the vectors recall reads; a wrong-dimension insert corrupts retrieval with no visible error.

### Domain: E-7 Law 7 NO-HARDCODE holds in the tagger itself -- the tool that documents the codebase must not be the one carrying phantom constants. (1 tasks)
- **AGY-1582**: Resolve mios-ai-tag's hint cap, teacher endpoint and teacher model from SSOT  (WS-DOCGEN | P0 | S)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: no numeric or model literal remains in the tagger; `mios-hardcode-lint` is clean on the file; a re-tag leaves the 363 long hints byte-identical.
  - *Why:* three different values for one port and a model that does not exist mean the teacher path is untested folklore, and the 260 cap is a live data-loss trigger worth ~100k characters of prose.

### Domain: Each declared edition is produced and testable. (1 tasks)
- **AGY-1908**: The variants registry is declared but variants are not built  (WS-DEPLOY | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each declared variant has a produced artefact and a statement of what makes it that variant.
  - *Why:* a registry of editions that all resolve to the same image is a naming scheme, not a product line.

### Domain: Each privileged unit records why it needs privilege. (1 tasks)
- **AGY-1878**: Privileged Quadlets are enumerated but their privilege is not justified  (WS-SEC | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every privileged unit has a recorded justification and no unit exceeds it.
  - *Why:* privilege granted without a recorded reason is never revoked, because nobody knows what would break.

### Domain: Each registered drift says why it drifts. (1 tasks)
- **AGY-1833**: The unit drift register has a count but no per-entry reason  (WS-UNITS | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: an entry without a reason fails.
  - *Why:* 55 opaque names is a backlog nobody can plan; 55 named causes is a work-list.

### Domain: Each spine item names the tasks that clear it. (1 tasks)
- **AGY-1934**: The finalization plan and this register are not cross-linked  (WS-DOCS | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every spine item names its tasks and every task addressing a spine item says so.
  - *Why:* a plan and a task register that do not reference each other diverge, and the recorded state is that both already describe the same work differently.

### Domain: Edge nodes automatically discover local MiOS mesh clusters and perform mutual authentication handshakes. (1 tasks)
- **AGY-1947**: Avahi and mDNS zero-configuration discovery and handshake for edge nodes  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Newly booted edge nodes discover the host cluster via mDNS and appear in `/v1/cluster/nodes` automatically.
  - *Why:* Zero-touch edge onboarding eliminates manual network configuration when adding worker blades to a MiOS mesh.

### Domain: Edge/AI-lanes (1 tasks)
- **T-994**: NODEDROID-09 -- On-device inference that does not mortgage Law 5 (NNAPI is deprecated; AICore is vendor-coupled)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the handset answers `/v1/models` and serves a chat completion from a GGUF the fleet already bakes; NNAPI appears nowhere; and an ADR records why AICore/Gemini Nano was rejected on Law 5 grounds and under what conditions ExecuTorch would be adopted instead.

### Domain: Edge/Android (2 tasks)
- **T-992**: NODEDROID-07 -- Wireless join over the Blade mesh AP; the cable becomes the enrolment channel
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a handset enrolled over USB rejoins over Wi-Fi after unplug with no re-enrolment; the mDNS responder answers on the tether or the mesh link and on no other interface; and a node never enrolled over the cable cannot join over Wi-Fi at all.
- **T-993**: NODEDROID-08 -- Survive Android process lifecycle (phantom process killer) or admit the node is unreliable
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: enrolment reports whether the escape was applied and the node advertises itself **degraded** when it was not, rather than presenting healthy and dying later; steady-state child-process count is asserted by a test; and a SIGKILLed node is observed missing by the fleet within a bounded interval.

### Domain: Edge/Security (1 tasks)
- **T-995**: NODEDROID-10 -- A device identity the handshake actually implements
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: enrolment provisions a per-device keypair whose private half never leaves the handset; a peer holding only public material can verify but not impersonate; revoking one device does not require re-keying the fleet; and the docstring matches the implementation, in whichever direction is made true.

### Domain: Eliminate inter-process serialization overhead when transferring intermediate KV tensors between dispatch workers. (1 tasks)
- **AGY-1961**: Zero-copy KV-cache transfer over shared memory between co-located Python worker processes  (WS-SCHED | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Workers read and write shared memory tensors with strict concurrency locking and zero memory leaks.
  - *Why:* Serialization of multi-gigabyte KV caches across local Unix sockets consumes unnecessary CPU and memory bandwidth.

### Domain: Enable BHI_DIS_S in SPEC_CTRL and execute 32-branch history clearing loops to eliminate Spectre-BHI in <150ns. (1 tasks)
- **AGY-2556**: Hardware BHI_DIS_S enforcer and universal BHB history clearing guard in mios-bhi-guard  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security guard enforces BHI_DIS_S and BHB clearing across security domains in <150ns.
  - *Why:* Hardware BHI_DIS_S and BHB clearing protect kernel indirect branches from speculative gadget steering.

### Domain: Enable UFFD_FEATURE_PAGEFAULT_FLAG_WP to intercept and track memory page writes in <1us without mprotect overhead. (1 tasks)
- **AGY-2528**: userfaultfd write-protection engine and dirty page tracker in mios-uffd-guard  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Memory virtualization runtime tracks dirty pages and protects buffers via UFFD write-protection in <1us.
  - *Why:* userfaultfd write-protection enables ultra-fast incremental memory checkpointing and microVM live migration with zero mprotect penalties.

### Domain: Enable natural-language semantic querying over historical system logs and error traces. (1 tasks)
- **AGY-2009**: Unified log aggregation pipeline streaming journald events to pgvector  (WS-DURA | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Critical system log events are indexed into pgvector for conversational diagnostic queries.
  - *Why:* Allowing agents to semantically search system logs dramatically accelerates automated troubleshooting.

### Domain: Enable sandboxed WebAssembly agents to interact with local hardware sensors and actuators safely. (1 tasks)
- **AGY-1987**: Wasm host import for local hardware GPIO and I2C access on embedded edge nodes  (WS-NODE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Wasm sandbox exposes safe, permission-gated hardware interfaces for IoT edge devices.
  - *Why:* Edge agents often run on single-board computers (Raspberry Pi, industrial gateways) that require sensor telemetry.

### Domain: Enable systemd-journald FSS with 15-minute key evolution and seal verification keys to TPM 2.0 / MiOS-USB. (1 tasks)
- **AGY-2305**: Forward-Secure Sealed (FSS) journald logger and TPM key enrollment manager  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Journald seals logs cryptographically with FSS and TPM key protection.
  - *Why:* Forward-Secure Sealing prevents attackers from altering past logs even if root privileges are subsequently compromised.

### Domain: Enable targeted PR_SET_L1D_FLUSH on microVM vCPUs and cryptographic services to flush L1D in <500ns on switchout. (1 tasks)
- **AGY-2480**: Dynamic L1 Data Cache flusher and context-switch sanitizer in mios-l1d-flush  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security sanitizer flushes L1D cache lines on targeted context switchouts in <500ns.
  - *Why:* Targeted L1D cache flushing neutralizes L1TF/Foreshadow side-channel extraction without incurring whole-system performance penalties.

### Domain: Encrypt mutable filesystem domains independently and export inert ciphertext snapshots. (1 tasks)
- **AGY-2119**: Multi-domain independent LUKS2/fscrypt partition segregater and inert snapshot export tool  (WS-DURA | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Storage segregater enforces independent per-domain encryption and exports inert encrypted snapshots.
  - *Why:* Independent domain encryption ensures a breach in one subsystem does not compromise user home data or database vaults.

### Domain: Enforce -fcf-protection=full / -mbranch-protection=standard to insert ENDBR64/BTI landing pads and trap illegal jumps in <5ns. (1 tasks)
- **AGY-2560**: Automated IBT/BTI landing pad enforcer and control-flow compiler in mios-ibt-guard  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security runtime and build toolchain enforce IBT/BTI landing pad verification across all binaries and kernel modules.
  - *Why:* Indirect Branch Tracking prevents Return/Jump-Oriented Programming (ROP/JOP) gadget hijacking in hardware.

### Domain: Enforce -mharden-sls=all and insert INT3/ISB barriers after returns and jumps to stop speculative overrun in <5ns. (1 tasks)
- **AGY-2540**: Automated Straight-Line Speculation (SLS) compiler enforcer and post-branch traps  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Compiler and security runtime enforce SLS hardening across all built binaries with post-branch trap instructions.
  - *Why:* Straight-Line Speculation hardening eliminates speculative instruction overrun past returns without hurting execution speed.

### Domain: Enforce Landlock ABI v5 scoped rulesets to isolate abstract Unix sockets and signals within subagent sandboxes in <1us. (1 tasks)
- **AGY-2532**: Dynamic Landlock scoped IPC and signal isolation guard in mios-exec-sandbox  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Sandbox guard isolates abstract Unix sockets and process signals dynamically across Landlock ABI v5.
  - *Why:* Scoped Landlock IPC rules prevent rogue subagents from hijacking host abstract sockets or terminating other agent processes.

### Domain: Enforce PR_SPEC_FORCE_DISABLE on untrusted subagent processes via prctl to block Spectre v4 memory bypasses. (1 tasks)
- **AGY-2460**: Dynamic Speculative Store Bypass (SSB) process sandboxer and prctl controller in mios-ssb-guard  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security guard enforces per-process SSB mitigation and neutralizes Spectre v4 side-channel vectors.
  - *Why:* Targeted dynamic SSB mitigation eliminates CPU side-channels without penalizing system-wide performance.

### Domain: Enforce USBGuard policies, authenticate MiOS-USB keys, and mount mass storage strictly read-only. (1 tasks)
- **AGY-2396**: Declarative USBGuard device authorization daemon and read-only storage mounter  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: USBGuard blocks unauthorized devices and enforces read-only mounts on external storage.
  - *Why:* Declarative USB security blocks BadUSB keystroke injection attacks and prevents accidental data contamination.

### Domain: Enforce hardware IOMMU translation (iommu=force) and validate PCIe ACS isolation before device assignment. (1 tasks)
- **AGY-2215**: Strict IOMMU DMA remapper and PCIe ACS group validator in automation  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: IOMMU guard validates hardware isolation and blocks unsafe DMA device passthrough.
  - *Why:* Strict IOMMU DMA remapping prevents virtual machines and peripheral firmware from tampering with host RAM.

### Domain: Enforce ima_appraise=enforce in UKI kernel command line to verify security.ima xattrs and block tampered binaries. (1 tasks)
- **AGY-2524**: In-kernel IMA appraisal and signed xattr verifier in UKI bootchain  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Kernel blocks execution of tampered binaries via IMA appraisal and validates signed extended attributes.
  - *Why:* In-kernel IMA appraisal cryptographically guarantees that only untampered, signed binaries can execute on the operating system.

### Domain: Enforce in-kernel USB device authorization, whitelist known peripherals, and prompt on new devices. (1 tasks)
- **AGY-2241**: Declarative USBGuard policy generator and desktop authorization notifier in automation  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: USBGuard blocks rogue USB devices and grants access upon operator authorization.
  - *Why:* Declarative USB authorization neutralizes BadUSB hardware attacks and rogue peripheral tampering.

### Domain: Enforce logit-level GBNF grammar constraints to guarantee 100% syntactically valid JSON in a single pass. (1 tasks)
- **AGY-2283**: Logit-level GBNF grammar constrained decoder and JSON schema compiler in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine enforces GBNF logit masking and outputs guaranteed valid JSON schemas.
  - *Why:* Logit-level grammar masking eliminates JSON syntax errors and reduces agent tool-loop latency by eliminating retries.

### Domain: Enforce module.sig_enforce=1 and lockdown=confidentiality in UKI to reject unsigned modules with EKEYREJECTED. (1 tasks)
- **AGY-2514**: Strict kernel module signature enforcer and lockdown runtime in UKI bootchain  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Kernel enforces module signature checking and lockdown confidentiality across all module loads.
  - *Why:* Strict kernel module signature enforcement and lockdown mode protect the host kernel against rootkits and ring-0 code injection.

### Domain: Enforce mutual write exclusion on shared host-guest filesystems across Windows and Linux. (1 tasks)
- **AGY-2089**: virtiofsd POSIX/OFD lock translation and cache policy configurator  (WS-STRG | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Virtiofs daemon translates guest file lock requests to host OFD locks deterministically.
  - *Why:* Cross-platform lock translation prevents silent data corruption when host and guest modify shared files concurrently.

### Domain: Enforce strict CPU and memory cgroup limits on subagents and verify escape resistance in CI. (1 tasks)
- **AGY-2150**: Transient systemd-run subagent cgroup quota enforcer and escape test suite  (WS-ORCH | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that subagent cgroup quotas and sandbox isolation withstand escape attempts.
  - *Why:* Cgroup quotas prevent rogue subagents from consuming host resources or triggering system-wide memory exhaustion.

### Domain: Enforce strict default-deny network segmentation between Podman sidecar containers. (1 tasks)
- **AGY-2077**: Declarative nftables inter-container firewall rule generator  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Nftables generator applies least-privilege inter-container routing rules automatically on startup.
  - *Why:* Micro-segmentation prevents compromised front-end containers from accessing sensitive internal database ports.

### Domain: Enforce strict default-drop on non-VPN WAN traffic while split-routing local cluster mesh packets via fwmark. (1 tasks)
- **AGY-2191**: Declarative nftables VPN kill-switch and fwmark split-tunnel manager  (WS-NET | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: VPN kill-switch blocks WAN traffic during tunnel drop while keeping local mesh accessible.
  - *Why:* A strict firewall kill-switch prevents accidental IP leakage while preserving local cluster control.

### Domain: Enforce targeted SSBD via prctl on untrusted subagents to toggle hardware SSBD bit in <500ns and block Spectre v4. (1 tasks)
- **AGY-2544**: Dynamic SSBD context-switch enforcer and speculative store isolation guard in mios-ssbd-guard  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security guard enforces targeted SSBD on untrusted sandboxes and disables speculative store bypass in <500ns.
  - *Why:* Targeted SSBD enforcement neutralizes Spectre v4 memory disclosure while preserving peak performance for trusted system services.

### Domain: Enforce vm.unprivileged_userfaultfd=0 and allow UFFD_USER_MODE_ONLY descriptors for demand paging in <1us. (1 tasks)
- **AGY-2518**: User-mode-only userfaultfd enforcer and ephemeral page interceptor in mios-uffd-guard  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security guard enforces user-mode-only page fault handling and blocks kernel fault interception.
  - *Why:* Restricting userfaultfd to user-space memory protects the kernel against race-condition exploitation while enabling fast memory virtualization.

### Domain: Enrol and bind user/node authentication to physical MiOS-USB hardware tokens via FIDO2 and PKCS#11 in <10ms. (1 tasks)
- **AGY-2552**: Dedicated MiOS-USB global hardware key and FIDO2/PKCS#11 multi-node enrolment  (WS-AUTH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Authentication subsystem enrols and validates MiOS-USB hardware keys across all blades and edge nodes.
  - *Why:* Dedicated MiOS-USB hardware keys provide cryptographic, physical presence-backed authentication across all nodes.

### Domain: Enroll hardware security keys for touch-based sudo elevation, git signing, and WebAuthn web console login. (1 tasks)
- **AGY-2189**: Declarative FIDO2 pam_u2f and ssh-ed25519-sk hardware key enrollment tool in mios-fido2-enroll  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: FIDO2 enrollment tool configures pam_u2f, SSH-SK keys, and WebAuthn credentials seamlessly.
  - *Why:* Hardware-backed FIDO2 authentication provides phishing-proof security for administrative privileges and code signing.

### Domain: Ensure edge micro-nodes automatically reboot if the application process hangs or kernel deadlocks. (1 tasks)
- **AGY-1998**: Hardware watchdog timer integration (/dev/watchdog) in mios-node  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Watchdog integration guarantees autonomous reboot recovery for unattended edge devices.
  - *Why:* Unattended remote edge hardware requires hardware watchdog resets to recover from hard deadlocks.

### Domain: Ensure in-flight inference turns finish or checkpoint safely before process termination. (1 tasks)
- **AGY-1966**: Graceful worker shutdown and SIGTERM drain handler in server.py  (WS-AI | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Server drains connections and flushes pending database events before cleanly exiting on systemd stop signals.
  - *Why:* Abrupt service termination corrupts in-flight task records and drops client connections.

### Domain: Ensure repeatable, fast RPM package layering with persistent local cache in OCI image builds. (1 tasks)
- **AGY-2101**: Atomic DNF5 package installation pipeline with local cache staging  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: DNF5 builds execute atomically with local caching and automated mirror failover.
  - *Why:* Hermetic package caching accelerates build cycles and provides offline build repeatability.

### Domain: Establish direct P2P WireGuard and WebRTC connections through consumer NAT routers with automated DERP relay fallback. (1 tasks)
- **AGY-2193**: Tiered NAT traversal engine (UPnP, NAT-PMP, STUN hole punching, DERP relay) in mios-nat-traversal  (WS-NET | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: NAT traversal engine establishes direct or relayed peer connectivity through arbitrary firewall topologies.
  - *Why:* Automated NAT traversal allows remote blades and mobile laptops to join the cluster mesh without router reconfiguration.

### Domain: Evaluate INT8 activations via pure integer add/sub on 1-bit weight signs to run 70B models at >350 tok/s in 12GB RAM. (1 tasks)
- **AGY-2506**: BitNet A8W1 fused sign-accumulation matrix engine in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes BitNet A8W1 via fused sign-accumulation integer kernels at >350 tok/s on CPU.
  - *Why:* BitNet A8W1 completely removes floating-point multiplication overhead, enabling high-speed 70B inference on consumer CPUs.

### Domain: Evaluate peripheral driver health on boot and log degraded hardware states without blocking OS startup. (1 tasks)
- **AGY-2129**: Peripheral hardware health evaluator and non-fatal Greenboot degradation reporter  (WS-BOOT | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Greenboot hardware evaluator logs degraded peripherals gracefully without blocking system promotion.
  - *Why:* Degrade-not-refuse ensures portable bootability across diverse consumer laptops and custom motherboards.

### Domain: Evaluation/CI (1 tasks)
- **T-983**: Ship real evaluation suites and gate on their scores in CI
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A scored run executes in CI against a frozen suite, its baseline is recorded, and a regression below the baseline fails the tier.

### Domain: Every `ExecStart` path exists in the image. (1 tasks)
- **AGY-1843**: Units reference binaries that may not be installed  (WS-UNITS | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a unit whose binary the image does not contain fails.
  - *Why:* a unit that cannot start is a unit that fails at first boot, on the operator's machine rather than in CI.

### Domain: Every check in 98-drift-checks.sh has a known edit that makes it fail. (1 tasks)
- **AGY-1812**: Audit the 53 remaining gate heredocs for a possible red  (WS-GATE | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every one of the 53 has a recorded verdict and the un-failable ones have follow-up task ids.
  - *Why:* the roadmap calls this campaign 1 and says a hollow gate falsifies the thesis directly.

### Domain: Every declared deployment format is proven to work. (1 tasks)
- **AGY-1902**: Deployment formats are declared but not all exercised  (WS-DEPLOY | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each format is either exercised in CI or explicitly marked unexercised with a reason.
  - *Why:* a declared format nobody has booted is a promise, not a capability.

### Domain: Every declared table has a consumer. (1 tasks)
- **AGY-1913**: The SSOT has tables nothing reads  (WS-PROJ | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a new table with no consumer fails unless declared inert with a reason.
  - *Why:* a config key nobody reads is a promise to the operator that nothing keeps.

### Domain: Every fleet lane needs "hardware-facing roles live on the Blade, never on the hosted image" to be a fact the SSOT states, rather than a convention each task re-argues and one of them gets wrong. (1 tasks)
- **AGY-2583**: Declare the Blade/guest plane boundary and the three role shapes in SSOT  (WS-MINI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Each capability in `[blade.archetypes]` carries a role shape, the gate enforces that a guest-plane archetype cannot claim a Blade-plane capability, and the negative test fails for the right reason.
  - *Why:* T-333 found the placement machinery for a fleet is projected, gated and inert. An undeclared plane boundary is the same defect one level up: every lane re-derives it.

### Domain: Every generated file is regenerated and diffed in CI. (1 tasks)
- **AGY-1914**: Generated artefacts are not all covered by the artefacts step  (WS-PROJ | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every generator's output is refreshed by the sync step.
  - *Why:* a generated file outside the sync step drifts permanently and silently.

### Domain: Every systemd unit in the tree is what the SSOT renders. (1 tasks)
- **AGY-1618**: Drive mios-unit-gen --check to zero drift  (WS-EVIDENCE | P0 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-unit-gen --check` reports zero drifted units, a negative test proves it fails when one unit is edited, and the gate runs in CI.
  - *Why:* a projection that does not match its output is not a projection; it is two hand-maintained copies with extra steps.

### Domain: Every unit the image ships is declared in the SSOT. (1 tasks)
- **AGY-1830**: 52 shipped units are not declared in `[units.*]` at all  (WS-UNITS | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: undeclared reaches 0 and `--check` exits 0.
  - *Why:* the roadmap names unit projection the largest single gap in "one file defines the OS".

### Domain: Execute 2:4 structurally sparse weights via Sparse Tensor Core mma.sp instructions for 2x matrix throughput. (1 tasks)
- **AGY-2410**: 2:4 hardware structural sparsity engine and Sparse Tensor Core dispatcher in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes 2:4 structural sparsity via Sparse Tensor Cores at >1.8x speedup.
  - *Why:* 2:4 structural sparsity doubles GPU compute throughput on Ampere/Ada/Blackwell architectures with near-zero accuracy loss.

### Domain: Execute 32-entry benign call/ret loops on domain switchouts to overwrite RSB in <100ns and prevent ret2spec. (1 tasks)
- **AGY-2536**: Dynamic RSB buffer stuffing and context-switch underflow guard in mios-rsb-guard  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security guard overwrites 32 RSB entries on security domain context switches in <100ns.
  - *Why:* Dynamic RSB stuffing eliminates ret2spec underflow hijacking while preserving native hardware call/return performance.

### Domain: Execute 4-bit E2M1 weights via native mma.sync FP4 instructions with block-32 scales for >4x GEMM throughput. (1 tasks)
- **AGY-2436**: Native NVFP4 / MXFP4 Tensor Core execution engine and block-32 scale unpacker in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes native NVFP4 Tensor Core instructions with block-32 microscaling.
  - *Why:* Native FP4 Tensor Core execution unlocks 4x matrix throughput and allows 70B parameter models to run within 20GB VRAM.

### Domain: Execute AQLM 2-bit additive vector codebook lookups via fused CUDA kernels to fit 70B models in 16GB VRAM. (1 tasks)
- **AGY-2468**: AQLM additive vector quantization engine and multi-codebook CUDA lookup kernel in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes AQLM multi-codebook vector lookups via fused CUDA kernels.
  - *Why:* AQLM additive vector quantization achieves sub-2-bit model compression while retaining high reasoning fidelity.

### Domain: Execute AVX-512/AVX2 VNNI dot-product intrinsics with 32KB L1 cache blocking for >35 tok/s CPU inference. (1 tasks)
- **AGY-2428**: Fused VNNI vectorized dot-product kernel engine and L1 cache blocker in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes fused VNNI dot-product kernels with L1 cache blocking on CPU.
  - *Why:* Fused VNNI integer dot-products deliver fast, responsive local AI reasoning on CPUs without discrete graphics.

### Domain: Execute BitNet b1.58 ternary models via integer addition/subtraction GEMM to fit 70B models in 14GB RAM. (1 tasks)
- **AGY-2402**: BitNet b1.58 ternary tensor execution engine and pure integer addition GEMM kernels  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine loads BitNet b1.58 models and executes pure integer addition kernels on CPU.
  - *Why:* BitNet b1.58 ternary execution brings massive 70B model reasoning to low-power CPU nodes and laptops at ultra-fast speeds.

### Domain: Execute EXL2 fractional bitrate models (2.0-8.0 bpw) via fused CUDA kernels to fit 70B models in 24GB VRAM. (1 tasks)
- **AGY-2390**: Dynamic EXL2 fractional bitrate execution engine and fused CUDA kernel manager in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine loads EXL2 models and executes fused CUDA kernels at >100 tok/s.
  - *Why:* Fractional EXL2 quantization allows high-accuracy 70B models to run at blazing speeds on standard 24GB GPUs.

### Domain: Execute FlashAttention-3 with FP8 TMA hardware overlapping and warp specialization for >1,200 TFLOPS throughput. (1 tasks)
- **AGY-2446**: FlashAttention-3 warp-specialized kernel engine and FP8 TMA overlapping in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes FlashAttention-3 with warp specialization and TMA hardware acceleration.
  - *Why:* FlashAttention-3 unlocks peak hardware FLOPS on modern GPUs, enabling instantaneous multi-hundred-thousand token context prefill.

### Domain: Execute W4A8KV4 quantization via fused INT8 Tensor Core kernels for >3.2x speedup and sub-22GB 70B VRAM residency. (1 tasks)
- **AGY-2458**: QServe W4A8KV4 mixed-precision execution engine and fused INT8 dispatcher in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes QServe W4A8KV4 via fused INT8 Tensor Core kernels with >3.0x speedup.
  - *Why:* QServe W4A8KV4 aligns weights, activations, and KV cache to maximize hardware integer tensor core performance.

### Domain: Execute automated continuous fuzzing against custom eBPF programs and storage modules in QEMU microVMs. (1 tasks)
- **AGY-2155**: Headless QEMU Syzkaller / KASAN kernel and eBPF fuzzing test harness  (WS-BUILD | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Syzkaller fuzzing harness executes automated nightly fuzz cycles in isolated microVMs.
  - *Why:* Continuous kernel fuzzing catches memory safety vulnerabilities and driver deadlocks prior to release.

### Domain: Execute automated headless microVM boot tests in CI with KVM acceleration and TCG fallback. (1 tasks)
- **AGY-2099**: Headless QEMU KVM/TCG microVM boot and Greenboot verification test runner  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Headless microVM test runner boots generated images and validates greenboot health in automated CI.
  - *Why:* MicroVM boot testing catches bootloader, kernel module, and systemd regressions before physical hardware deployment.

### Domain: Execute background Btrfs/CephFS scrubs under ionice -c 3 and throttle dynamically on PSI I/O pressure. (1 tasks)
- **AGY-2315**: Storage integrity scrubber daemon with idle I/O priority and PSI pressure throttling  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Storage scrubber repairs bit rot in background with zero noticeable desktop latency degradation.
  - *Why:* Idle-class background scrubbing eliminates silent bit rot while preserving fluid interactive desktop I/O.

### Domain: Execute database schema updates transactionally with automated rollback on SQL syntax or constraint failure. (1 tasks)
- **AGY-2010**: Zero-downtime database schema migration runner with rollback safety checks  (WS-DURA | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Migration runner applies database upgrades safely with atomic rollback guarantees.
  - *Why:* Failed database migrations must never leave the persistent agent datastore in an inconsistent half-applied state.

### Domain: Execute lightweight 4-bit QLoRA fine-tuning on local GPUs during system idle states. (1 tasks)
- **AGY-2085**: Unprivileged containerized QLoRA fine-tuning engine using Unsloth  (WS-AI | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: QLoRA fine-tuning engine trains domain adapters cleanly inside unprivileged containers.
  - *Why:* Continuous local adaptation allows the coding model to specialize in the operator's specific codebase patterns.

### Domain: Execute multiple independent tool calls emitted in a single model turn concurrently. (1 tasks)
- **AGY-1965**: Asynchronous tool execution batching for non-dependent parallel tool invocations  (WS-AI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Read-only parallel tool calls execute concurrently with measurable reduction in total turn latency.
  - *Why:* Sequential execution of independent tool calls introduces unnecessary latency in multi-tool agent interactions.

### Domain: Expand branching candidate token trees and verify all paths in a single target forward pass for >2.8x speedup. (1 tasks)
- **AGY-2520**: SpecInfer dynamic multi-draft tree engine and 2D tree-attention mask verifier in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine verifies dynamic candidate token trees concurrently via 2D tree-attention masks at >2.8x speedup.
  - *Why:* SpecInfer tree speculation maximizes token acceptance per forward pass by exploring multiple plausible next-token trajectories concurrently.

### Domain: Expansion emits the steps the skill declares. (1 tasks)
- **AGY-1716**: Resolve the open-url-fallback-chain skill so tests/test-expand-from.py sees its three steps  (WS-CI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the suite passes in the `unit` tier against the repository tree with no MiOS installed.
  - *Why:* the fallback chain is what makes a URL open when the first browser is absent; nothing has tested it.

### Domain: Export compressed SquashFS templates over Unix NBD sockets and boot microVMs with RAM COW overlays in <15ms. (1 tasks)
- **AGY-2404**: SquashFS template streaming over Unix-socket NBD with ephemeral RAM overlay in mios-microvm  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Virtualization manager streams SquashFS templates over NBD and boots microVMs in <15ms.
  - *Why:* SquashFS NBD streaming enables massive microVM sandbox density with near-zero memory and disk footprints.

### Domain: Expose host memfd buffers via virtio-pmem with guest -o dax for >20 GB/s ephemeral sandbox storage. (1 tasks)
- **AGY-2331**: Virtio-PMEM direct DAX memory storage manager and memfd sandbox enclave in mios-microvm  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: MicroVM engine boots ephemeral sandboxes with virtio-pmem direct DAX memory storage.
  - *Why:* Virtio-PMEM DAX storage delivers 20+ GB/s I/O bandwidth and eliminates SSD write wear during high-volume agent sandboxing.

### Domain: Expose real-time preemption counts, queue latencies, and active KV slot allocations via Prometheus metrics. (1 tasks)
- **AGY-1958**: Continuous batch preemption metrics exporter for Prometheus on port 8640  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Prometheus endpoint reports preemption counters and slot swap histograms accurately.
  - *Why:* Visibility into tensor preemption and KV slot churn is essential for tuning scheduling heuristics.

### Domain: Expose typed Varlink JSON-RPC interfaces over point-to-point Unix sockets with systemd socket activation. (1 tasks)
- **AGY-2341**: Point-to-point Varlink IPC socket activator and typed interface compiler in mios-varlink  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: System services expose typed Varlink interfaces activated on-demand via systemd sockets.
  - *Why:* Point-to-point Varlink IPC eliminates broker daemon bottlenecks and provides strict schema validation.

### Domain: Extract recurring token n-grams from context to propose candidate branches for 1.8x-2.4x code/JSON speedup. (1 tasks)
- **AGY-2474**: Lookahead N-gram prompt-lookup speculative decoding engine in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes Lookahead n-gram speculative decoding at >1.8x speedup on code/JSON.
  - *Why:* Prompt-lookup n-gram speculation delivers instant 2x decoding speedups on repetitive structured tokens for free.

### Domain: Extrapolate feature vectors via single-layer transformer head and verify dynamic draft trees for >2.5x speedup. (1 tasks)
- **AGY-2494**: EAGLE-2 feature-level speculative head and dynamic draft tree verifier in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes EAGLE-2 feature-level speculative decoding at >2.5x speedup.
  - *Why:* EAGLE-2's contextual feature extrapolation achieves superior token acceptance rates, tripling generation speed at minimal memory cost.

### Domain: Factorize weights into 2 binary sign matrices with channel scales for >350 tok/s on CPU in 18.0GB RAM. (1 tasks)
- **AGY-2558**: DBQ double-binarized dual-POPCOUNT matrix engine in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes DBQ dual-POPCOUNT matrix operations at >350 tok/s on CPU.
  - *Why:* Double-Binarized Quantization enables 2-bit models to achieve high fidelity while executing on lightweight integer hardware.

### Domain: Federation (1 tasks)
- **T-022**: FED-CONSUME -- Light Up A2A/MCP Client Halves
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Loopback self-registration round-trips A2A `Message -> Task -> Artifact`; a second MiOS node on the LAN appears in `/v1/cluster/health` and contributes fan-out; a remote MCP server's tools appear in the council tool roster via `/v1/verbs/openai-tools`.

### Domain: Federation/Discovery (2 tasks)
- **T-229**: KACT-04 -- Gossip/DHT federated discovery transport (`mios_gossi
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Two nodes with no shared registry discover each other and exchange reputation entries purely over gossip.
- **T-978**: Real mDNS responder bound to the tethered interface, replacing the placeholder discovery module
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: The node resolves over the tether within seconds of attach, and the negative test fails if the responder ever answers on another interface.

### Domain: Fewer files, each doing more, all readable. (1 tasks)
- **AGY-1627**: Fold the 282 libexec verbs and 72 automation phases  (WS-THESIS | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: verb and phase counts are materially lower with no capability lost, each fold is covered by a test, and the legibility floors are tightened to the new measurement.
  - *Why:* the deliverable is a repository a person can read; 282 verbs is not readable regardless of how good each one is.

### Domain: Firstboot ordering is asserted, not assumed. (1 tasks)
- **AGY-1848**: Firstboot units have no ordering test  (WS-UNITS | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: an ordering change that would let enrolment gate boot fails a check.
  - *Why:* Law 12 is a boot-time property, and boot is the surface with the least test coverage.

### Domain: Foreground user requests take immediate precedence over background autonomous agent batches at the inference engine level. (1 tasks)
- **AGY-1937**: Pass per-request priority and enable priority scheduling on heavy inference lanes  (WS-SCHED | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Both heavy lane containers boot with engine priority flags enabled, and per-request priority headers are propagated from `agent-pipe` without error.
  - *Why:* Without engine-level priority, computed priority dies at the userspace semaphore gate and foreground turns get starved behind large background DAG batches.

### Domain: Format and configure multi-device Bcachefs pools with NVMe hot targets and HDD bulk storage tiers. (1 tasks)
- **AGY-2195**: Declarative Bcachefs multi-device storage tiering configurator in automation  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Bcachefs configurator provisions multi-device storage tiers with automated block promotion/demotion.
  - *Why:* In-kernel multi-device tiering delivers 5GB/s+ model weight loading speeds without wasting expensive NVMe capacity on cold backups.

### Domain: Fuse scale multiplication and zero-point offset subtraction directly into Tensor Core registers for >3.6x speedup. (1 tasks)
- **AGY-2466**: Fused asymmetric scale and zero-point register execution engine in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes fused asymmetric scale and zero-point register math with >3.6x speedup.
  - *Why:* Register-level asymmetric quantization fusion avoids VRAM round-trips while maximizing model accuracy.

### Domain: G-001 (1 tasks)
- **T-002**: no CI: every gate in this repo runs only when a human remembers
  - *Acceptance:* WHEN a commit is pushed THE SYSTEM SHALL run validate.sh and fail on a red gate

### Domain: Gates/Honesty (3 tasks)
- **T-1030**: HONEST-01 -- a skip, an empty match and a missing tool must all be RED; audit all 209 checks for the three vacuous shapes
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: no check can report success without proving it ran; each repaired gate's new findings are reported as blast radius before it is armed; a planted missing-tool condition fails every check that depends on that tool.
- **T-1037**: HOLLOW-01 -- 55 of 76 miosd Check impls are a constant Verdict::Pass with an empty body, and they run at every bake
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `miosd drift-check --root <nonexistent>` reports no check as PASS; every remaining stub is either implemented or removed from the registry rather than left reporting green; each implemented check has a paired negative fixture.
- **T-1043**: PIPENUM-01 -- check_pipeline_numbering reports PASS against a root that does not exist
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `miosd drift-check --root <nonexistent>` reports zero checks as PASS, and the remaining 20 ctx-reading checks are each audited for an empty-set path.

### Domain: Gates/Ratchets (1 tasks)
- **T-1046**: MERGERATCHET-01 -- the merge half was the SMALLER half. mios-gate ratchet-direction compared the WORKTREE against `git show HEAD:mios.toml`, and in a clean checkout those are byte-identical (`git show HEAD:...
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: merging a base branch that grew tooling Python does not trip the ratchet, while a commit on the branch that adds a single Python line still does -- both proved by planting; a ceiling raised in an earlier commit on the branch still FAILS (which it does not today); and the ceiling's recorded provenance names the base commit it was baselined against.

### Domain: Gateway/Ops (1 tasks)
- **T-083**: GWY-08 -- Hermes ➔ mios-gateway-agent Service Transition (Phase
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `hermes-agent.service` is masked and does not start at boot, `curl localhost:8642/health` returns ok from the new unit, all 10 smoke-test tool calls pass, agent-pipe dispatches reach `:8642` and get valid completions, OWUI chat works end to end, and `[gateway].enable = false` still leaves Hermes running on unupgraded installs.

### Domain: General (6 tasks)
- **T-005**: GOALS.md is double-tracked: goal.py writes root, scaffold and SKILL §3 say docs/
  - *Acceptance:* WHEN the goal artifact is written THE SYSTEM SHALL write exactly one path, the one SKILL §3 names
- **AGY-1596**: Give every GPU-gated service a CPU fallback lane so placement never refuses  (WS-BLADE | P1 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a GPU-gated unit started on a GPU-less blade serves `/v1/models` from the CPU lane; the caller's endpoint is unchanged; a drift-check asserts every `gpu-serving` requirement declares a fallback.
  - *Why:* without this, "migrate anywhere" is false for exactly the services that matter most, and the failure presents as a hang rather than a decision.
- **AGY-1597**: Implement local-first failover ordering with asymmetric anti-flap dwell  (WS-BLADE | P1 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: killing a service restarts it in place without a migration event; killing the machine migrates it; a link flapping faster than `recover_dwell_s` produces exactly one migration, not one per flap.
  - *Why:* most failures are a crashed process on a healthy machine where a restart is the whole fix; migrating first turns two seconds into a cold start and possibly a volume move.
- **AGY-1598**: Add origin-node id and logical timestamp to the pgvector schema  (WS-BLADE | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every row in the six tables carries origin + logical timestamp; existing rows are backfilled; a drift-check fails if `[blade.reconcile].enabled = true` while any of the six lacks the columns.
  - *Why:* enabling divergence without provenance produces a merge nobody can compute and silent data loss on rejoin.
- **AGY-1599**: Implement the per-class reconcile rules, with config_kv conflicts raised to the operator  (WS-BLADE | P2 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a simulated partition with writes on both sides reconciles losslessly for the first three classes; a divergent `config_kv` key blocks reconcile and names the conflicting keys; only then may `enabled` flip to true.
  - *Why:* the availability choice in ADR-0017 is only affordable if each data class has a fixed rule decided in advance; a vague rule is how this design fails.
- **AGY-1600**: Make "blade unreachable" legible instead of surfacing as a model error  (WS-BLADE | P1 | S)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: with the blade unreachable, the dashboard states "blade unreachable" and `/v1` returns a named error rather than a model failure; greenboot records the check without failing the boot.
  - *Why:* the seat's whole contract is that its front door is off-box, so the one failure it must explain clearly is the one where the box behind the door is gone.

### Domain: Generate CycloneDX and SPDX SBOM JSON manifests during export and attach Cosign attestations to OCI image refs. (1 tasks)
- **AGY-2309**: Automated Syft CycloneDX/SPDX SBOM generator and Cosign attestation attacher  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: SBOM generator outputs validated CycloneDX/SPDX manifests and Cosign signs the image attestations.
  - *Why:* Standardized, signed SBOMs provide complete supply-chain transparency and enable precise vulnerability matching.

### Domain: Generate K=5 candidate tokens via small draft model and verify concurrently in single target forward pass. (1 tasks)
- **AGY-2416**: Draft-model speculative decoding and parallel target verification engine in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes draft-model speculative decoding and achieves >2.0x speedup.
  - *Why:* Speculative drafting bypasses memory bandwidth bottlenecks, tripling 70B parameter model generation speeds.

### Domain: Generate bootable hybrid ISOs and iPXE netboot kernel/initrd bundles from the target OCI container image. (1 tasks)
- **AGY-2245**: Hybrid live ISO and iPXE netboot artifact synthesis pipeline using BIB  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: BIB pipeline exports bootable hybrid ISOs and iPXE netboot bundles automatically.
  - *Why:* Automated recovery media synthesis guarantees rapid disaster recovery and zero-touch bare-metal cluster expansion.

### Domain: Generate candidate token trees via Medusa heads and verify paths in a single Tree-Attention forward pass. (1 tasks)
- **AGY-2293**: Medusa / EAGLE multi-head token tree speculative engine and Tree-Attention kernels  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Medusa engine verifies token trees in single forward passes and achieves >2.5x generation speedup.
  - *Why:* Medusa Tree-Attention provides speculative decoding speedups without requiring extra VRAM for a draft model.

### Domain: Generate dynamic proxy routing configurations from mios.toml with Unix socket fast-paths and W3C trace propagation. (1 tasks)
- **AGY-2199**: Declarative Traefik / Envoy service mesh proxy generator and Unix socket router  (WS-NET | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Mesh generator creates declarative proxy routing rules and binds Unix sockets dynamically.
  - *Why:* Declarative service mesh provides high-performance Unix socket routing locally and encrypted mTLS across nodes.

### Domain: Generate least-privilege CDI JSON specifications mapping allocated GPU device nodes to rootless containers. (1 tasks)
- **AGY-2123**: Scoped CDI specification generator for NVIDIA/AMD/Intel rootless Podman containers  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CDI generator creates scoped GPU specifications for rootless containers automatically.
  - *Why:* Scoped CDI specifications prevent containerized AI processes from accessing unauthorized host devices.

### Domain: Generate randomized structural AST code mutations and fuzz Tree-Sitter semantic merge algorithms. (1 tasks)
- **AGY-2213**: Continuous differential AST git merge fuzzing harness and mutation generator  (WS-GIT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Differential merge fuzzer stress-tests AST merge algorithms and logs reproducible reproducers.
  - *Why:* Continuous merge fuzzing guarantees that automated agent code merges never introduce silent syntax corruptions.

### Domain: Git/DualRemote (1 tasks)
- **T-484**: Bi-Directional Dual-Remote Git Synchronization Daemon with Safe Divergence Gate
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Dual-remote sync daemon replicates commits across GitHub and Forgejo with safe conflict gating.

### Domain: Git/Sanitize (1 tasks)
- **T-483**: Pre-Push Secret Sanitization & Sensitive Token Detection Hook
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Pre-push hook scans all outgoing commits and blocks secret leakage reliably.

### Domain: Git/Transaction (1 tasks)
- **T-473**: Atomic Agent Git Transaction Coordinator with PostgreSQL Advisory Locking
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Agent git commit coordinator serializes concurrent commits deterministically without index collisions.

### Domain: Glob matching gives the same answer on both hosts. (1 tasks)
- **AGY-1854**: `fnmatch` is case-insensitive on Windows and case-sensitive on Linux  (WS-HOSTDEP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: path globbing behaves identically on both hosts.
  - *Why:* git is case-sensitive, so a case-insensitive match against tracked paths is wrong on both hosts -- it just only fails on one.

### Domain: Grammar-constrained tool calling is either used or removed, not maintained unused. (1 tasks)
- **AGY-2582**: Put the GBNF compiler on the dispatch hot path or retire it  (WS-ORCH | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A dispatch test proves the grammar reaches the lane request, or the module is gone and the decision is recorded.
  - *Why:* Unused compilers rot into false capability claims, and this one is already cited as shipped.

### Domain: Group E4M3/E5M2 values into 32-element blocks with E8M0 shared exponents for >2.8x speedup and 99.9% convergence. (1 tasks)
- **AGY-2546**: OCP MXFP8 microscaled tensor core engine and block exponent scaler in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference and training engine executes OCP MXFP8 microscaled Tensor Core kernels at >2.8x speedup.
  - *Why:* OCP standard MXFP8 microscaling enables high-density Tensor Core acceleration with wide dynamic range and zero gradient clipping.

### Domain: Guarantee 100% JSON schema compliance for structured tool calls using grammar-constrained generation. (1 tasks)
- **AGY-1964**: Structured output JSON schema compiler utilizing constrained decoding grammar engines  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Structured output requests enforce GBNF grammars at the inference layer with zero JSON parsing failures.
  - *Why:* Grammar-based token masking eliminates invalid JSON outputs and costly validation-retry cycles.

### Domain: Guarantee standard non-system UID 1000 assignment for primary user mios across installation, bootstrap, dev-VM provisioning, and container builds, eliminating ConditionUser=!@system overrides. (1 tasks)
- **AGY-2562**: Standard Non-System UID 1000 Enforcement & systemd-sysusers Migration Pipeline  (WS-USER | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: All user provisioning pathways deterministically assign UID 1000 to mios and systemd user session services start without @system override drop-ins.
  - *Why:* Systemd user session managers and desktop indexing services enforce ConditionUser=!@system; having UID >= 1000 is required by standard Linux FHS and freedesktop specifications.

### Domain: Handle netlink IP changes, update WireGuard peer endpoints in <50ms, and adapt MTU dynamically (1280-1420). (1 tasks)
- **AGY-2351**: Dynamic WireGuard endpoint roaming daemon and adaptive Path MTU prober in mios-mesh-roam  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Mesh roaming daemon preserves active connections across network handoffs and adapts MTU dynamically.
  - *Why:* Dynamic endpoint roaming ensures edge nodes and laptops maintain continuous cluster connectivity while traveling.

### Domain: Hardware/Alert (1 tasks)
- **T-532**: Automated network and audio fallback manager with operator desktop alert daemon
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Hardware fallback manager routes traffic to secondary devices and alerts operator automatically.

### Domain: Hardware/CDI (1 tasks)
- **T-525**: Scoped CDI specification generator for NVIDIA/AMD/Intel rootless Podman containers
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: CDI generator creates scoped GPU specifications for rootless containers automatically.

### Domain: Hardware/CDITest (1 tasks)
- **T-526**: Rootless container GPU device isolation and cgroup v2 eBPF device filter test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Automated test suite confirms cgroup v2 device filter blocks unauthorized GPU access.

### Domain: Hardware/Drivers (1 tasks)
- **T-471**: Unified Host GPU Driver Ingestion & MOK Pre-Compilation Pipeline
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Physical host GPU drivers load automatically on boot across all deployment shapes with verified MOK signatures.

### Domain: Hardware/Fallback (1 tasks)
- **T-531**: Peripheral hardware health evaluator and non-fatal Greenboot degradation reporter
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Greenboot hardware evaluator logs degraded peripherals gracefully without blocking system promotion.

### Domain: Hardware/Hotplug (1 tasks)
- **T-495**: Udev hotplug handler for dynamic Thunderbolt/USB4 eGPU and PCIe accelerator re-enumeration
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Udev rules detect hotplugged GPUs and trigger automated provisioning immediately.

### Domain: Hardware/IPKVM (1 tasks)
- **T-524**: Dedicated Out-of-Band IP-KVM management mesh and Redfish/PiKVM virtual media provisioner
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: IP-KVM manager controls hardware power and mounts virtual media over isolated management mesh.

### Domain: Hardware/NUMA (1 tasks)
- **T-519**: Multi-GPU PCIe/NVLink topology discovery and NUMA node affinity generator
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: NUMA affinity generator binds multi-GPU workers to optimal local CPU nodes automatically.

### Domain: Hardware/P2PTest (1 tasks)
- **T-520**: Automated inter-GPU P2P bandwidth and memory latency validation benchmark
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Benchmark suite confirms inter-GPU P2P transfer rates meet physical bus capacity.

### Domain: Hardware/TargetMatrix (1 tasks)
- **T-852**: Consumer PC, Laptop, NAS, and modern smartphone edge target matrix in mios-hardware-profile
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Hardware profiler classifies device tiers and configures AI inference profiles across all supported hardware.

### Domain: Hardware/TargetTest (1 tasks)
- **T-853**: Automated mobile and NAS mesh node enrollment, local inference profiling, and discovery test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates hardware profiling accuracy, dynamic memory bounds, and rapid mesh enrollment.

### Domain: Hardware/Thermal (1 tasks)
- **T-543**: Proactive PID thermal daemon and dynamic CPU/GPU power cap modulator
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Thermal daemon proactively modulates power caps and prevents silicon thermal throttling.

### Domain: Hardware/ThermalGuard (1 tasks)
- **T-850**: Proactive hardware thermal regulator and dynamic PWM fan curve controller in mios-thermal-guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Thermal guard regulates PWM fans and power caps in <500ms, sustaining peak computation.

### Domain: Hardware/ThermalTest (2 tasks)
- **T-544**: Continuous thermal stress and governor modulation recovery test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates thermal power cap modulation and automated frequency recovery.
- **T-851**: Automated sustained thermal load, fan curve modulation (<500ms), and power cap test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-500ms thermal response, proactive PWM fan modulation, and sustained clock stability.

### Domain: Hardware/VideoEnc (1 tasks)
- **T-535**: Multi-vendor hardware video encoder discovery and DMA-BUF capture bridge
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Video encoder probe detects hardware ASICs and binds zero-copy DMA-BUF streaming automatically.

### Domain: Hardware/VideoTest (1 tasks)
- **T-536**: Adaptive bitrate and low-latency frame encoding streaming benchmark suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Benchmark suite confirms adaptive bitrate encoding maintains target frame rates under network jitter.

### Domain: Harvest and condition entropy from CPU RDSEED, TPM 2.0 TRNG, and JitterEntropy to seed /dev/urandom early. (1 tasks)
- **AGY-2277**: Multi-source hardware TRNG conditioning daemon and early-boot entropy seeder in automation  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Entropy daemon harvests multiple hardware TRNG sources and seeds kernel entropy pools in early boot.
  - *Why:* Multi-source entropy conditioning prevents cryptographic key duplication and backdoor vulnerability in hardware RNGs.

### Domain: Harvested prose keeps its provenance across reorganisation. (1 tasks)
- **AGY-1684**: Give the manual a stable anchor scheme  (WS-MANUAL | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the scheme is documented, duplicate anchors fail a gate, and `landing` distinguishes moved from lost.
  - *Why:* the anchors are what make the prune step safe; ambiguity there makes deletion unverifiable.

### Domain: Hibernate idle microVMs by dumping RAM to disk in <20ms and restore state instantly in <10ms upon wakeup. (1 tasks)
- **AGY-2470**: Ephemeral microVM memory snapshot hibernator and instant RAM restorer in mios-microvm-snap  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Virtualization manager hibernates microVMs in <20ms and restores execution in <10ms.
  - *Why:* MicroVM snapshot hibernation enables thousands of paused subagent sandboxes to reside on a host with zero RAM waste.

### Domain: Hot-swap running agent-pipe daemon instances using systemd file descriptor passing with zero dropped connections. (1 tasks)
- **AGY-2140**: Zero-downtime systemd socket handoff (sd_listen_fds) daemon swapper for agent-pipe  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Socket swapper transitions active daemon instances with zero client connection drops.
  - *Why:* Zero-downtime socket handoff allows continuous autonomous self-development without operator disruption.

### Domain: Implement halfvec (FP16) quantization and partitioned HNSW indices in PostgreSQL pgvector for sub-5ms recall. (1 tasks)
- **AGY-2323**: Quantized halfvec HNSW vector indexer and workspace table partitioner in pgvector  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Pgvector schema applies halfvec HNSW indexing and partitions tables dynamically.
  - *Why:* Quantized HNSW indexing enables fast vector memory recall at scale while keeping PostgreSQL memory footprints lightweight.

### Domain: Implement native HTTPX async transport pooling with Unix domain socket support and stream decoding. (1 tasks)
- **AGY-2203**: Async HTTPX transport client pool and stream decoder in agent-pipe  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: HTTPX transport pool handles async web requests and local UDS container streams natively.
  - *Why:* Native HTTPX transports provide high-throughput async streaming, HTTP/2 multiplexing, and UDS fast-paths.

### Domain: Implement zero-polling reactive agent wakeups using Linux epoll, inotify, and PostgreSQL LISTEN/NOTIFY. (1 tasks)
- **AGY-2249**: Asyncio/epoll reactive event loop and PostgreSQL LISTEN/NOTIFY dispatcher in agent-pipe  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Reactive loop wakes subagents in <5ms on database and filesystem events with zero idle CPU overhead.
  - *Why:* Reactive event loops enable hundreds of concurrent agents to sleep efficiently without draining battery or CPU.

### Domain: Improve RAG relevance precision by scoring top-k vector candidates with a cross-encoder re-ranker. (1 tasks)
- **AGY-1971**: Vector similarity re-ranking using local cross-encoder model in RAG pipeline  (WS-RAG | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Re-ranker integration improves precision@5 retrieval benchmarks with sub-100ms added latency.
  - *Why:* Bi-encoder vector search alone fails to capture fine-grained semantic subtleties that cross-encoders resolve accurately.

### Domain: Index prompt prefixes in a Radix Tree to share KV blocks across subagents and achieve <5ms TTFT. (1 tasks)
- **AGY-2394**: Radix Tree prefix KV-cache sharing engine in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine shares KV blocks via Radix Tree and delivers sub-5ms TTFT on shared prefixes.
  - *Why:* Radix Tree prefix caching eliminates redundant GPU prefill computations across multi-agent swarms.

### Domain: Ingest and queue incoming webhooks securely with cryptographic signature verification and deduplication. (1 tasks)
- **AGY-2115**: HMAC-SHA256 authenticated webhook receiver and idempotent agent_inbox queue in agent-pipe  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Webhook receiver validates cryptographic signatures and queues events idempotently.
  - *Why:* Authenticated webhook ingestion allows autonomous event-driven triggers without opening unauthenticated attack surfaces.

### Domain: Install/Deploy/SSOT (1 tasks)
- **T-166**: DEPLOY-01 -- Install/first-boot reorder → eliminate "missing dep
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Every consumer step gates on its producer's real readiness with no fixed-timeout aborts and every producer is atomic, retried, idempotent and completeness-checked; a clean `podman-MiOS-DEV` reinstall brings up AI plane, forge and webtools with zero "missing dependency" failures; and the new drift-gate fails the build on any consumer-before-producer edge with `just drift-gate` and `test_mios_*` green.

### Domain: Instrument bounds checks with LFENCE/CSDB and array index masking to block Spectre v1 in <10ns with <1% overhead. (1 tasks)
- **AGY-2500**: Automated array bounds speculation barrier instrumenter and index masker in mios-spec-fence  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security instrumenter protects array bounds with LFENCE/CSDB and prevents Spectre v1 out-of-bounds reads.
  - *Why:* Targeted speculation barriers and index masking neutralize Spectre v1 memory leakage with near-zero CPU performance impact.

### Domain: Integrate Cockpit Storage UI with CephFS tiered storage pools and local encrypted partition health. (1 tasks)
- **AGY-2148**: Cockpit Storage integration module for CephFS tiered CRUSH pools and local encrypted volume monitoring  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Cockpit Storage module renders physical disk encryption and CephFS pool status in web console.
  - *Why:* A visual storage management console allows operators to monitor disk health and storage tiers intuitively.

### Domain: Interleave weight allocations across NUMA nodes via MPOL_INTERLEAVE and pin threads to local core sockets. (1 tasks)
- **AGY-2424**: Heterogeneous NUMA weight buffer interleaver and local core affinity pinner  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: NUMA allocator interleaves memory allocations and pins threads to local CPU core domains.
  - *Why:* NUMA memory interleaving doubles aggregate memory throughput for memory-bandwidth-bound CPU inference.

### Domain: Isolate autonomous subagent tool execution inside lightweight bubblewrap sandboxes. (1 tasks)
- **AGY-2149**: Ephemeral Bubblewrap subagent isolation engine with scoped bind-mounts in agent-pipe  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Bubblewrap sandbox restricts subagent filesystem mutations to designated workspace folders.
  - *Why:* Scoped sandboxing prevents misprompted or compromised subagents from modifying system files or parent directories.

### Domain: Isolate decrypted tokens in memory-locked, non-dumpable pages with compiler-barrier zeroization. (1 tasks)
- **AGY-2225**: Secure in-memory secret enclave runtime (mlock, MADV_DONTDUMP, explicit_bzero)  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Secret memory allocator pins memory, blocks core dump inclusion, and zeroes memory deterministically.
  - *Why:* Memory pinning and zeroization prevent credential harvesting from swap files and post-crash memory forensics.

### Domain: Isolate top 0.5% outlier weights in CSR sparse format and quantize remainder to 3-bit for 3.5x speedup. (1 tasks)
- **AGY-2534**: SpQR outlier isolation compiler and fused sparse-dense CUDA engine in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes SpQR fused sparse-dense CUDA kernels on GPU Tensor Cores at >3.5x speedup.
  - *Why:* SpQR preserves sensitive outlier weights in high-precision sparse formats, unlocking near-FP16 quality on 3-bit models.

### Domain: Issue hardware IBPB barriers via prctl when switching between security domains to clear BTB in <800ns. (1 tasks)
- **AGY-2496**: Dynamic IBPB indirect branch barrier manager and BTB sanitizer in mios-ibpb-guard  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security guard issues targeted IBPB barriers on security domain switches in <800ns.
  - *Why:* Targeted IBPB execution neutralizes Spectre v2 branch poisoning while preserving maximum CPU computing performance.

### Domain: Issue short-lived 24h X.509 SVID certificates to cluster services and rotate in-memory with zero downtime. (1 tasks)
- **AGY-2165**: SPIFFE/SPIRE workload identity agent and ephemeral 24h mTLS certificate rotator  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: SPIRE agent rotates ephemeral mTLS certificates automatically across cluster workloads.
  - *Why:* Ephemeral cryptographic identities eliminate long-lived credential theft risks in distributed agent meshes.

### Domain: Issue vzeroupper and AVX-512 register zeroing upon security domain switches to clear vector state in <50ns. (1 tasks)
- **AGY-2510**: Dynamic AVX/FPU register zeroization engine and GDS mitigation manager in mios-fpu-zero  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security sanitizer clears AVX-512 and FPU register state on domain switches in <50ns.
  - *Why:* Dynamic AVX register zeroization prevents Downfall/GDS speculative snooping from extracting secrets from CPU vector units.

### Domain: Kernel/FlightRecorder (1 tasks)
- **T-516**: In-kernel eBPF circular flight recorder ring and crash diagnostic parser
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: eBPF flight recorder logs rolling kernel states and crash parser reconstructs pre-panic events.

### Domain: Kernel/Kdump (1 tasks)
- **T-515**: Reserved memory kdump kernel deployment and automated zstd crash dump extractor
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Kdump captures compressed crash dumps to persistent storage and reboots safely on panics.

### Domain: Kernel/PstoreCrash (1 tasks)
- **T-790**: Persistent pstore ramoops kernel crash buffer manager and post-mortem extractor in mios-pstore
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Pstore ramoops preserves kernel panic backtraces across reboots and extracts them automatically.

### Domain: Kernel/PstoreTest (1 tasks)
- **T-791**: Automated kernel panic injection, ramoops log preservation, and database ingestion test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates ramoops log preservation, stack trace parsing, and database recording.

### Domain: Kernel/SysSync (1 tasks)
- **T-822**: Dynamic kernel sysctl/sysfs parameter synchronizer and udev reload daemon in mios-sys-sync
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: System synchronizer applies sysctl, sysfs, and udev rule updates on-the-fly in <50ms.

### Domain: Kernel/SysSyncTest (1 tasks)
- **T-823**: Automated zero-reboot sysctl parameter application (<50ms) and live udev test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates instant sysctl reload, live sysfs updates, and udev rule execution.

### Domain: Law 14 The whole-tree lexing pass runs in the native tier without creating a second definition of the corpus. (1 tasks)
- **AGY-1594**: Port the comment lexer hot path to Rust behind the unchanged mios-manual CLI  (WS-DOCGEN | P3 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the differential gate is green, the binary is optional (a bare checkout still works), and full-tree `mios-manual audit` runtime drops below 5s.
  - *Why:* Law 14 puts native tooling in Rust, but porting the classifier or the taggability rules would fork the corpus definition -- the lexer is the one piece that can move without that cost.

### Domain: Law 8 The generated resolvers carry VALUES, not documentation, and a unit's narrative has exactly one home. (1 tasks)
- **AGY-1591**: Stop projecting AI-hint prose into globals.{sh,ps1} and gate it  (WS-DOCGEN | P2 | M) **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: both resolvers shrink by ~1.1 MB combined, gate 157 is green, and appending one `MIOS_UNITS_TEST_COMMENT='# AI-hint: x'` line turns it red.
  - *Why:* one stale sentence about `hermes-agent.service` on `:8642` currently exists in four materially different file formats, and fixing the doc fixes none of the others.

### Domain: Legibility is the deliverable, so the doc programme is not tidying -- it is the artifact a reader receives. (1 tasks)
- **AGY-1604**: Close the documentation campaign  (WS-THESIS | P1 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: both ratchets read 0, `check_comment_landing` proves every pruned block still lands, and the generated manual builds from SSOT plus harvested prose alone.
  - *Why:* 1,724 narrative blocks are knowledge trapped where no reader will find it, and the repo is meant to be the thing that carries the idea.

### Domain: Lifecycle/Offline (1 tasks)
- **T-215**: WSL-02 -- bootc offline atomic upgrades (skopeo→oci→bootc switch
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: an air-gapped host upgrades from an OCI-on-USB image and a userspace-only update lands via soft-reboot without a full restart.

### Domain: Linux/Branding (1 tasks)
- **T-144**: WBRAND-02 -- Linux desktop palette parity via matugen  [P2]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: changing `[colors].accent` or `[branding].wallpaper` once reflows the Windows and Linux desktops -- including Flatpak apps -- to the same palette, verifiable by the theme drift-check rather than by eye.

### Domain: Lock cryptographic keys in physical RAM via mlock() and wipe buffers via explicit_bzero in <1us. (1 tasks)
- **AGY-2476**: Locked secure memory allocator and compiler-barrier zeroization runtime in libmios-sec  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security library allocates locked memory pages and sanitizes secret buffers via compiler barriers.
  - *Why:* Compiler-barrier memory zeroization and mlock guarantee cryptographic keys are never leaked to swap or memory dumps.

### Domain: Maintain an explicit ledger of open disagreements and objections throughout multi-agent deliberation rounds. (1 tasks)
- **AGY-1969**: Tension-tracking ledger in DCI deliberation to quantify unresolved objections  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Tension ledger tracks objections through to resolution and includes residual caveats in the final Decision Packet.
  - *Why:* Formal tension tracking prevents premature convergence where dominant agents ignore valid security challenges.

### Domain: Maintain optimal pgvector search recall and query performance under frequent embedding inserts. (1 tasks)
- **AGY-1999**: Automated VACUUM ANALYZE and HNSW vector index rebuilding timer in pgvector  (WS-DURA | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Automated index maintenance timer prevents vector performance degradation over time.
  - *Why:* HNSW vector indices degrade in search quality and latency without periodic maintenance under high mutation load.

### Domain: Manage KV blocks in 16-token chunks on AMD GPUs and compact memory asynchronously in dedicated HIP streams. (1 tasks)
- **AGY-2329**: ROCm / HIP PagedAttention virtual block manager and async stream compaction engine  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: ROCm inference lane allocates KV caches in 16-token virtual blocks with async stream compaction.
  - *Why:* HIP PagedAttention maximizes concurrent batch capacity on AMD GPUs and eliminates memory fragmentation.

### Domain: Manage KV-cache in 16/32-token virtual memory blocks and defragment VRAM pools asynchronously. (1 tasks)
- **AGY-2235**: PagedAttention virtual block memory manager and asynchronous KV defragmenter  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: PagedAttention block manager allocates and defragments KV memory dynamically with zero stall barriers.
  - *Why:* Virtual block paging eliminates VRAM waste from internal fragmentation and quadruples concurrent conversational capacity.

### Domain: Manage distributed Raft cluster consensus, leader election, and sub-3s PostgreSQL database failover. (1 tasks)
- **AGY-2219**: Embedded Raft consensus coordinator and Patroni HA database failover engine  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Raft coordinator elects cluster leaders and executes sub-3s database failover cleanly.
  - *Why:* Embedded Raft consensus eliminates single points of failure across multi-blade local clusters.

### Domain: Manage hardware IP-KVM devices and bare-metal provisioning over an isolated servicing mesh. (1 tasks)
- **AGY-2122**: Dedicated Out-of-Band IP-KVM management mesh and Redfish/PiKVM virtual media provisioner  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: IP-KVM manager controls hardware power and mounts virtual media over isolated management mesh.
  - *Why:* Out-of-Band IP-KVM management guarantees total remote bare-metal control even during OS crashes or BIOS configuration.

### Domain: Manage isolated git worktrees for subagents and prune merged branches and scratch directories automatically. (1 tasks)
- **AGY-2201**: Ephemeral subagent git worktree lifecycle manager and branch pruner in agent-pipe  (WS-GIT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Worktree manager provisions and cleans up subagent worktrees and topic branches deterministically.
  - *Why:* Isolated worktrees enable concurrent subagent operations without stepping on active developer files.

### Domain: Map GPU interconnect matrix and bind inference workers to local NUMA CPU nodes. (1 tasks)
- **AGY-2117**: Multi-GPU PCIe/NVLink topology discovery and NUMA node affinity generator  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: NUMA affinity generator binds multi-GPU workers to optimal local CPU nodes automatically.
  - *Why:* NUMA memory and PCIe affinity alignment maximizes tensor copy throughput and prevents cross-socket bus contention.

### Domain: Map modern open-weight models dynamically across hardware tiers (3B for entry consumer, 8B for average consumer, 32B for prosumer, 70B for poweruser). (1 tasks)
- **AGY-2169**: Hardware-tiered modern model matrix allocator for Consumer, Prosumer, and Poweruser nodes  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Tier allocator assigns modern open-weight models matching target node hardware capacity automatically.
  - *Why:* Hardware-tiered allocation ensures optimal inference speed and reasoning quality across diverse consumer and prosumer PCs.

### Domain: Memory/Filesystem (1 tasks)
- **T-177**: LSFS-01 -- Semantic-FS verbs + task-state protocol  [P3]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `lsfs_write` followed by `lsfs_search` round-trips a semantic query over the stored content; `lsfs_rollback` restores a prior version of an entry; task state survives an agent-pipe restart and is observable only through a tool call, with no auto-injected block in the assembled prompt.

### Domain: Memory/NUMAAlloc (1 tasks)
- **T-826**: Heterogeneous NUMA weight buffer interleaver and local core affinity pinner
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: NUMA allocator interleaves memory allocations and pins threads to local CPU core domains.

### Domain: Memory/NUMATest (1 tasks)
- **T-827**: Automated multi-socket NUMA bandwidth scaling (>400 GB/s) and core pinning test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates high aggregate NUMA memory bandwidth, even page distribution, and strict core pinning.

### Domain: Memory/OOMProtection (1 tasks)
- **T-820**: Proactive systemd-oomd PSI pressure manager and cgroup hierarchy protector
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Systemd-oomd evicts runaway worker cgroups under PSI pressure and preserves system stability.

### Domain: Memory/OOMTest (1 tasks)
- **T-821**: Automated memory exhaustion stress test, worker eviction, and daemon survival test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates targeted subagent eviction, zero system service degradation, and forensic audit logging.

### Domain: Memory/THPCompaction (1 tasks)
- **T-800**: Transparent Huge Pages (THP madvise) and proactive memory compaction manager
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Kernel allocates huge pages via madvise and defragments memory in the background asynchronously.

### Domain: Memory/THPTest (1 tasks)
- **T-801**: Automated 2MB/1GB huge page allocation, sub-1ms allocation latency, and TLB benchmark suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates instant huge page allocation, high coverage ratio, and low TLB miss rate.

### Domain: Meter real-time CPU/GPU energy consumption and dynamically enforce chassis wattage caps. (1 tasks)
- **AGY-2231**: Declarative RAPL / NVML hardware energy metering and chassis power cap manager  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Energy daemon meters power in real time and throttles accelerators to enforce power caps.
  - *Why:* Declarative power capping prevents electrical breaker trips and optimizes thermal efficiency on multi-accelerator nodes.

### Domain: MiOS runs as a WSL distribution with its declared units active. (1 tasks)
- **AGY-1920**: WSL units ship but the WSL host path is unproven  (WS-HOST | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a documented command produces a working WSL distribution running the declared units.
  - *Why:* WSL is one of the declared deployment formats and is currently declared rather than demonstrated.

### Domain: Migrate activation outliers into weights via alpha=0.5 scaling and execute fused W8A8 INT8 Tensor Core GEMM. (1 tasks)
- **AGY-2430**: SmoothQuant W8A8 activation-weight smoothing engine and fused INT8 Tensor Core dispatcher  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes SmoothQuant W8A8 via fused INT8 Tensor Core kernels with <0.02 perplexity loss.
  - *Why:* SmoothQuant enables true INT8 matrix computation on GPU Tensor Cores without outlier accuracy collapse.

### Domain: Migrate active Wayland desktop sessions and application states seamlessly across cluster blades. (1 tasks)
- **AGY-2158**: Dynamic cross-node Wayland session checkpoint and migration protocol  (WS-USER | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Session migration protocol transfers active desktop sessions across cluster nodes cleanly.
  - *Why:* Cross-node session migration provides continuous, ubiquitous desktop access across physical towers and remote thin clients.

### Domain: Mint 60s single-use Macaroons with attenuated permission caveats and burn nonces upon tool execution. (1 tasks)
- **AGY-2321**: Ephemeral HMAC Macaroon minter and attenuated caveat verifier in agent-pipe  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Macaroon minter issues time-bound attenuated tokens and gateway enforces single-use verification.
  - *Why:* Attenuated Macaroons prevent compromised or hallucinated subagents from abusing elevated credentials.

### Domain: Modulate chassis and GPU fans smoothly across multi-zone PID curves with 5°C hysteresis to eliminate acoustic pulsing. (1 tasks)
- **AGY-2221**: Multi-zone hysteresis PID fan curve controller and hwmon sensor mapper in mios-fand  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Fan daemon regulates multi-zone fan RPMs smoothly with hysteresis and acoustic damping.
  - *Why:* Smooth multi-zone fan control ensures silent idle operation and effective cooling during sustained AI training.

### Domain: Monitor CPU/GPU temperatures and dynamically modulate EPP (performance -> balance_power) with 10°C hysteresis. (1 tasks)
- **AGY-2319**: Proactive PID thermal frequency governor and dynamic EPP stepping daemon in mios-thermald  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Thermal governor modulates EPP dynamically with 10°C hysteresis to prevent thermal cliff drops.
  - *Why:* Proactive frequency stepping prevents thermal throttling cliffs and emergency motherboard power cuts.

### Domain: Monitor drive wear counters via smartd and trigger proactive CephFS OSD drain before hardware failure. (1 tasks)
- **AGY-2237**: Predictive S.M.A.R.T. drive health monitor and automated CephFS evacuation manager  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Drive health monitor catches degraded wear indicators and evacuates data proactively.
  - *Why:* Predictive drive failure detection and proactive migration eliminate data loss risks on high-write AI workloads.

### Domain: Monitor hardware topology changes via udev netlink sockets and maintain live inventory in PostgreSQL. (1 tasks)
- **AGY-2161**: In-kernel udev netlink hardware change monitor and PostgreSQL hardware_inventory recorder  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Hardware monitor logs device state transitions and maintains PostgreSQL inventory in real time.
  - *Why:* Real-time hardware inventory tracking allows immediate cluster scheduling adaptation when accelerators change.

### Domain: Mount immutable /usr using Composefs and fs-verity block-level signature verification. (1 tasks)
- **AGY-2125**: Composefs fs-verity root filesystem sealing and atomic image descriptor validator  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Composefs seals the root filesystem and fs-verity blocks runtime binary modifications.
  - *Why:* Cryptographic composefs sealing guarantees that system binaries cannot be tampered with while running.

### Domain: Naming (1 tasks)
- **T-237**: NAME2-02 -- Rename `mios-daemon-agent` agent-id → `daemon-agent`
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: No `mios-daemon-agent` string remains in the tree, the drift-check is green, and a live fan-out still resolves and dispatches to the agent under its new id.

### Domain: Naming/Addressing (1 tasks)
- **T-324**: ADDR-05 -- Retired ports live on in shipped units and Quadlets; the sweep only scans docs
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the retired-port sweep covers `usr/lib/systemd/system/**` and `usr/share/containers/systemd/**`; the six non-comment sites are resolved or justified; the host-vs-container-internal ambiguity on `8432` is settled in the SSOT rather than in a unit comment; comment-only occurrences are either rewritten to port KEYS or registered as shrink-only debt.

### Domain: Naming/Hygiene (1 tasks)
- **T-238**: NAME2-03 -- Mutable-state casing pass + `ContainerName=` audit
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Every module-level global that is genuinely MUTATED at runtime (caches, registries, pools) is `_lower_snake`; every `ContainerName=` equals its unit name (or, for a template unit, the instantiated `<base>-%i` form); and the drift-check is green. REVISED: the original wording -- "every module-level *mutable* global" -- was measured and does not survive contact. 406 module-level UPPER_SNAKE names are reassigned at runtime via a `global` statement, but the large majority are dependency-INJECTED configuration constants set once by `configure()` (`REFINE_MODEL`, `WEB_RESEARCH_ENABLED`, `KNOWLEDGE_RECALL_K`...). UPPER_SNAKE is correct for those; renaming them would obscure that they are config, and would break every `configure()` call site, `server.py`'s verbatim re-imports (the surface-parity gate) and the AI-hint headers. The rule that actually serves the goal is mutated-at-runtime vs set-once-at-wiring, not the literal word "mutable".

### Domain: Negotiate Landlock ABI at runtime and enforce unprivileged filesystem and TCP port filtering in <1us. (1 tasks)
- **AGY-2504**: Dynamic Landlock ABI v1..v4 ruleset negotiator and network port enforcer in mios-exec-sandbox  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Sandbox negotiator enforces filesystem and network rulesets dynamically across all Landlock ABI versions.
  - *Why:* Dynamic Landlock ABI versioning provides robust, unprivileged in-kernel security sandboxing across all kernel releases.

### Domain: Network/Android (1 tasks)
- **T-976**: USB CDC-NCM gadget orchestration, host link bring-up, and the edge.android_tether SSOT table
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Attach yields the SSOT-declared address on the tether interface; an RNDIS-only handset produces a degraded report; no IP, interface name or product ID is a literal in the script.

### Domain: Network/DNS (1 tasks)
- **T-497**: systemd-resolved to mios-adguard split-horizon DNS routing configurator
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: System DNS resolves internal mesh hostnames and external DoH queries seamlessly through AdGuard Home.

### Domain: Network/DNSTest (1 tasks)
- **T-498**: DNS-over-HTTPS leak prevention and encrypted query test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Automated test suite confirms zero DNS leaks across system and container network interfaces.

### Domain: Network/Firewall (1 tasks)
- **T-479**: Declarative nftables inter-container firewall rule generator
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Nftables generator applies least-privilege inter-container routing rules automatically on startup.

### Domain: Network/MobileSync (1 tasks)
- **T-854**: Mobile edge node A2A proxy and adaptive task offloader in mios-mobile-sync
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Mobile sync daemon coordinates smartphone nodes and offloads complex reasoning seamlessly.

### Domain: Network/MobileTest (1 tasks)
- **T-855**: Automated mobile peer discovery, adaptive prompt routing (<50ms), and memory sync test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates instant mobile offload routing, home cluster execution, and bidirectional vector synchronization.

### Domain: Network/WoL (1 tasks)
- **T-523**: Signed Proxy WoL with SecureON payload and peer wake daemon
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Proxy WoL daemon wakes sleeping blades securely on incoming workload dispatch.

### Domain: Network/XDPFastpath (1 tasks)
- **T-802**: Native eBPF XDP network fastpath and WireGuard packet router in mios-xdp
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: XDP eBPF driver programs route packets and drop flood traffic at hardware line rate.

### Domain: Network/XDPTest (1 tasks)
- **T-803**: Automated 10M pps packet routing throughput, sub-microsecond XDP latency, and DDoS test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates line-rate packet processing, sub-microsecond latency, and wire-speed flood filtering.

### Domain: Network/mDNSDiscovery (1 tasks)
- **T-816**: Declarative Avahi mDNS service publisher and ZeroConf peer resolver in mios-mdns
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Avahi publishes local services and discovers peer endpoints over mDNS in <200ms.

### Domain: Network/mDNSTest (1 tasks)
- **T-817**: Automated local mDNS service advertising, sub-200ms peer discovery, and offline test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates ZeroConf service publication, TXT record parsing, and rapid peer resolution.

### Domain: No check remains in the unknown bucket. (1 tasks)
- **AGY-1814**: Resolve the 66 gates the falsifiability audit left inconclusive  (WS-GATE | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: all 66 have a verdict and every hollow one has been repaired or has an open task id.
  - *Why:* an audit that ends with a third of its subjects unresolved has not measured what it claims.

### Domain: No check reports success for work it did not do. (1 tasks)
- **AGY-1728**: Find every gate that skips where it should fail  (WS-PROCESS | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every prerequisite-absent path either fails under REQUIRE_TOOLS or has its prerequisite provisioned, and the list is written down.
  - *Why:* this is the repository's most expensive recurring defect, and it just cost eighteen files of undetected drift between the two published repositories.

### Domain: No crate ships asserting nothing. (1 tasks)
- **AGY-1801**: Cover the ten remaining untested native crates, hardest-consequence first  (WS-LANG | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `[rust].max_untested_crates` has reached zero, or every remaining entry states a reason that is structural rather than pending.
  - *Why:* eleven crates and roughly 5,600 lines currently pass `cargo test` unconditionally, which is most of what the Rust layer's green means today.

### Domain: No file exists in the image that the thesis does not account for. (1 tasks)
- **AGY-1910**: Every file in the image must be generated-and-gated or declared authored  (WS-PROJ | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the unclassified set is empty and a new unclassified file fails a check.
  - *Why:* the surfaces nobody has classified are exactly where hand-maintained configuration survives.

### Domain: No gate passes because it found nothing to look at. (1 tasks)
- **AGY-1619**: Audit every check for vacuous pass conditions  (WS-EVIDENCE | P0 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every check has a documented empty-input behaviour, and `check_negative_coverage` requires a negative test for each.
  - *Why:* this is the repository's most expensive recurring defect: a check that cannot fail also stops anyone looking.

### Domain: No live code path references a retired backend. (1 tasks)
- **AGY-1916**: The AI plane is /v1-only but legacy tokens survive in live paths  (WS-AI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every surviving reference is classified and no live path reaches a retired backend.
  - *Why:* a retired lane that is still reachable is a service that answers when it should not exist.

### Domain: No open task can be called done without a command that proves it. (1 tasks)
- **AGY-1724**: Ratchet the AGY task schema downward from 1607 until every OPEN task is falsifiable  (WS-PROCESS | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `[tasks].schema_from` is 1 and every OPEN task carries all eight fields.
  - *Why:* the task list is the plan; a task with no falsifiable Verify is an opinion about what to do next.

### Domain: No other generator can repeat the bib-configs defect. (1 tasks)
- **AGY-1821**: A generator's --check mode must compare what its write mode produces  (WS-GATE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every `--check` implementation derives its comparison from the same rendering its writer uses.
  - *Why:* a check that does not compare what the writer produces cannot detect the drift the writer creates.

### Domain: No secret is ever committed, logged, or baked. (1 tasks)
- **AGY-1652**: Make secret handling provable end to end  (WS-SECURITY | P0 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the gate has a negative test that plants a credential shape and fails, image layers are scanned, and every legitimate fixture is allowlisted with a reason.
  - *Why:* a credential in a committed layer is permanent regardless of what a later commit does.

### Domain: Node/Attestation (1 tasks)
- **T-530**: Automated RFC 9334 RATS remote TPM 2.0 quote verifier and zero-touch cluster onboarding daemon
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Attestation daemon authenticates pre-enrolled blades and provisions cluster mesh access automatically.

### Domain: Node/PreEnroll (1 tasks)
- **T-529**: Declarative SSOT blade pre-enrollment registry and TPM EK fingerprint parser
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: SSOT parser registers declared hardware blades with valid TPM EK fingerprints.

### Domain: Notify GNOME and mios-wallpaperd of theme updates in real time via DBus and Unix domain sockets. (1 tasks)
- **AGY-2098**: Real-time DBus and WebGL wallpaper theme synchronization bus  (WS-LANG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Theme broadcast bus synchronizes GNOME settings and living wallpaper shaders in real time.
  - *Why:* Real-time shader and desktop theme synchronization delivers a responsive, living desktop environment.

### Domain: One boot menu, generated, with no dead twin. (1 tasks)
- **AGY-1756**: Collapse the two hand-maintained boot menus into one generator  (WS-DEPLOY | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: one source produces the menu and no unreferenced menu template remains.
  - *Why:* whichever of the two a maintainer edits, there is a coin-flip chance it is the one nothing reads.

### Domain: One declaration decides whether a unit is enabled. (1 tasks)
- **AGY-1837**: Enablement is declared in two places for some units  (WS-UNITS | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: changing enablement in one place without the other fails a check.
  - *Why:* two sources for one fact is the condition the SSOT thesis exists to remove.

### Domain: One definition of "the files in this tree". (1 tasks)
- **AGY-1855**: `git ls-files` and `os.walk` disagree and both are used  (WS-HOSTDEP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each enumeration states which definition it uses and why.
  - *Why:* a ratchet that counts differently depending on what is lying around the working directory is not a measurement.

### Domain: One key per value across the namespace. (1 tasks)
- **AGY-1872**: 79 version-duplicate pairs remain in the key namespace  (WS-SSOT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the duplicate-pair count reaches zero.
  - *Why:* duplicate keys are how two consumers end up configured differently while appearing to read the same setting.

### Domain: One resolver answers every SSOT question. (1 tasks)
- **AGY-1873**: The SSOT resolver has two implementations that can disagree  (WS-SSOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a divergence in any resolver's answer for any key fails.
  - *Why:* the SSOT is only single if every reader reads it the same way.

### Domain: One statement of the product line, read everywhere it is mentioned. (1 tasks)
- **AGY-1739**: Project the variant registry into the surfaces that name variants  (WS-VARIANT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every surface that lists variants derives that list, and hand-editing one is caught.
  - *Why:* the registry only settles the naming question if the places people read are the places it reaches.

### Domain: One version value, derived everywhere. (1 tasks)
- **AGY-1871**: Version is declared in three places at conflicting values  (WS-SSOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every version string in the tree and the image derives from one key.
  - *Why:* version disagreement makes provenance claims unverifiable.

### Domain: Optimize PostgreSQL table maintenance with tuned autovacuum, nightly pg_cron schedules, and concurrent HNSW reindexing. (1 tasks)
- **AGY-2207**: Declarative PostgreSQL autovacuum tuner, pg_cron scheduler, and concurrent HNSW reindexer  (WS-RAG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: PostgreSQL maintenance daemon vacuums tables and reindexes HNSW indices with zero service downtime.
  - *Why:* Continuous non-blocking maintenance preserves sub-10ms vector search latency and prevents database disk bloat.

### Domain: Optimize learnable clipping bounds and transformation matrices in <15min to run 3-bit models with >99.4% accuracy. (1 tasks)
- **AGY-2490**: OmniQuant learnable clipping and equivalent transformation optimizer in mios-quantize-omniquant  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: OmniQuant optimizer compiles 3-bit models in <15min and inference engine executes fused Tensor Core kernels.
  - *Why:* OmniQuant's learnable equivalent transforms eliminate quantization distortion, unlocking high-accuracy 3-bit models.

### Domain: Orchestrate multi-seat hardware assignment dynamically for roaming users across any cluster blade. (1 tasks)
- **AGY-2157**: Network-wide roaming multi-seat session orchestrator and GPU assignment manager  (WS-USER | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Seat router assigns GPUs and manages multi-user physical/remote desktop sessions network-wide.
  - *Why:* Dynamic multi-seat allows arbitrary users to roam across cluster blades and utilize available GPU hardware seamlessly.

### Domain: Orchestrate smartphone edge nodes running local models and adaptively offload heavy reasoning to cluster blades. (1 tasks)
- **AGY-2452**: Mobile edge node A2A proxy and adaptive task offloader in mios-mobile-sync  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Mobile sync daemon coordinates smartphone nodes and offloads complex reasoning seamlessly.
  - *Why:* Mobile edge coordination brings the full power of the MiOS multi-blade cluster to personal smartphones securely.

### Domain: Orchestration (1 tasks)
- **T-029**: ORCH-02 -- DCI-CF Convergent Flow Critic (4-Persona Loop)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A conflicted deliberation produces a decision packet containing `minority_report`, routine queries bypass DCI-CF with no added latency, and `SELECT * FROM event WHERE kind='dissent'` returns rows.

### Domain: Pack 4 ternary weights per byte and dispatch fused CUDA kernels to run 70B models at >3.8x speedup in 14GB VRAM. (1 tasks)
- **AGY-2526**: TriLM fused 1.58-bit ternary GPU kernel and warp-specialized accumulator in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes TriLM fused 1.58-bit ternary CUDA kernels on GPU Tensor Cores at >3.8x speedup.
  - *Why:* TriLM GPU kernels enable 70B parameter reasoning models to fit entirely within consumer 16GB GPUs at breakthrough speeds.

### Domain: Pack E2M1 FP4 weights into 32-element blocks with E8M0 shared scales and dispatch FP4 Tensor Cores for >4.5x speedup. (1 tasks)
- **AGY-2512**: NVFP4 / MXFP4 block-scaled (E2M1 + E8M0) tensor core pipeline in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes NVFP4/MXFP4 block-scaled Tensor Core kernels at >4.5x speedup.
  - *Why:* Microscaled FP4 floating-point representations enable maximum Tensor Core math density with near-lossless numerical fidelity.

### Domain: Packaging/WSL (1 tasks)
- **T-214**: WSL-01 -- Dual-personality `rootfs-export → wsl --import` pipeli
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `wsl --import` of the exported rootfs yields a working MiOS distro, and the MiOS updater moves an already-installed WSL distro to a newer image with bootc absent.

### Domain: Pair heavy models with lightweight draft models and adapt draft lengths dynamically for 3x token speedups. (1 tasks)
- **AGY-2253**: Dynamic speculative decoding draft pairing and adaptive draft-length manager in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Speculative decoding engine pairs draft models and accelerates token generation throughput.
  - *Why:* Speculative decoding delivers 3x faster local LLM generation without degrading output accuracy.

### Domain: Parse code patches into Tree-Sitter ASTs, compute semantic structural diffs, and gate merges with 2 peer reviews. (1 tasks)
- **AGY-2378**: Tree-Sitter AST structural diff engine and 2-peer review gate in agent-pipe  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Agent pipeline parses Tree-Sitter ASTs and enforces 2-peer review gating on structural diffs.
  - *Why:* AST structural diffing eliminates whitespace noise and focuses peer review on genuine logic and type mutations.

### Domain: Partition physical drives with hardware-level OPAL SED or LUKS2 encryption sealed to TPM 2.0. (1 tasks)
- **AGY-2147**: Hardware OPAL 2.0 SED / LUKS2 automated disk partitioning and TPM enrollment  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Disk partitioner provisions hardware OPAL SED / LUKS2 encryption on all physical drives automatically.
  - *Why:* Hardware-level disk encryption guarantees data security at rest against physical drive theft.

### Domain: Pin core system invariants and compact intermediate conversation turns into semantic summaries at context limits. (1 tasks)
- **AGY-2273**: Hierarchical semantic context compactor and invariant pinning manager in agent-pipe  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Context compactor compresses long-horizon conversation histories while preserving system invariants.
  - *Why:* Semantic compaction enables multi-day agent coding sessions to proceed indefinitely without hitting hard context limits.

### Domain: Pin first 4 tokens as attention sinks and maintain rolling 32k KV window for perpetual streaming. (1 tasks)
- **AGY-2353**: StreamingLLM attention sink pinner and rolling KV eviction manager in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine maintains attention sinks and slides rolling KV window perpetually.
  - *Why:* StreamingLLM allows autonomous agents to stream millions of tokens continuously without context window overflow crashes.

### Domain: Poll hwmon/NVML sensors every 500ms and modulate PWM fans and power caps to prevent thermal clock throttling. (1 tasks)
- **AGY-2448**: Proactive hardware thermal regulator and dynamic PWM fan curve controller in mios-thermal-guard  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Thermal guard regulates PWM fans and power caps in <500ms, sustaining peak computation.
  - *Why:* Proactive thermal regulation prevents sudden performance degradation during heavy agent inference runs.

### Domain: Poll temperatures and modulate CPU/GPU power caps proactively before thermal throttling occurs. (1 tasks)
- **AGY-2141**: Proactive PID thermal daemon and dynamic CPU/GPU power cap modulator  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Thermal daemon proactively modulates power caps and prevents silicon thermal throttling.
  - *Why:* Proactive thermal regulation maintains stable inference token throughput and prevents hardware degradation.

### Domain: Pre-pull and unpack Quadlet container images into /var/lib/containers/storage during build time. (1 tasks)
- **AGY-2347**: Build-time Quadlet container image pre-warmer and zstd chunked layer optimizer  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Build pipeline bakes pre-warmed, zstd-compressed Quadlet layers directly into container storage.
  - *Why:* Build-time container pre-warming enables instant offline Day-0 boot and eliminates first-run download delays.

### Domain: Preserve critical system prompts and relevant conversational turns during automated context compression. (1 tasks)
- **AGY-1960**: Adaptive context window truncation with needle-in-a-haystack retention heuristics  (WS-AI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Context trimmer maintains long-running conversations within model token ceilings without losing system instructions.
  - *Why:* Long-running autonomous agent sessions will fail if context windows are exceeded or improperly pruned.

### Domain: Prevent GPU Out-Of-Memory (OOM) crashes by monitoring VRAM allocation and evicting stale KV slots. (1 tasks)
- **AGY-1968**: Per-lane VRAM watermark monitor and emergency KV-cache eviction daemon  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: VRAM watchdog prevents GPU allocation panics by maintaining a 5% safety margin on GPU memory pools.
  - *Why:* Uncontrolled KV cache growth under multi-agent load will trigger kernel GPU panics and drop entire inference lanes.

### Domain: Prevent accidental git pushes of private keys, passwords, or personal access tokens. (1 tasks)
- **AGY-2081**: Pre-Push Secret Sanitization & Sensitive Token Detection Hook  (WS-GIT | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Pre-push hook scans all outgoing commits and blocks secret leakage reliably.
  - *Why:* Leaked credentials in public git repositories cause severe security breaches and invalidate sovereignty.

### Domain: Prevent any single user or agent workspace from exhausting shared distributed CephFS storage. (1 tasks)
- **AGY-2001**: CephFS dynamic quota enforcement per tenant subvolume  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CephFS directory quotas enforce disk boundaries per tenant automatically.
  - *Why:* Multi-tenant storage pools require strict quota enforcement to ensure fair capacity distribution.

### Domain: Prevent edge compute workloads from starving host OS system tasks. (1 tasks)
- **AGY-1988**: Dynamic CPU core pinning and cgroup limits for mios-node worker threads  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Worker processes obey cgroup resource limits and CPU affinity masks strictly.
  - *Why:* Edge nodes must maintain interactive responsiveness and stability while processing compute tasks.

### Domain: Prevent git index.lock collisions by coordinating concurrent agent commits through PostgreSQL advisory locks. (1 tasks)
- **AGY-2071**: Atomic Agent Git Transaction Coordinator with PostgreSQL Advisory Locking  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Agent git commit coordinator serializes concurrent commits deterministically without index collisions.
  - *Why:* Concurrent agent commits without locking corrupt working tree states and abort transactions.

### Domain: Prevent hung MCP tools from blocking agent execution threads indefinitely. (1 tasks)
- **AGY-1962**: Tool-call latency profiling and dead-lock watchdog timeout in agent-pipe tool loop  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Tool invocations enforce timeouts strictly and record latency metrics for performance profiling.
  - *Why:* Unresponsive external tools or network calls can lock worker processes and degrade total system responsiveness.

### Domain: Prevent leaking sensitive internal paths, private keys, and user tokens to external search engines. (1 tasks)
- **AGY-2073**: Pre-Search Query Sanitization & Secret Scrubbing Filter in agent-pipe  (WS-AI | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Pre-search filter scrubs sensitive tokens from outgoing search queries reliably.
  - *Why:* Autonomous agents frequently reference code containing secrets; un-scrubbed web searches leak private credentials.

### Domain: Prevent multi-tenant agent starvation by enforcing token-bucket rate limits and burst capacities. (1 tasks)
- **AGY-1957**: Dynamic token-bucket rate limiter and per-tenant burst quotas in agent-pipe  (WS-SCHED | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Rate limiter enforces token quotas per tenant and returns standard 429 responses under burst load.
  - *Why:* Unchecked autonomous agents can exhaust inference lane bandwidth and starve user-interactive sessions.

### Domain: Prevent system OOM kills by spilling large in-memory `/tmp` files to fast NVMe swap storage. (1 tasks)
- **AGY-2008**: Automated tmpfs spill-to-NVMe manager under memory pressure conditions  (WS-STRG | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Tmpfs spill manager prevents out-of-memory lockups during large parallel compilation jobs.
  - *Why:* Large build jobs can quickly exhaust RAM tmpfs on edge devices with limited physical memory.

### Domain: Prioritize interactive voice/chat streams on high-priority GPU compute queues and preempt background training tasks. (1 tasks)
- **AGY-2229**: CUDA/ROCm compute stream priority scheduler and background preemption manager  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: GPU scheduler preempts low-priority kernels and executes interactive voice turns in <50ms.
  - *Why:* Compute stream preemption guarantees crisp conversational voice response times without stopping background AI training.

### Domain: Probe CPU architecture dynamically; enable ARM64 MTE, x86_64 Shadow Stack/CET, or software fallback in <1us. (1 tasks)
- **AGY-2548**: Universal hardware-agnostic memory safety and tagging negotiator in mios-mem-tag-guard  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security runtime dynamically negotiates hardware memory tagging across ARM64, x86_64, and fallback architectures.
  - *Why:* Universal hardware memory tagging provides state-of-the-art memory safety across every supported CPU vendor architecture.

### Domain: Probe hardware video encoders (QuickSync/NVENC/AMF) and capture desktop frames via zero-copy DMA-BUF. (1 tasks)
- **AGY-2133**: Multi-vendor hardware video encoder discovery and DMA-BUF capture bridge  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Video encoder probe detects hardware ASICs and binds zero-copy DMA-BUF streaming automatically.
  - *Why:* Hardware video encoding provides 4K60 desktop streaming with minimal CPU utilization and sub-10ms frame encoding latency.

### Domain: Process concurrent voice audio and vision frames over duplex WebSockets without blocking voice synthesis. (1 tasks)
- **AGY-2269**: Duplex multi-modal WebSocket streaming pipeline (audio, vision, TTS, tools) in agent-pipe  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Multi-modal WebSocket pipeline streams concurrent audio, vision, and tool results fluidly.
  - *Why:* Duplex multi-modal streaming delivers natural real-time conversational agent experiences while understanding desktop context.

### Domain: Profile layer sensitivity via Hessian diagonal and allocate 8-bit to outer layers and 2/3-bit to middle layers. (1 tasks)
- **AGY-2464**: Automated mixed-bit layer slicing compiler and sensitivity profiler in mios-quantize-hybrid  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Hybrid quantization compiler produces mixed-bit models with 68% compression and <0.02 perplexity loss.
  - *Why:* Layer-specific mixed-bit quantization preserves reasoning fidelity while maximizing model weight compression.

### Domain: Promote staged UKIs to default only after Greenboot verifies hardware boot success. (1 tasks)
- **AGY-2106**: Automated UKI A/B boot promotion and Greenboot validation gate  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Greenboot gate automatically promotes verified staged UKI binaries to default boot entries.
  - *Why:* Automated promotion guarantees that unverified kernel parameter modifications do not persist across crashes.

### Domain: Protect top 1% salient weight channels via optimal per-channel scales and execute fused W4A16 Tensor Core GEMM. (1 tasks)
- **AGY-2442**: Activation-Aware Weight Quantization (AWQ) engine and fused W4A16 dispatcher in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine loads AWQ models and executes fused W4A16 Tensor Core kernels with >3.5x speedup.
  - *Why:* AWQ protects critical outlier channels to deliver 4-bit memory footprints with zero coding intelligence loss.

### Domain: Provide durable, automated, compressed backups of the entire PostgreSQL+pgvector datastore to prevent state loss across upgrades. (1 tasks)
- **AGY-1949**: Automated PostgreSQL+pgvector backup service with zstd snapshot rotation  (WS-DURA | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Daily automated database backups execute via systemd timer and older snapshots are rotated according to retention policy.
  - *Why:* Immutable OS upgrades must never risk data loss in the mutable `/var` agent datastore; durable automated backups are essential for disaster recovery.

### Domain: Provide high-speed S3 object storage APIs for distributed model weight distribution across cluster blades. (1 tasks)
- **AGY-2002**: S3-compatible object storage gateway (radosgw) sidecar for bulk model distribution  (WS-STRG | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: RADOS S3 gateway serves bulk model blobs to worker nodes with high parallel read bandwidth.
  - *Why:* Object storage protocols allow efficient chunked streaming of massive model weights across cluster nodes.

### Domain: Provide instant database failover capability by streaming WAL logs to a standby PostgreSQL replica. (1 tasks)
- **AGY-2004**: Hot-standby PostgreSQL replica provisioning over local cluster nodes  (WS-DURA | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Streaming replication keeps standby database in sync with sub-50ms replication lag.
  - *Why:* High-availability cluster blades must survive sudden hardware failure without losing recent agent memory.

### Domain: Provide instant, zero-dependency validation of `mios.toml` syntax and schema constraints. (1 tasks)
- **AGY-1996**: Rust implementation of SSOT mios.toml validation and type checker  (WS-LANG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `mios-check` validates the complete SSOT file with rich terminal error formatting and instant execution.
  - *Why:* Pre-commit and build-time schema validation must be instantaneous to provide fast feedback to developers.

### Domain: Provide low-overhead eBPF tracing probes (biosnoop, tcpretrans, execsnoop) and record traces in PostgreSQL. (1 tasks)
- **AGY-2317**: Declarative eBPF kernel tracing suite and bpftrace histogram recorder in mios-trace  (WS-DIAG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Tracing tool attaches eBPF kprobes dynamically and records structured latency histograms.
  - *Why:* Non-invasive eBPF tracing enables autonomous agents to pinpoint kernel and hardware bottlenecks in real time.

### Domain: Provision /home/mios as a systemd-homed LUKS2 Btrfs container bound to TPM 2.0 and FIDO2 PIN. (1 tasks)
- **AGY-2343**: Declarative systemd-homed LUKS2 user enclave configurator and TPM2/FIDO2 key manager  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Systemd-homed manages encrypted user enclaves with TPM2/FIDO2 key protection.
  - *Why:* Systemd-homed LUKS2 enclaves protect user credentials and private keys from offline physical disk extraction.

### Domain: Provision MiOS-USB as graduated hardware key for cluster nodes and multiplex virtual CCID across containers/microVMs. (1 tasks)
- **AGY-2287**: Global MiOS-USB graduated hardware key runtime and virtual CCID PC/SC multiplexer  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Smartcard multiplexer shares MiOS-USB hardware key capabilities across containers and mesh nodes.
  - *Why:* Graduated MiOS-USB hardware keys provide unified cryptographic identity, secure commit signing, and node attestation.

### Domain: Provision mediated vGPU and SR-IOV virtual slices dynamically for guest virtual machines. (1 tasks)
- **AGY-2070**: Automated SR-IOV and mdevctl mediated vGPU slice provisioner  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Mediated vGPU slices provision and attach to virtual machines automatically based on SSOT configuration.
  - *Why:* GPU fractioning enables concurrent guest OS graphics acceleration alongside host-side background AI inference.

### Domain: Provision subagent copy-on-write workspaces in <10ms using OverlayFS and isolate executions via bubblewrap. (1 tasks)
- **AGY-2289**: Ephemeral OverlayFS workspace provisioner and bubblewrap sandbox in agent-pipe  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Workspace manager provisions isolated OverlayFS environments in <10ms and merges diffs atomically.
  - *Why:* OverlayFS copy-on-write sandboxes allow hundreds of agents to edit code concurrently with zero disk duplication.

### Domain: Provision ~/.var/app/<app-id>/ as discrete subvolumes and provide atomic per-application state rollback. (1 tasks)
- **AGY-2243**: Per-app Flatpak state subvolume snapshotter and rollback manager in mios-app-snapshot  (WS-APP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Application snapshotter captures per-app state deltas and executes instant rollbacks.
  - *Why:* Per-app state rollbacks allow instant recovery from corrupted browser profiles or IDE plugins with zero blast radius.

### Domain: Provisioning/AI-lanes (1 tasks)
- **T-200**: FBM-01 -- First-boot large-model provisioner (`mios-models-first
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a fresh boot with an empty model dir pulls the SSOT set, verifies each sha, writes the sentinel, and is inert on the next boot; a network-down first boot still reaches a login with the lane serving whatever is present; killing the fetch mid-pull and rebooting resumes rather than restarting the download.

### Domain: Provisioning/Preflight (1 tasks)
- **T-1019**: PFDISK-01 -- the disk floor is measured with `df -BG`, which rounds UP, so the check is optimistic
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a filesystem with less than the floor free never reports [OK], proved with a fixture whose free space is just under a whole-gigabyte boundary.

### Domain: Provisioning/Repos (1 tasks)
- **T-1006**: REPOS-01 -- offline-first repo rendering restates [repos] in three places instead of reading it
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: changing a metalink or enabling/disabling a repo in a COPY of the SSOT changes the rendered .repo file in BOTH modes -- proved by planting and rendering offline and `--online`; the offline path still emits `file:///` vendored baseurls and reaches no network, proved by asserting no metalink appears in the offline render; and `[repos]` leaves the unconsumed register because it is read.

### Domain: Prune rejected speculative candidate token branches via in-place bitmasking and advance KV pointers in a single kernel. (1 tasks)
- **AGY-2333**: In-place tree branch bitmask pruner and speculative KV compaction kernel in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference kernel prunes unaccepted speculative tree branches in-place with zero memory leakage.
  - *Why:* In-place branch pruning ensures speculative tree decoding maintains ultra-low latency and predictable VRAM bounds.

### Domain: Prune tombstoned CRDT elements to prevent unbounded memory growth over extended operation. (1 tasks)
- **AGY-1989**: CRDT state compaction and snapshot garbage collection in mios-node  (WS-NODE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CRDT garbage collector prunes obsolete tombstones and stabilizes memory consumption.
  - *Why:* Without garbage collection, CRDT delete tombstones accumulate indefinitely and exhaust node RAM.

### Domain: Prune unreferenced container build layers when storage exceeds 80% and deduplicate identical blocks. (1 tasks)
- **AGY-2187**: LRU container image garbage collector and block deduplicator daemon in mios-container-gc  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Container GC daemon reclaims storage space and deduplicates OCI layer blocks automatically.
  - *Why:* Automated layer pruning prevents disk exhaustion on continuous self-developing AI workstations.

### Domain: Prune weights to 2:4 structural sparsity with Hessian compensation to double Tensor Core throughput at >99.2% accuracy. (1 tasks)
- **AGY-2530**: SparseGPT 2:4 structural sparsity compiler and fused mma.sp Tensor Core engine  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Compiler prunes models to 2:4 sparsity and inference engine executes fused mma.sp sparse Tensor Core kernels.
  - *Why:* 2:4 structural sparsity leverages hardware sparse Tensor Cores to double matrix math throughput without accuracy loss.

### Domain: Publish local AI and mesh services via Avahi mDNS and resolve peer nodes in <200ms without central servers. (1 tasks)
- **AGY-2414**: Declarative Avahi mDNS service publisher and ZeroConf peer resolver in mios-mdns  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Avahi publishes local services and discovers peer endpoints over mDNS in <200ms.
  - *Why:* Decentralized ZeroConf mDNS discovery allows nodes and edge devices to discover local AI clusters instantly.

### Domain: Quantize 768D embeddings to 96-byte binary vectors and evaluate via bitwise XOR + POPCOUNT for 32x RAM savings. (1 tasks)
- **AGY-2492**: 1-bit binary embedding quantizer and hardware Hamming distance matcher in mios-embed-binary  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Embedding engine quantizes vectors to 1-bit and performs million-scale Hamming lookups in <100ms.
  - *Why:* 1-bit binary embeddings allow massive million-document vector search indexes to run in low memory on laptops and phones.

### Domain: Quantize FP16 models to INT4/INT3/INT2 in <30s without calibration data via Half-Quadratic optimization. (1 tasks)
- **AGY-2422**: Calibration-free HQQ quantization compiler and fused dequantization GEMM manager  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: HQQ toolchain quantizes models in <30s and inference engine executes fused dequantization kernels.
  - *Why:* Calibration-free HQQ allows newly published models to be quantized and served locally within seconds of release.

### Domain: Quantize FP16 models to ternary {-1, 0, 1} via optimal thresholding and bitpack 4 weights/byte into .tri containers. (1 tasks)
- **AGY-2412**: Automated TriLM / BitNet ternary quantization compiler and bitpacker in mios-quantize-ternary  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Ternary compiler quantizes FP16 models to bitpacked ternary containers in under 2 minutes.
  - *Why:* Automated ternary compilation converts heavy floating-point models into ultra-lightweight integer models effortlessly.

### Domain: Quantize KV caches to 6-bit FP6 (E3M2) packed in 3-byte pairs for 62.5% VRAM savings and 99.8% precision. (1 tasks)
- **AGY-2406**: Dynamic FP6 (E3M2) KV-cache quantizer and bit-packed CUDA kernel manager in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine quantizes KV caches dynamically to bit-packed FP6 with fused CUDA kernels.
  - *Why:* FP6 quantization fills the sweet spot between FP8 capacity and FP4 fidelity, enabling large reasoning contexts on 16GB/24GB GPUs.

### Domain: Quantize KV caches to 8-bit FP8 (E4M3) with per-head scaling to cut VRAM consumption by 50%. (1 tasks)
- **AGY-2361**: Dynamic FP8 (E4M3) KV-cache quantizer and per-head scale manager in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine quantizes KV caches dynamically to FP8 with per-head scaling.
  - *Why:* FP8 KV caching doubles concurrent session density and enables massive context windows on consumer GPUs.

### Domain: Quantize attention heads at Q5_K/Q6_K and FFN layers at Q4_K_M to fit 32B models into 16GB VRAM budgets. (1 tasks)
- **AGY-2371**: Dynamic K-Quants mixed-precision layer slicer (Q4_K_M / Q5_K_M / Q6_K) in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine loads mixed-precision K-Quant models fitting 32B weights into 16GB VRAM.
  - *Why:* Mixed-precision K-Quants preserve critical attention head resolution while fitting heavy models into consumer VRAM.

### Domain: Quantize base weights to 4-bit NF4 with Double Quantization and dispatch fused LoRA residual kernels in <1ms. (1 tasks)
- **AGY-2516**: NF4 Double-Quantized base and fused LoRA residual adapter dispatcher in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference and training engine executes NF4 double-quantized models with fused LoRA adapters in <24GB VRAM.
  - *Why:* QLoRA NF4 Double Quantization enables fine-tuning and specialized adaptation of 70B parameter models on single 24GB GPUs.

### Domain: Quantize keys and values to 4-bit MXFP4 with block-32 scale vectors for 75% VRAM savings and 4x density. (1 tasks)
- **AGY-2369**: Microscaling MXFP4 (E2M1) KV-cache quantizer and block-32 scale vector manager in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine quantizes KV caches dynamically to MXFP4 with block-32 scale vectors.
  - *Why:* MXFP4 KV caching achieves 4x memory density, enabling massive concurrent agent swarms on local workstations.

### Domain: Quantize weights into 2 shared 8D codebooks (2-bit average) and dispatch fused CUDA kernels in 18.2GB VRAM. (1 tasks)
- **AGY-2550**: AQLM 2-bit multi-codebook vector engine and fused CUDA dequant kernel in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes AQLM 2-bit multi-codebook vector kernels on GPU Tensor Cores at <18.5GB VRAM.
  - *Why:* AQLM additive vector quantization achieves the highest accuracy among all sub-3-bit compression formats.

### Domain: Query UEFI EFI_RNG_PROTOCOL in early boot stub and randomize kernel physical/virtual base offsets. (1 tasks)
- **AGY-2299**: Early EFI_RNG_PROTOCOL KASLR entropy collector and kernel memory randomizer  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Kernel boot stub collects EFI_RNG_PROTOCOL entropy and randomizes memory base offsets.
  - *Why:* High-entropy KASLR prevents kernel memory layout prediction and neutralizes return-oriented programming exploits.

### Domain: ROADMAP.md's state table is generated, not asserted. (1 tasks)
- **AGY-1634**: Record the honest state table from measurement  (WS-THESIS | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every number in the table is either derived from a gate or explicitly marked as unmeasured, and the table regenerates in `sync-generated`.
  - *Why:* the roadmap is the project's own account of itself; hand-maintained numbers in it drift exactly like hand-maintained config.

### Domain: Raising a shrink-only floor fails CI. (1 tasks)
- **AGY-1823**: Ratchets can only be lowered, and nothing enforces it  (WS-GATE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a commit that raises any ratchet ceiling fails, and one that lowers it passes.
  - *Why:* every ratchet in the tree is enforced by discipline alone, and discipline has already failed once.

### Domain: Re-distribute in-flight AI tasks immediately when an assigned cluster node disconnects. (1 tasks)
- **AGY-2136**: Automated node failure detection and zero-loss dynamic task re-distribution engine  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Task failover engine detects node drops and completes in-flight AI tasks across surviving nodes.
  - *Why:* Dynamic re-distribution guarantees system resiliency across unstable network links or power interruptions.

### Domain: Record agent steps and tool executions into an unforgeable Merkle-chained audit log in PostgreSQL. (1 tasks)
- **AGY-2151**: Cryptographic Merkle-tree agent audit chain recorder and Ed25519 block signer  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Audit chain engine signs agent execution blocks and enforces Merkle linkage in PostgreSQL.
  - *Why:* Cryptographic audit chaining provides mathematical proof of agent actions and prevents post-hoc log tampering.

### Domain: Record last 60 seconds of kernel syscalls, I/O latency, and GPU events in a circular ring. (1 tasks)
- **AGY-2114**: In-kernel eBPF circular flight recorder ring and crash diagnostic parser  (WS-DIAG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: eBPF flight recorder logs rolling kernel states and crash parser reconstructs pre-panic events.
  - *Why:* A rolling flight recorder reveals the exact sequence of agent operations leading up to a system crash.

### Domain: Reformat GPTQ weights into Marlin 2D tiled layouts and dispatch fused INT4/FP16 Tensor Core kernels for 3.8x speedup. (1 tasks)
- **AGY-2472**: GPTQ-Marlin 2D tiled layout converter and fused Tensor Core GEMM dispatcher in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine loads GPTQ-Marlin models and executes fused 2D tiled Tensor Core kernels at >3.8x speedup.
  - *Why:* GPTQ-Marlin restructures tensor layouts to saturate physical memory bandwidth, delivering near-theoretical GPU inference speeds.

### Domain: Regulate swarm agent allocations against a 16GB host memory budget, enabling >1,500 background workers without OOM thrashing. (1 tasks)
- **AGY-2570**: PSS memory budget regulator and swarm agent OOM circuit breaker in agent-pipe  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: PSS memory regulator admits >1,500 concurrent worker tasks while strictly bounding total allocation below 16GB.
  - *Why:* Proportional Set Size regulation guarantees system stability and high-density agent swarm execution on standard workstations.

### Domain: Reliability/Health (1 tasks)
- **T-981**: Android battery and thermal watchdog with greenboot wanted.d work drain
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Crossing either threshold drains work and refuses new tasks; the check never blocks boot; thresholds resolve from the SSOT.

### Domain: RemoteDesktop/GPU (1 tasks)
- **T-213**: RDSK-01 -- Selkies (WebRTC + NVENC) GPU remote-desktop lane  [P3
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a GPU host streams the desktop over NVENC/WebRTC and a non-GPU host falls back to the VNC path with no manual switch.

### Domain: Render and apply SSOT theme palettes across GTK3/4, QT6, and terminal PTYs live. (1 tasks)
- **AGY-2097**: Multi-surface theme renderer with ANSI OSC 4/10/11 PTY injector and GTK/QT CSS generator  (WS-LANG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Theme renderer propagates color palette updates across GTK, QT, and active PTYs with zero restarts.
  - *Why:* Instant multi-surface theme synchronization provides a cohesive, polished operator aesthetic.

### Domain: Replace the shell-based `/usr/bin/mios` script with a fast, compiled multi-call CLI binary. (1 tasks)
- **AGY-1997**: High-performance binary CLI dispatcher (/usr/bin/mios) in Rust  (WS-LANG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Compiled `mios` CLI binary replaces shell dispatcher with sub-5ms command invocation latency.
  - *Why:* The primary user-facing CLI should have zero startup latency and provide robust argument parsing and help menus.

### Domain: Replicate CephFS/RBD snapshot deltas over WireGuard every 15min and enable 1-click remote failover promotion. (1 tasks)
- **AGY-2432**: Asynchronous Ceph snapshot mirroring daemon and multi-node recovery manager in mios-ceph-mirror  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Mirroring daemon replicates incremental snapshot deltas and executes 1-click disaster recovery.
  - *Why:* Asynchronous snapshot mirroring guarantees multi-site disaster recovery without slowing local client I/O.

### Domain: Replicate critical task and audit ledgers across distributed CephFS storage pools with cryptographic integrity. (1 tasks)
- **AGY-2000**: Transactional ledger replication across CephFS pools with integrity hashing  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Ledger replication synchronizes audit journals across cluster nodes with verified cryptographic integrity.
  - *Why:* Distributed multi-agent systems require tamper-evident shared ledgers for security auditing.

### Domain: Reserve 16MB RAM for ramoops in UKI kargs, log kernel panics atomically, and ingest into database on boot. (1 tasks)
- **AGY-2388**: Persistent pstore ramoops kernel crash buffer manager and post-mortem extractor in mios-pstore  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Pstore ramoops preserves kernel panic backtraces across reboots and extracts them automatically.
  - *Why:* Persistent RAM crash logging guarantees forensic trace availability even during hard hardware watchdog resets.

### Domain: Retain warm KV-cache blocks in an LRU session pool to bind incoming agent requests in <1ms without re-allocation. (1 tasks)
- **AGY-2434**: Warm KV-cache ring pooler and dynamic session recycling manager in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine maintains warm KV pool and recycles session memory across agent handoffs in <1ms.
  - *Why:* Warm KV memory recycling eliminates GPU memory allocation stalls and accelerates multi-agent collaboration loops.

### Domain: Reuse pre-allocated packet buffers to minimize heap fragmentation under high network traffic. (1 tasks)
- **AGY-1991**: Zero-copy network buffer pooling to reduce memory allocations in mios-node  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Buffer pool recycles frame memory with zero per-packet heap allocations in the hot path.
  - *Why:* Frequent memory allocations in network framing loops degrade throughput and cause garbage collection pauses.

### Domain: Rotate volume encryption keys periodically without unmounting active storage pools. (1 tasks)
- **AGY-2003**: Encrypted volume key rotation service for LUKS2 and dm-crypt Ceph OSD drives  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: LUKS2 volume keys rotate seamlessly in-place with zero downtime.
  - *Why:* Cryptographic compliance requires periodic rotation of data-at-rest encryption keys.

### Domain: Route .mios queries to local WireGuard resolver and encrypt public queries via strict DNS-over-TLS. (1 tasks)
- **AGY-2295**: Split-DNS systemd-resolved configurator for .mios mesh domains and strict DoT  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Systemd-resolved resolves `.mios` mesh queries locally and encrypts public traffic over DoT.
  - *Why:* Split-DNS prevents internal hostname leakage and protects public DNS traffic from eavesdropping.

### Domain: Route embeddings and wake-word to NPU (<2W) or quantized CPU vector threads, power-gating discrete GPUs. (1 tasks)
- **AGY-2291**: Hierarchical accelerator router with NPU priority and CPU vector fallback  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Accelerator router dispatches lightweight AI tasks to NPU/CPU and keeps discrete GPUs asleep.
  - *Why:* Heterogeneous accelerator routing with CPU fallback maximizes battery endurance and eliminates unnecessary fan noise.

### Domain: Route shallow layer representations to exit adapters and reuse primary KV-cache for >1.9x speedup with 0MB extra VRAM. (1 tasks)
- **AGY-2554**: Kangaroo draftless self-speculative early-exit engine in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes Kangaroo draftless self-speculative early-exit decoding at >1.9x speedup.
  - *Why:* Kangaroo self-speculation delivers massive decoding speedups without requiring any extra VRAM for separate draft models.

### Domain: Route system DNS queries through local AdGuard Home with split-horizon resolution for .mios domains. (1 tasks)
- **AGY-2095**: systemd-resolved to mios-adguard split-horizon DNS routing configurator  (WS-NET | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: System DNS resolves internal mesh hostnames and external DoH queries seamlessly through AdGuard Home.
  - *Why:* Split-horizon encrypted DNS blocks telemetry tracking and secures name resolution across private and public domains.

### Domain: Routing/Catalog (1 tasks)
- **T-222**: OAI-01 -- Unified multi-kind capability catalog (recipes + skill
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Recipes and skills appear as catalog rows carrying `kind`/`domain`, the router demonstrably routes a turn to each kind, and a recipe→skill composition is rejected by the loader rather than silently accepted.

### Domain: Routing/Cost (1 tasks)
- **T-227**: KACT-02 -- Remote SmartRouting + quality-gate + daily budget (`m
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A forced quality-gate failure escalates to a remote lane and returns; with the daily budget exhausted the same failure falls back to local instead of spending; with the feature at its default the path is inert.

### Domain: SSOT/Cross-cutting (1 tasks)
- **T-165**: NAME-01 -- Global naming minification → one unified names/keys r
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: One registry is the naming SSOT with every surface generated from or sourcing it and no authored per-name mapping left anywhere; similar capabilities are folded to one parametric entry with legacy names and the userenv table deleted at zero functional regression; and a drift-gate regenerates and diffs the registry, failing on any new translation or duplicate, with all `test_mios_*` and `just drift-gate` green.

### Domain: SSOT/DB/Configurator (1 tasks)
- **T-247**: VECTOR-05 -- V5 Invert authority: DB=SSOT, TOML=generated export
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A configurator edit writes the DB and emits a `config_event`, the regenerated `mios.toml` export diffs clean against the DB in the drift-gate, a time-travel rollback restores prior config, and `just drift-gate` plus `test_mios_*` pass.

### Domain: SSOT/Identity (1 tasks)
- **T-236**: NAME2-01 -- Agent-plane user SSOT reconciliation (820/822 → 850)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: SSOT and every consumer name the same live agent-plane uid, and a tree-wide search returns no remaining 820/822 references.

### Domain: SSOT/Law9 (2 tasks)
- **T-1013**: DUPVAL-01 -- the row is STALE on both numbers: the gate is GREEN at "406 groups at ceiling 406" with 406 ledger rows, not 412 vs 407, and ZERO ledger rows are stale. It is also NOT a Count-Only Ratchet -- the ledger pins each group's exact KEY SET, so two count-invariant mutations (a swap, and a key joining an existing group) both FAIL while the count stays 406. THE REAL DEFECT, proven end to end: MIOS_VALUE_DUP_BASELINE_BUMP=1 rewrites `#!ceiling` to the live count UP as readily as down, so planting a 407th duplicate and running the command the ledger's own header prints absorbs it and the gate re-reads green. The ledger's ceiling sits outside every shrink-only monotonicity gate (mios-gate ratchet-direction and check_doc_ratchet_monotone both read only mios.toml), by the same design choice its header explains. A GUARD WAS BUILT AND VERIFIED, then reverted: capture the prior ceiling during the header re-read and refuse a higher one unless MIOS_VALUE_DUP_BASELINE_BUMP=raise -- four arms green (equal regenerates byte-identically; live>declared REFUSES and writes nothing; =raise regenerates; a TIGHTENING still passes), plus a negative-test arm whose mutation control exits 1 by name when the guard is stubbed out. BLOCKED: it costs +10 tooling-Python lines (+22 uncompressed) against legibility.max_tooling_python_lines, which T-1044 pulled to its measurement with ZERO slack per that ceiling's own stated convention ("T-1052's repair had to fit inside it rather than ask for room"). So a zero-slack ratchet admits no Python tooling improvement at all. Three exits, all operator calls: offset by deleting >=10 lines of tooling Python; move the floor by the guard's exact cost with a reason; or port check_no_duplicate_value_key to mios-gate per the Rust directive. Recover the reverted work from this session's transcript
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the live group count is at or under the ceiling WITHOUT the ceiling moving up; `MIOS_PORTS_RADOSGW`/`MIOS_RADOSGW_PORT` and `MIOS_URLS_NON_ADDRESSABLE` are gone or provably one declaration; the ledger has no SHRANK or vanished rows; `test_no_duplicate_value_key` passes, dropping the CI negative-test failures from 8 to 7.
- **T-1020**: ALIAS-01 -- MIOS_AI_RAM_FLOOR_GB had two sources and table order picked the winner; the gate that catches it skips locally
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a gate reports any `MIOS_*` name produced by more than one dotted path and fails; planting a second producer for an existing name fails it; the remaining allowlist entries are each shown to have a single producer.

### Domain: Sample Linux PSI metrics continuously and signal throttling events to inference workers. (1 tasks)
- **AGY-2083**: Linux PSI (Pressure Stall Information) monitor daemon in agent-pipe  (WS-SCHED | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: PSI monitor detects system resource saturation in real time with sub-2s latency.
  - *Why:* Early detection of CPU/memory pressure prevents system lockups and audio/video stuttering in interactive sessions.

### Domain: Sample inter-GPU NVLink/PCIe throughput in real time and render live tensor heatmaps in Cockpit and CLI. (1 tasks)
- **AGY-2261**: Multi-GPU NVLink / PCIe interconnect profiler and P2P bandwidth heatmap daemon  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: GPU heatmap daemon samples interconnect throughput and renders live matrix telemetry.
  - *Why:* Real-time P2P bandwidth visualization identifies PCIe lane degradation and tensor bottlenecks instantly.

### Domain: Sandboxing/Wasm (1 tasks)
- **T-979**: Fuel-metered Wasm engine in the native mios-node crate with interpreter fallback
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A fuel-metered module runs on-device, exhausting fuel terminates it, and a test exercises the interpreter path rather than assuming it.

### Domain: Scan screenshot frames for visible credit card numbers, private keys, and API tokens and mask matching text regions. (1 tasks)
- **AGY-2138**: Lightweight on-device OCR regex credential masking pipeline for vision frames  (WS-AI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: OCR masking pipeline detects and redacts credential text patterns from vision frames locally.
  - *Why:* Local OCR pattern masking catches unmasked plaintext secrets displayed inside non-accessible terminal or web windows.

### Domain: Scan synthesized OCI container images with Trivy/Grype and block deployment on Critical CVSS >= 9.0 vulnerabilities. (1 tasks)
- **AGY-2259**: Automated Trivy / Grype OCI image vulnerability scanner and CVE report generator  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Vulnerability scanner audits OCI image archives and generates machine-readable CVE reports.
  - *Why:* Automated vulnerability gating prevents known security flaws from entering the immutable host operating system.

### Domain: Scheduler/Cgroup (1 tasks)
- **T-486**: Dynamic cgroup v2 cpu.max and memory.high pressure-adaptive controller
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Dynamic cgroup controller restricts background slices under pressure and recovers automatically.

### Domain: Scheduler/PSI (1 tasks)
- **T-485**: Linux PSI (Pressure Stall Information) monitor daemon in agent-pipe
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: PSI monitor detects system resource saturation in real time with sub-2s latency.

### Domain: Seal host master secrets cryptographically to TPM 2.0 PCR 7 and PCR 11 measurements. (1 tasks)
- **AGY-2091**: TPM 2.0 PCR 7/11 systemd-creds automated secret sealing and enrollment script  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Master credentials are sealed to hardware TPM 2.0 bound strictly to PCR 7 and 11.
  - *Why:* TPM sealing guarantees credentials remain inaccessible if disks are stolen or unauthorized kernels booted.

### Domain: Seamlessly route inter-node frames over Tailscale/WireGuard WAN tunnels when local LAN connectivity is lost. (1 tasks)
- **AGY-1994**: Automated fallback to Tailscale and WireGuard overlay when LAN broadcast is partitioned  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Mesh routing switches between LAN and WAN overlay transports automatically based on reachability.
  - *Why:* Distributed nodes must maintain mesh federation across remote home offices and multi-site deployments.

### Domain: Search/Cache (1 tasks)
- **T-476**: Search Result Semantic Vector Cache & Deduplication in pgvector
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Semantic search cache serves repeated queries locally with sub-10ms response times.

### Domain: Search/Scrubbing (1 tasks)
- **T-475**: Pre-Search Query Sanitization & Secret Scrubbing Filter in agent-pipe
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Pre-search filter scrubs sensitive tokens from outgoing search queries reliably.

### Domain: Security (1 tasks)
- **T-033**: SEC-02 -- Semantic Firewall (CaMeL-class Taint Propagation)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A web-fetched result driving `service_restart` lands in HITL rather than executing, a local-only result driving the same verb executes directly, and every decision is a pgvector `event` row carrying a `verdict` field.

### Domain: Security/ACL (1 tasks)
- **T-478**: POSIX ACL and user namespace validator in greenboot pre-flight checks
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Greenboot validates container storage ACLs and subordinate namespace isolation on every boot.

### Domain: Security/Anomaly (1 tasks)
- **T-512**: Jensen-Shannon divergence anomaly alarm and PostgreSQL threat_events vector sink
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Anomaly detector flags abnormal network traffic shifts and stores threat vectors in PostgreSQL.

### Domain: Security/BHIGuard (1 tasks)
- **T-958**: Hardware BHI_DIS_S enforcer and universal BHB history clearing guard in mios-bhi-guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security guard enforces BHI_DIS_S and BHB clearing across security domains in <150ns.

### Domain: Security/BHITest (1 tasks)
- **T-959**: Automated Spectre-BHI mitigation verification (<150ns latency) and /proc test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond BHB clearing, kernel vulnerability reporting, and total Spectre-BHI immunity.

### Domain: Security/BPFLSM (1 tasks)
- **T-842**: Declarative BPF LSM security policy enforcer and hook monitor in mios-bpf-lsm
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: BPF LSM programs enforce programmable in-kernel security policies and prevent privilege escalation.

### Domain: Security/BPFLSMTest (1 tasks)
- **T-843**: Automated container escape blocking, ptrace denial (<1us), and BPF LSM test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates in-kernel LSM denial, microsecond enforcement speed, and complete audit logging.

### Domain: Security/Boot (1 tasks)
- **T-239**: UKI-01 -- verity-rooted UKI build + fapolicyd enforce-promotion
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: All four defects are fixed and a VM boots a verity-rooted signed UKI with fapolicyd in enforce while agent codegen still executes -- with observe-mode remaining the shipped default.

### Domain: Security/CoreSched (1 tasks)
- **T-858**: Linux Core Scheduling cookie tagger and SMT sibling isolator in mios-core-sched
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Core scheduler tags untrusted processes and guarantees zero cross-SMT side-channel co-location.

### Domain: Security/CoreSchedTest (1 tasks)
- **T-859**: Automated SMT sibling isolation verification (<1us tagging) and core scheduling test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond cookie tagging, strict SMT sibling isolation, and scheduler security guarantees.

### Domain: Security/ExecSandbox (1 tasks)
- **T-890**: Declarative Landlock and Bubblewrap ephemeral sandbox wrapper in mios-exec-sandbox
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Execution sandbox isolates untrusted commands in <5ms and blocks unauthorized filesystem modifications.

### Domain: Security/ExecTest (1 tasks)
- **T-891**: Automated <5ms sandbox launch latency, write denial, and network isolation test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-5ms sandbox provisioning, read-only host protection, and network isolation.

### Domain: Security/FPUZero (1 tasks)
- **T-912**: Dynamic AVX/FPU register zeroization engine and GDS mitigation manager in mios-fpu-zero
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security sanitizer clears AVX-512 and FPU register state on domain switches in <50ns.

### Domain: Security/FPUZeroTest (1 tasks)
- **T-913**: Automated Downfall/GDS vector register scrub (<50ns latency) and SIMD isolation test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-50ns vector scrubbing, Downfall exploit neutralization, and high compute performance.

### Domain: Security/Federation (1 tasks)
- **T-327**: SEC-02 -- A seat's auth posture must follow the role, not an operator remembering a flag
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: three of five clauses met.

### Domain: Security/IBPBGuard (1 tasks)
- **T-898**: Dynamic IBPB indirect branch barrier manager and BTB sanitizer in mios-ibpb-guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security guard issues targeted IBPB barriers on security domain switches in <800ns.

### Domain: Security/IBPBTest (1 tasks)
- **T-899**: Automated Spectre v2 BTB mitigation verification (<800ns IBPB) and context-switch test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-800ns barrier execution, branch predictor invalidation, and zero speculative leakage.

### Domain: Security/IBTGuard (1 tasks)
- **T-962**: Automated IBT/BTI landing pad enforcer and control-flow compiler in mios-ibt-guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security runtime and build toolchain enforce IBT/BTI landing pad verification across all binaries and kernel modules.

### Domain: Security/IBTTest (1 tasks)
- **T-963**: Automated IBT/BTI illegal jump trapping (<5ns) and binary landing pad test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates landing pad opcode presence, hardware exception trapping, and minimal CPU overhead.

### Domain: Security/IMAAppraise (1 tasks)
- **T-926**: In-kernel IMA appraisal and signed xattr verifier in UKI bootchain
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Kernel blocks execution of tampered binaries via IMA appraisal and validates signed extended attributes.

### Domain: Security/IMATest (1 tasks)
- **T-927**: Automated IMA binary appraisal, tampered executable rejection, and latency test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates cryptographic file appraisal, tampered executable denial, and low verification overhead.

### Domain: Security/Kernel (1 tasks)
- **T-168**: KENF-01 -- Tetragon eBPF/LSM kernel enforcement plane  [P2] [VM]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: In observe mode a tainted process's disallowed `execve` or outbound connect produces a Tetragon Post event and a shipper row; flipping to enforce SIGKILLs the offending process; the unit is Condition-skipped and inert on the WSL2 dev VM; `bootc container lint` and the Law-6 postcheck pass with the documented exception; and editing `[security.policy]` re-renders the TracingPolicy YAML with no hardcoded policy.

### Domain: Security/L1DFlush (1 tasks)
- **T-882**: Dynamic L1 Data Cache flusher and context-switch sanitizer in mios-l1d-flush
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security sanitizer flushes L1D cache lines on targeted context switchouts in <500ns.

### Domain: Security/L1DTest (1 tasks)
- **T-883**: Automated L1TF cache flush latency (<500ns) and context-switch test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond cache flush latency, complete L1D invalidation, and zero side-channel leakage.

### Domain: Security/LandlockNet (1 tasks)
- **T-906**: Dynamic Landlock ABI v1..v4 ruleset negotiator and network port enforcer in mios-exec-sandbox
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Sandbox negotiator enforces filesystem and network rulesets dynamically across all Landlock ABI versions.

### Domain: Security/LandlockNetTest (1 tasks)
- **T-907**: Automated Landlock ABI negotiation, unprivileged network port denial, and file test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates multi-ABI compatibility, microsecond network port denial, and strict directory sandboxing.

### Domain: Security/LandlockScope (1 tasks)
- **T-934**: Dynamic Landlock scoped IPC and signal isolation guard in mios-exec-sandbox
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Sandbox guard isolates abstract Unix sockets and process signals dynamically across Landlock ABI v5.

### Domain: Security/LandlockScopeTest (1 tasks)
- **T-935**: Automated Landlock scoped abstract socket and signal denial (<1us) test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond abstract socket isolation, signal protection, and flawless intra-sandbox IPC.

### Domain: Security/Law5 (1 tasks)
- **T-1002**: LAW5-01 -- retired lane ports are hardcoded across the code surface and no gate covers code
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a planted retired port in a live code path FAILS the gate and the message names the file and the port; the classification of today's ~52 hits is recorded; and the retained residue is an itemised register under a ceiling that only falls.

### Domain: Security/LivepatchMOK (1 tasks)
- **T-782**: Cryptographic MOK livepatch signature gate and IMA measurement logger in mios-livepatch
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Livepatch manager validates MOK signatures and logs IMA measurements before applying kernel patches.

### Domain: Security/LivepatchTest (1 tasks)
- **T-783**: Automated livepatch signature verification, unsigned module rejection, and IMA test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates strict MOK signature gating, rapid ftrace redirection, and IMA attestation logging.

### Domain: Security/ModSignEnforce (1 tasks)
- **T-916**: Strict kernel module signature enforcer and lockdown runtime in UKI bootchain
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Kernel enforces module signature checking and lockdown confidentiality across all module loads.

### Domain: Security/ModSignTest (1 tasks)
- **T-917**: Automated unsigned kernel module rejection and lockdown integrity test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates unsigned module rejection, MOK key validation, and lockdown memory protections.

### Domain: Security/PenTest (1 tasks)
- **T-480**: Container bridge lateral movement penetration test in CI test suites
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Automated CI test verifies container network isolation boundaries continuously.

### Domain: Security/Policy (1 tasks)
- **T-982**: Consult the policy arbiter by default instead of shipping it unreachable
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: With the arbiter up, a dangerous verb is gated by it; with the arbiter down, the verb is refused rather than allowed; no host allowlist literal remains in server.py.

### Domain: Security/Quadlets (1 tasks)
- **T-1035**: QUADSEC-01 -- DB passwords render as literals into 0644 Quadlets under /usr, and a build-env var can write User=0 off the privileged roster
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a planted `MIOS_PG_PASS` never appears as a literal in any rendered unit; a planted `MIOS_<name>_UID=0` for a unit off the roster FAILS the stage; a gate asserts no rendered unit under `/usr` carries a password-shaped `Environment=` value.

### Domain: Security/RSBGuard (1 tasks)
- **T-938**: Dynamic RSB buffer stuffing and context-switch underflow guard in mios-rsb-guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security guard overwrites 32 RSB entries on security domain context switches in <100ns.

### Domain: Security/RSBTest (1 tasks)
- **T-939**: Automated ret2spec RSB underflow mitigation (<100ns latency) and context-switch test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-100ns RSB stuffing, complete underflow neutralization, and negligible overhead.

### Domain: Security/Recovery (1 tasks)
- **T-494**: Offline split-key emergency recovery and TPM unseal failure test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Emergency recovery tool successfully restores sealed vault data following simulated TPM lockouts.

### Domain: Security/SLSGuard (1 tasks)
- **T-942**: Automated Straight-Line Speculation (SLS) compiler enforcer and post-branch traps
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Compiler and security runtime enforce SLS hardening across all built binaries with post-branch trap instructions.

### Domain: Security/SLSTest (1 tasks)
- **T-943**: Automated SLS post-return trap verification (<5ns barrier) and disassembly test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates post-branch trap opcodes on all unconditional jumps, zero fault rate, and minimal overhead.

### Domain: Security/SSBDGuard (1 tasks)
- **T-946**: Dynamic SSBD context-switch enforcer and speculative store isolation guard in mios-ssbd-guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security guard enforces targeted SSBD on untrusted sandboxes and disables speculative store bypass in <500ns.

### Domain: Security/SSBDTest (1 tasks)
- **T-947**: Automated Spectre v4 / SSB mitigation verification (<500ns MSR toggle) and /proc test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond SSBD activation, /proc kernel status compliance, and complete Spectre v4 neutralization.

### Domain: Security/SSBGuard (1 tasks)
- **T-862**: Dynamic Speculative Store Bypass (SSB) process sandboxer and prctl controller in mios-ssb-guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security guard enforces per-process SSB mitigation and neutralizes Spectre v4 side-channel vectors.

### Domain: Security/SSBTest (1 tasks)
- **T-863**: Automated Spectre v4 SSB mitigation verification (<1us prctl) and memory test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond SSB enforcement, thread-level speculation status, and 0 side-channel leakage.

### Domain: Security/Sandbox (2 tasks)
- **T-169**: ISOL-01 -- Per-action isolation tier ladder (promote-not-refuse)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Tainting a session with an external `open_url` and then dispatching a high-privilege verb records a `firewall_promote` event with the verb having run in the promoted tier; `[isolation].enable=false` leaves behavior byte-identical to today; the tier-4 microVM Quadlet is inert on WSL2 with no `/dev/kvm`; and `test_mios_isolation.py` passes on tier selection and degrade-closed.
- **T-309**: SBX-01 -- Reconcile the reference bwrap argv with the wrapper
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Exactly one definition of the confined argv exists, or a test fails when the two diverge; and a confined verb on a real host is observed running under the flag set the surviving definition names.

### Domain: Security/SecMemTest (1 tasks)
- **T-879**: Automated secret memory zeroization (<1us scrub) and swap leak prevention test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond DRAM scrubbing, swap protection, and complete compiler optimization resistance.

### Domain: Security/SeccompGen (1 tasks)
- **T-910**: Dynamic seccomp-bpf syscall filter synthesizer and user-notification gate in mios-seccomp-gen
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security synthesizer compiles and attaches seccomp-bpf filter trees in <100us.

### Domain: Security/SeccompTest (1 tasks)
- **T-911**: Automated seccomp-bpf attachment latency (<100us), syscall denial, and user notification test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-100us filter attachment, complete syscall blocking, and user-space notification handling.

### Domain: Security/SecureMemory (1 tasks)
- **T-878**: Locked secure memory allocator and compiler-barrier zeroization runtime in libmios-sec
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security library allocates locked memory pages and sanitizes secret buffers via compiler barriers.

### Domain: Security/SpecFence (1 tasks)
- **T-902**: Automated array bounds speculation barrier instrumenter and index masker in mios-spec-fence
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security instrumenter protects array bounds with LFENCE/CSDB and prevents Spectre v1 out-of-bounds reads.

### Domain: Security/SpecFenceTest (1 tasks)
- **T-903**: Automated Spectre v1 bounds check bypass exploit prevention (<10ns barrier) and SLH test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates nanosecond barrier latency, zero out-of-bounds leak recovery, and minimal runtime overhead.

### Domain: Security/Supply (1 tasks)
- **T-1036**: COSIGN-01 -- signature verification ships off (insecureAcceptEverything), cannot be turned on, and the stage is non-fatal
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `policy_mode` is operator-settable and reaches the rendered policy; a non-permissive policy validates under a real parser (`skopeo standalone-verify` / `podman --signature-policy`, not `jq -e .`); at least one trust root ships; a missing or malformed policy fails the stage.

### Domain: Security/TPM2 (1 tasks)
- **T-493**: TPM 2.0 PCR 7/11 systemd-creds automated secret sealing and enrollment script
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Master credentials are sealed to hardware TPM 2.0 bound strictly to PCR 7 and 11.

### Domain: Security/UFFDGuard (1 tasks)
- **T-920**: User-mode-only userfaultfd enforcer and ephemeral page interceptor in mios-uffd-guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security guard enforces user-mode-only page fault handling and blocks kernel fault interception.

### Domain: Security/UFFDTest (1 tasks)
- **T-921**: Automated UFFD_USER_MODE_ONLY demand-paging (<1us latency) and kernel fault test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates kernel-space fault denial, user-space demand-paging latency, and memory isolation.

### Domain: Security/UFFDWPTest (1 tasks)
- **T-931**: Automated UFFDIO_WRITEPROTECT intercept latency (<1us), dirty page logging test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond fault intercept latency, exact dirty page tracking, and zero memory corruption.

### Domain: Security/UFFDWriteProtect (1 tasks)
- **T-930**: userfaultfd write-protection engine and dirty page tracker in mios-uffd-guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Memory virtualization runtime tracks dirty pages and protects buffers via UFFD write-protection in <1us.

### Domain: Security/USBGuard (1 tasks)
- **T-798**: Declarative USBGuard device authorization daemon and read-only storage mounter
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: USBGuard blocks unauthorized devices and enforces read-only mounts on external storage.

### Domain: Security/USBTest (1 tasks)
- **T-799**: Automated BadUSB device rejection, read-only mount enforcement, and audit test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates instant BadUSB blocking, secure mount flag enforcement, and event logging.

### Domain: Security/UniversalMemTag (1 tasks)
- **T-950**: Universal hardware-agnostic memory safety and tagging negotiator in mios-mem-tag-guard
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Security runtime dynamically negotiates hardware memory tagging across ARM64, x86_64, and fallback architectures.

### Domain: Security/UniversalMemTest (1 tasks)
- **T-951**: Automated cross-architecture memory tagging negotiation and violation test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates multi-architecture capability negotiation, accurate violation trapping, and robust fallback handling.

### Domain: Security/eBPF (1 tasks)
- **T-511**: In-kernel eBPF network flow aggregation probe and mios-netflowd collector daemon
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: eBPF flow probe aggregates network connections and streams summarized telemetry to userspace.

### Domain: Serialize microVM CPU registers, dirty memory pages, and virtio-pmem DAX descriptors for <50ms live handover. (1 tasks)
- **AGY-2566**: Zero-downtime MicroVM state serialization and live migration handover engine in mios-virt  (WS-HCI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: MicroVM live migration engine serializes and transfers execution state with sub-50ms latency.
  - *Why:* Live microVM migration enables seamless workload rebalancing and hot-patching across hyper-converged host clusters.

### Domain: Sign next-generation OCI image manifests with host Ed25519 keys and push to local registry. (1 tasks)
- **AGY-2108**: Local Cosign image signing and registry push validation gate  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Cosign publish tool signs images and verifies signatures before host deployment transitions.
  - *Why:* Cryptographic image signatures ensure that only authentic, verified OS images are booted onto the host.

### Domain: Silent failures are impossible to act on, so make them impossible to ship. (1 tasks)
- **AGY-1815**: A check that exits non-zero with no diagnostic must fail the suite  (WS-GATE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a check stubbed to exit 1 with no output produces a violation that names it.
  - *Why:* in a log, a non-zero exit with no message is indistinguishable from a pass.

### Domain: Skip default LFS download on clone, fetch only requested quantization blobs, and cache in /var/cache/mios/lfs/. (1 tasks)
- **AGY-2313**: Declarative Git LFS sparse fetcher and shared content-addressed blob cache manager  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Git LFS sparse fetcher downloads only targeted model files and caches blobs efficiently.
  - *Why:* Sparse LFS fetching saves hundreds of gigabytes of disk and network bandwidth when managing large AI models.

### Domain: Slice large prefill prompts into 512-token chunks and interleave with active token decode steps for <5ms jitter. (1 tasks)
- **AGY-2486**: Interleaved chunked prefill scheduler and iteration-level batcher in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine schedules chunked prefills alongside active decode streams with <5ms jitter.
  - *Why:* Chunked prefill prevents long prompt ingestion from interrupting ongoing interactive agent and user streaming sessions.

### Domain: Spawn ephemeral microVMs in <50ms with Virtio-VSOCK host communication for untrusted agent tasks. (1 tasks)
- **AGY-2167**: Ephemeral Cloud-Hypervisor microVM orchestrator and Virtio-VSOCK agent tool bridge  (WS-VFIO | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: MicroVM orchestrator executes untrusted tasks inside ephemeral hypervisor sandboxes with VSOCK IPC.
  - *Why:* MicroVM isolation provides true hardware-level virtualization security for untrusted code execution.

### Domain: Split 80-layer 70B models across local GPUs and remote RPC workers with calculated activation tensor network handoffs. (1 tasks)
- **AGY-2572**: Distributed pipeline tensor dispatcher with dynamic RPC worker layer partitioning  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Tensor pipeline dispatcher calculates network payloads and partitions 80-layer models across distributed RPC workers.
  - *Why:* Distributed tensor pipeline parallelism enables high-parameter models (70B+) to execute across commodity networked hardware.

### Domain: Standards/A2A (1 tasks)
- **T-218**: STD26-02 -- A2A v1.0.0 + signed AgentCard (JWS/JCS) + task-state
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the published card validates as A2A v1.0 with a verifiable `AgentCardSignature`, and DAG/swarm progress is observable by a stock A2A client as standard task states with push updates.

### Domain: Standards/Federation (1 tasks)
- **T-219**: STD26-03 -- AGNTCY OASF Agent Directory + DID Agent Identity  [P
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: peers register via OASF records carrying DID identity, the directory syncs between hosts, and agent-pipe routes from the directory rather than reading the static overlay files.

### Domain: Standards/HITL (1 tasks)
- **T-221**: STD26-05 -- Standards-based HITL (MCP elicitation SEP-2322 + A2A
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: A third-party standards client raises AND clears a HITL prompt end-to-end via elicitation / `INPUT_REQUIRED`, and the approval is visible in the existing bespoke queue (one queue, two faces).

### Domain: Standards/MCP (1 tasks)
- **T-217**: STD26-01 -- MCP `2026-07-28` wire adoption  [P2]
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a `2026-07-28` MCP client connects over Streamable-HTTP, reads structured tool output and the Server Cards, and successfully elicits a response; the legacy stdio client still connects.

### Domain: Storage/CephMirror (1 tasks)
- **T-834**: Asynchronous Ceph snapshot mirroring daemon and multi-node recovery manager in mios-ceph-mirror
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Mirroring daemon replicates incremental snapshot deltas and executes 1-click disaster recovery.

### Domain: Storage/CephMirrorTest (1 tasks)
- **T-835**: Automated 15-minute snapshot replication, delta sync, and 1-click failover test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates incremental snapshot delta replication, sub-5s failover, and exact data parity.

### Domain: Storage/CephSnapTest (1 tasks)
- **T-795**: Automated CephFS snapshot creation (<10ms), retention rotation, and rollback test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond snapshot creation, data integrity restoration, and automated pruning.

### Domain: Storage/CephSnapshot (1 tasks)
- **T-794**: Atomic CephFS subvolume snapshot scheduler and instant rollback daemon in mios-ceph-snap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Snapshot manager takes atomic subvolume snapshots in <10ms and restores workspaces instantaneously.

### Domain: Storage/Encryption (1 tasks)
- **T-521**: Multi-domain independent LUKS2/fscrypt partition segregater and inert snapshot export tool
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Storage segregater enforces independent per-domain encryption and exports inert encrypted snapshots.

### Domain: Storage/IoUringSQPOLL (1 tasks)
- **T-840**: Dedicated in-kernel io_uring SQPOLL thread manager and registered buffer allocator
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Storage engines process I/O asynchronously via in-kernel io_uring SQPOLL threads.

### Domain: Storage/IoUringTest (1 tasks)
- **T-841**: Automated 1,000,000 IOPS random I/O benchmark and zero-syscall SQPOLL test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates microsecond storage latency, million-IOPS throughput, and syscall elimination.

### Domain: Storage/LockTest (1 tasks)
- **T-492**: Cross-platform concurrent write and lock contention test suite in QEMU
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates cross-platform file locking integrity in virtualized integration runs.

### Domain: Storage/Performance (1 tasks)
- **T-088**: STRG-05 -- CephFS Client-Side Caching Tuning
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `/etc/ceph/ceph.conf` shows the rendered `[client]` block after firstboot, steady-state GNOME login measures under 500 MDS ops/s, `cachefilesd.service` is active with `fsc` visible in `findmnt` output, and `ceph config get client client_reconnect_stale_interval` returns 30.

### Domain: Storage/Virtiofs (1 tasks)
- **T-491**: virtiofsd POSIX/OFD lock translation and cache policy configurator
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Virtiofs daemon translates guest file lock requests to host OFD locks deterministically.

### Domain: Stream 16kHz microphone audio through Silero VAD into quantized Conformer ONNX for sub-100ms word emission. (1 tasks)
- **AGY-2335**: Streaming CTC / Conformer ONNX speech recognition daemon and VAD chunker in mios-asr  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Streaming ASR engine emits partial transcribed words over socket with sub-100ms latency.
  - *Why:* Streaming low-latency ASR enables fluid conversational voice interaction with local AI agents.

### Domain: Stream OpenAI-compatible SSE token deltas with TCP_NODELAY and adaptive backpressure for <1ms latency. (1 tasks)
- **AGY-2345**: Zero-copy SSE/WebSocket token streamer and TCP_NODELAY socket flusher in agent-pipe  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Agent gateway streams individual token deltas over SSE with immediate TCP flushing.
  - *Why:* Zero-copy immediate socket flushing eliminates streaming stutter and delivers instant perceived AI responses.

### Domain: Stream async optimizer checkpoints to NVMe and resume pre-empted fine-tuning jobs via TorchElastic. (1 tasks)
- **AGY-2267**: Asynchronous non-blocking PyTorch checkpoint engine and TorchElastic preemption manager  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Elastic training engine streams async checkpoints and resumes training automatically after preemption.
  - *Why:* Asynchronous checkpointing and elastic resumption protect long model fine-tuning runs from unexpected system restarts.

### Domain: Stream cold KV blocks asynchronously across VRAM, pinned RAM, and NVMe via io_uring to enable 1M+ contexts. (1 tasks)
- **AGY-2484**: Tiered PagedAttention KV-cache offloader (VRAM/RAM/NVMe via io_uring) in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine offloads and prefetches tiered KV blocks across VRAM, RAM, and NVMe seamlessly.
  - *Why:* Tiered KV-cache offloading enables massive 1M+ document analysis on standard workstation hardware.

### Domain: Stream live agent thought tokens, tool calls, and step status over WebSockets to dashboards and consoles. (1 tasks)
- **AGY-2116**: Authenticated WebSocket real-time agent execution token stream (/v1/events/ws)  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: WebSocket endpoint streams real-time execution events with sub-50ms latency.
  - *Why:* Streaming agent telemetry provides full visibility into agent reasoning and tool executions for UI dashboards.

### Domain: Stream live microphone audio over WebRTC to local Whisper with real-time text token emission. (1 tasks)
- **AGY-2131**: Low-latency WebRTC streaming audio ingress and streaming Whisper speech-to-text bridge  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Streaming STT engine transcribes microphone audio in real time with sub-150ms token latency.
  - *Why:* Real-time streaming speech-to-text enables natural, interactive voice conversations with the OS brain.

### Domain: Stream model layers from pinned host RAM and page inactive conversation KV-caches to system memory dynamically. (1 tasks)
- **AGY-2227**: Dynamic host RAM layer swapping and LRU KV-cache paging manager in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Llama-swap streams model weights and pages conversational KV-caches dynamically without OOM.
  - *Why:* Dynamic VRAM offloading and KV-cache paging allow consumer GPUs to host multiple large models concurrently.

### Domain: Stream node journald logs over WireGuard mesh to central PostgreSQL cluster_logs table with local ring buffering. (1 tasks)
- **AGY-2257**: Fluent Bit encrypted mesh log forwarder and central PostgreSQL cluster sink  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Fluent Bit streams node telemetry to central PostgreSQL sink with network partition buffering.
  - *Why:* Centralized encrypted log aggregation gives operators and autonomous agents a unified cluster-wide diagnostic pane.

### Domain: Switch to secondary interfaces on primary hardware failure and display actionable remediation alerts. (1 tasks)
- **AGY-2130**: Automated network and audio fallback manager with operator desktop alert daemon  (WS-NET | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Hardware fallback manager routes traffic to secondary devices and alerts operator automatically.
  - *Why:* Automated fallback ensures users retain system connectivity and diagnostics even when specific hardware lacks drivers.

### Domain: Synchronize cluster clocks with sub-microsecond PTP hardware timestamps and smooth NTS slewing. (1 tasks)
- **AGY-2163**: PTP IEEE 1588 hardware timestamping and Chrony NTS smooth clock synchronization daemon  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Time sync service maintains sub-microsecond clock synchronization and smooth slew rates.
  - *Why:* Monotonic high-precision clocks are critical for distributed Raft consensus, eBPF telemetry, and Merkle audit chains.

### Domain: Synchronize commits concurrently between GitHub and local Forgejo with safe divergence handling. (1 tasks)
- **AGY-2082**: Bi-Directional Dual-Remote Git Synchronization Daemon with Safe Divergence Gate  (WS-GIT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Dual-remote sync daemon replicates commits across GitHub and Forgejo with safe conflict gating.
  - *Why:* Equal-publisher parity guarantees local sovereignty on Forgejo while maintaining public open-source release on GitHub.

### Domain: Synthesize 24kHz PCM audio chunks in parallel via Kokoro/Piper ONNX and achieve <50ms playback latency. (1 tasks)
- **AGY-2285**: Streaming Kokoro / Piper ONNX speech synthesis engine and PipeWire ring buffer feeder  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: TTS engine streams audio chunks into PipeWire with sub-50ms latency on local hardware.
  - *Why:* Zero-latency streaming TTS makes voice conversations with the agent feel instantaneous and natural.

### Domain: Synthesize OCI container images in rootless Podman and generate machine-readable SPDX SBOMs. (1 tasks)
- **AGY-2107**: Hermetic multi-stage Podman OCI image synthesis and Syft SBOM generation pipeline  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Build pipeline compiles OCI image and generates verifiable SPDX SBOM automatically.
  - *Why:* Cryptographic SBOMs guarantee supply-chain transparency and enable automated vulnerability scanning.

### Domain: Synthesize and stream voice audio concurrently as LLM text tokens arrive with sub-300ms time-to-sound. (1 tasks)
- **AGY-2132**: Concurrent streaming Piper/Kokoro TTS audio synthesis and PipeWire buffer feeder  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Concurrent TTS engine streams synthesized voice audio concurrently with token generation.
  - *Why:* Concurrent sentence-level TTS synthesis delivers human-fluid voice conversation with zero perceptible lag.

### Domain: Synthesize cBPF filter trees per sandbox profile to block unauthorized syscalls in <100us via SECCOMP_RET_ERRNO. (1 tasks)
- **AGY-2508**: Dynamic seccomp-bpf syscall filter synthesizer and user-notification gate in mios-seccomp-gen  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Security synthesizer compiles and attaches seccomp-bpf filter trees in <100us.
  - *Why:* Dynamic seccomp-bpf filtering prevents untrusted scripts from attacking the kernel or escalating privileges.

### Domain: Take atomic CephFS .snap/ snapshots in <10ms, rotate retention, and roll back workspaces instantaneously. (1 tasks)
- **AGY-2392**: Atomic CephFS subvolume snapshot scheduler and instant rollback daemon in mios-ceph-snap  (WS-STRG | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Snapshot manager takes atomic subvolume snapshots in <10ms and restores workspaces instantaneously.
  - *Why:* Instantaneous point-in-time snapshots protect against agent workspace corruption and accidental data deletion.

### Domain: The 109 cannot become 110. (1 tasks)
- **AGY-1851**: Nothing prevents a new unpinned text write from being added  (WS-HOSTDEP | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: adding an unpinned text write fails the gate.
  - *Why:* a cleanup with no gate behind it regrows.

### Domain: The DB-seed coverage gate can report an unseeded section. (1 tasks)
- **AGY-1936**: check_db_seed_coverage compares the SSOT against a copy of itself  (WS-GATE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: appending an unhandled section to mios.toml turns the check red, and removing it turns it green.
  - *Why:* a gate that compares an input against a function returning that input is the tree's signature defect, and this one has a negative test that has been telling us so in every CI run.

### Domain: The SBOM describes the image it ships with. (1 tasks)
- **AGY-1932**: SBOM records exist but are not verified against the image  (WS-SBOM | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: an SBOM that disagrees with the image fails the build.
  - *Why:* an SBOM that is generated from what shipped can never disagree with what shipped.

### Domain: The account model has a working first implementation. (1 tasks)
- **AGY-1921**: Database-backed accounts ship inert with no path to active  (WS-ACCT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: an account declared in the database resolves through the system name service on Linux.
  - *Why:* an inert key is a promise; the Linux leg is the part that can be made real now.

### Domain: The collaboration rules are enforced by tooling, not by recall. (1 tasks)
- **AGY-1726**: Make the shared-tree rules mechanical rather than remembered  (WS-PROCESS | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the hook is installed by the standard setup path and refuses each of the three shapes, with an override that has to be typed deliberately.
  - *Why:* these three cost a whole session's rework, and every one of them is mechanically detectable before the commit that ships it.

### Domain: The combined pushed state is under 100 MB. (1 tasks)
- **AGY-1628**: Get the pushed repo state under 100 MB  (WS-THESIS | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the pushed state is under 100 MB, every removed asset is reproducibly fetchable at build with its checksum recorded, and the size floor is tightened.
  - *Why:* size is a correctness property here: the repository is the artifact being read.

### Domain: The compositor configuration derives from the SSOT. (1 tasks)
- **AGY-1928**: The desktop shell effects are hardcoded rather than projected  (WS-DESKTOP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: changing an effect value in the SSOT changes the live compositor configuration.
  - *Why:* a hand-written compositor config is a hand-maintained surface in the most visible part of the product.

### Domain: The conformance check compares against a fixed baseline. (1 tasks)
- **AGY-1828**: The golden-master conformance test diffed the tree against a copy of itself  (WS-GATE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: changing a templated file without updating its golden fails.
  - *Why:* it is the clearest instance of a check structurally incapable of failing.

### Domain: The cross-platform dotfiles claim is proven on more than one application. (1 tasks)
- **AGY-1875**: The dotfiles registry has one proven surface  (WS-SSOT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: at least three surfaces project settings on both platforms and are gated.
  - *Why:* one proof point does not establish a cross-platform mechanism.

### Domain: The daemon that runs the drift checks proves it runs them. (1 tasks)
- **AGY-1800**: Give miosd tests, starting with the check registry that decides every verdict  (WS-LANG | P0 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: miosd has tests over the registry, the regenerate-and-diff primitive and the bake plan, and is removed from `[rust.untested_crates]`.
  - *Why:* an untested check runner can report a pass it never observed, and every drift verdict in CI passes through it.

### Domain: The development host can verify the layer it edits. (1 tasks)
- **AGY-1863**: Windows cannot build the Rust workspace at all  (WS-HOSTDEP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `cargo test --workspace` completes on a documented Windows setup, or the desktop crates are excluded with the exclusion stated.
  - *Why:* the Rust layer went unverified for a whole session because no available toolchain worked.

### Domain: The development host runs the system it builds. (1 tasks)
- **AGY-1734**: Make MiOS-DEV run MiOS itself and record what the cutover needed  (WS-VARIANT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the distro boots MiOS, systemd reaches a running state, and its Quadlet containers start.
  - *Why:* a development host that cannot run the image it produces cannot tell you the image is broken.

### Domain: The dispatch in `main()` is covered like the checks it calls. (1 tasks)
- **AGY-1820**: The gate's own runner has no test  (WS-GATE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: adding a `check_*` function without wiring it into `main()` fails.
  - *Why:* the tree already contained a module subcommand that nothing called; this is the same shape one level up.

### Domain: The documented curl-pipe entry point either works or is gone. (1 tasks)
- **AGY-1759**: Resolve the root redirector that points at nothing  (WS-DEPLOY | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every documented entry point resolves, or is no longer documented.
  - *Why:* it carries an installer role marker and a curl-pipe docstring, so it reads as a supported way in.

### Domain: The drift register empties. (1 tasks)
- **AGY-1831**: 55 declared units are registered as drifting from their projection  (WS-UNITS | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the register is empty and faithful equals declared.
  - *Why:* 55 units that do not regenerate is the concrete form of part 1 of the thesis being unproven.

### Domain: The exemption list shrinks as the reasons are removed. (1 tasks)
- **AGY-1719**: Re-run the exempted suites and lower [ci].max_exempt_suites to what remains  (WS-CI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the ceiling equals the number of exemptions and every remaining entry states why it can never join a tier.
  - *Why:* an exemption list with a ceiling above its count is a list that can grow quietly, which is how thirteen suites went unrun.

### Domain: The gaming edition is a measured difference, not a colour. (1 tasks)
- **AGY-1736**: Prove MiOS-Xbox differs from MiOS in the ways it claims  (WS-VARIANT | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a test names each declared difference and fails when the built artifact does not carry it.
  - *Why:* an edition is a promise about output; unverified, it is a promise about intent.

### Domain: The gate compares projected image size to the SSOT budget it names. (1 tasks)
- **AGY-1769**: Make the bake-budget gate measure size  (WS-GATES | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: lowering the SSOT budget below the measured total turns the gate red, and raising it above turns it green.
  - *Why:* it advertises a guard over the exact publish-capacity failure that has already blocked this project, while the operator-facing knob is decorative.

### Domain: The gate stays fast enough that people run it. (1 tasks)
- **AGY-1638**: Audit the drift gate's runtime and parallelise the census  (WS-EVIDENCE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the full gate's wall-clock is measured, the census is computed once, and the improvement is recorded.
  - *Why:* a gate too slow to run locally becomes a gate that only CI runs, which pushes every failure into a round trip.

### Domain: The hypervisor-host design is demonstrated at the smallest useful scale. (1 tasks)
- **AGY-1929**: The split-plane host design has no executable proof  (WS-METAL | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a host boots, passes a GPU through to a guest running the image, and the guest reaches the network over the mesh.
  - *Why:* the design is currently observation-free, and the roadmap says blade and mesh behaviour is design rather than observation.

### Domain: The image that publishes is shown to boot and serve, not merely to build. (1 tasks)
- **AGY-1731**: Validate the pulled image end to end on MiOS-DEV  (WS-DEPLOY | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a boot from this image is recorded, including every unit that did not start.
  - *Why:* every deployment claim in the documentation is still a design claim; this is the first chance to make one an observation.

### Domain: The kickstart and the image archive are on the stick, at the paths the boot entry names. (1 tasks)
- **AGY-1754**: Stage the Path-B payload where its own boot entry points  (WS-DEPLOY | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a staged stick carries the kickstart and the archive, and a stager run that cannot stage them fails.
  - *Why:* the immutable install is fully written and has never had its inputs delivered to the medium.

### Domain: The label gate reads the SSOT or fails. (1 tasks)
- **AGY-1766**: Stop the partition-label gate substituting a literal for the SSOT  (WS-GATES | P0 | S)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: removing or renaming `[cat.repo_partition]` turns the gate red.
  - *Why:* it will report green through the entire variant rename it exists to police.

### Domain: The metal-owning variant exists as something you can boot. (1 tasks)
- **AGY-1735**: Give MiOS-Metal a built artifact so it stops being a design  (WS-VARIANT | P2 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the artifact builds, boots headless, and binds the declared devices to vfio.
  - *Why:* a variant that builds nothing is a document with a table of contents entry.

### Domain: The metric measures authored shell, not SSOT size. (1 tasks)
- **AGY-1856**: The legibility ratchet counts generated shell against a "bash is glue" limit  (WS-HOSTDEP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: both figures are reported and ratcheted separately, and declaring a unit moves only the generated one.
  - *Why:* a metric that penalises the roadmap's own goal will eventually be raised or ignored, and both outcomes lose the ratchet.

### Domain: The mobility model in ADR-0017 exists in code, not only in a decision record. (1 tasks)
- **AGY-1624**: Implement blade workload mobility per ADR-0017  (WS-BLADE | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a two-node fleet demonstrates a container failing over under k3s and a VM under Pacemaker, with the dwell behaviour observed and the merge rules exercised including a `conflict-is-error` case.
  - *Why:* `[blade.*]` currently declares behaviour nothing implements, which `check_no_inert_ssot_tables` should be catching.

### Domain: The native node executes Wasm micro-tasks on-device under a fuel budget. (1 tasks)
- **AGY-2577**: Fuel-metered Wasm engine in the native mios-node crate with interpreter fallback  (WS-NODE-ANDROID | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A fuel-metered module runs on-device, exhausting fuel terminates it, and the interpreter path is covered by a test.
  - *Why:* The WS-NODE NODE-02 entry already claims Wasmtime integration that the crate does not contain.

### Domain: The native runner does not certify the deploy plane it never inspects. (1 tasks)
- **AGY-1768**: Replace six hardcoded Rust passes and the parity harness that hides them  (WS-GATES | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each native check either inspects the tree or declares itself skipped, and a disagreement between the two runners is an error.
  - *Why:* six checks named after the deploy plane's most broken surfaces return a literal string.

### Domain: The offline medium carries the weights it promises, or the promise is withdrawn. (1 tasks)
- **AGY-1776**: Carry the models, or stop claiming the medium does  (WS-DEPLOY | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a staged medium either contains the declared weights at a path the heavy lane reads, or the SSOT stops declaring them.
  - *Why:* an unreachable second half of a build script is dead code that reads as coverage, and the medium's stated purpose includes the weights.

### Domain: The offline-install invariant is asserted against executable code. (1 tasks)
- **AGY-1767**: Stop a comment satisfying the offline-install gate  (WS-GATES | P0 | S)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: gutting the installer body turns the gate red, and a network call anywhere in the offline path is a violation.
  - *Why:* this is the gate the entire offline claim rests on, and it currently reads a docstring.

### Domain: The operator can select the bootc install from the boot menu. (1 tasks)
- **AGY-1755**: Put the immutable-install entry in the menu Ventoy actually loads  (WS-DEPLOY | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: booting the medium shows an "Install MiOS (Immutable bootc)" entry that loads.
  - *Why:* two locks on one door -- the payload is missing and the menu that would open it is not the menu that loads.

### Domain: The out-of-process policy arbiter that already ships is actually on the decision path. (1 tasks)
- **AGY-2580**: Consult the policy arbiter by default instead of shipping it unreachable  (WS-SEC | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: With the arbiter up a dangerous verb is gated by it; with it down the verb is refused; no host allowlist literal remains in server.py.
  - *Why:* An enforcement component nothing consults is indistinguishable from one never written, and the shipped default makes the gate a no-op.

### Domain: The per-class merge rules are proven, including the failure class. (1 tasks)
- **AGY-1635**: Cover the reconcile-blade merge classes with adversarial tests  (WS-BLADE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each merge class has a discriminating test, `conflict-is-error` is proven to raise, and the tests fail if two classes are swapped.
  - *Why:* merge rules that are only tested on agreeing inputs are untested.

### Domain: The plan's images exist and are pullable. (1 tasks)
- **AGY-1637**: Prove the bake plan against a real registry resolution  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a build resolves every image to a digest, records them in the SBOM, and fails loudly rather than silently when the network is absent under `MIOS_DRIFT_REQUIRE_TOOLS`.
  - *Why:* a plan listing an image that cannot be pulled fails at bake time, which is the most expensive place to find out.

### Domain: The portable edition deploys the system it carries. (1 tasks)
- **AGY-1737**: Make MiOS-Cat install MiOS rather than boot beside it  (WS-VARIANT | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a machine booted from the medium installs the carried MiOS image and reboots into it, with the network physically absent.
  - *Why:* the portable edition exists so a machine with no network can become a MiOS machine, and that is the one thing it cannot yet do.

### Domain: The privileged-unit roster is computed from the units, not maintained beside them. (1 tasks)
- **AGY-1842**: Privileged units are declared in the SSOT but the list is not derived  (WS-UNITS | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: granting privilege to an unlisted unit fails a check.
  - *Why:* a hand-maintained security roster drifts silently, and its drift is the failure it exists to prevent.

### Domain: The product name does not shadow a standard command. (1 tasks)
- **AGY-1900**: The portable-media working name collides with a coreutils command  (WS-DEPLOY | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the surface list is complete and a rename can be executed mechanically.
  - *Why:* the name appears in the variants registry, so it is load-bearing rather than cosmetic.

### Domain: The projection cannot emit a file systemd would reject. (1 tasks)
- **AGY-1846**: Nothing checks that a declared unit parses as a systemd unit  (WS-UNITS | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a unit that systemd rejects fails CI.
  - *Why:* a projection validated only against itself proves the renderer is self-consistent, not that it is correct.

### Domain: The publish path's tier split is explicit and checked. (1 tasks)
- **AGY-1909**: Firstboot tier evicts large images and the split is undocumented  (WS-DEPLOY | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the tier assignment is declared and a bake that would exceed capacity fails before it runs.
  - *Why:* the publish path has failed on capacity before, and the recovery was a manual tier decision nobody recorded.

### Domain: The published image has exactly one working OS update mechanism. (1 tasks)
- **AGY-1761**: Ship an image that can update itself  (WS-DEPLOY | P0 | M)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every published image has an enabled OS update timer, and a build that would ship without one fails.
  - *Why:* every machine installed from this image is frozen at install time and nothing anywhere says so.

### Domain: The published number matches the measured one. (1 tasks)
- **AGY-1847**: The unit count in the roadmap contradicts the generator  (WS-UNITS | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the roadmap's unit figure is generated and matches `--check`.
  - *Why:* a roadmap that misstates its own central metric cannot be used to decide what to work on.

### Domain: The reliability numbers the self-improvement loop trusts are measured by CI rather than asserted. (1 tasks)
- **AGY-2581**: Ship real evaluation suites and gate on their scores in CI  (WS-SCHED | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: A scored run executes in CI against a frozen suite with a recorded baseline, and a regression below baseline fails the tier.
  - *Why:* The self-rewrite gate is only as trustworthy as the measurement behind it, and that measurement never runs unattended today.

### Domain: The repository IS the deliverable -- a person should be able to read it and see the idea. (1 tasks)
- **AGY-1606**: Drive the legibility floors down  (WS-THESIS | P2 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: each floor is materially lower with no capability lost, and the PowerShell-to-Rust ratio has inverted for anything that is a program rather than glue.
  - *Why:* an idea nobody can read is not demonstrated. Size is therefore a correctness property here, not hygiene.

### Domain: The second design variant resolves in one direction or the other. (1 tasks)
- **AGY-1738**: Give MiOS-Xbox-Arm an arm64 build or retire the variant  (WS-VARIANT | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: an arm64 artifact exists and boots, or the variant and its edition are gone.
  - *Why:* a declared target nobody builds sets an expectation the project does not meet.

### Domain: The shell linter cannot pass by not being installed. (1 tasks)
- **AGY-1810**: check_shellcheck warns instead of violating when shellcheck is absent  (WS-GATE | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: with shellcheck removed from PATH and `MIOS_DRIFT_REQUIRE_TOOLS=1`, the gate reports a violation; with the variable unset it still warns and passes.
  - *Why:* a linter that reports success when it did not run is the defect class the first open campaign exists to close.

### Domain: The staging area does not become a second manual. (1 tasks)
- **AGY-1685**: Decide what happens to the _harvest area once distilled  (WS-MANUAL | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the end state is decided and gated, with a ratchet that prevents the staging area growing while the narrative count falls.
  - *Why:* moving prose from comments into a directory nobody reads is not documentation, it is relocation.

### Domain: The summary line is actionable without a second command. (1 tasks)
- **AGY-1839**: The unit gate reports its own coverage as a count, not a list  (WS-UNITS | P3 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `--check` names what is undeclared, and says how many it did not name.
  - *Why:* a silent truncation reads as complete coverage, which is a recorded defect class here.

### Domain: The two publishers are provably equal. (1 tasks)
- **AGY-1924**: Both publishers must produce bit-for-bit identical images and it is unverified  (WS-CI | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the same commit produces the same image digest on both, or every difference is declared.
  - *Why:* equal publishers that produce different images means the provenance of a deployed system depends on which forge built it.

### Domain: Thesis part 1 -- a check that cannot fail asserts a proof that does not exist, so a hollow gate does not merely miss bugs, it falsifies the claim that drift is mechanically impossible. (1 tasks)
- **AGY-1602**: Audit every drift-check for falsifiability  (WS-THESIS | P0 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every dispatched check has a negative test that demonstrably fails on an injected defect; `check_negative_coverage` passes with an empty exempt list, or each exemption states why the check is structurally unfalsifiable.
  - *Why:* four hollow checks were found in a single session, three of them shipped green for weeks. The count of undiscovered ones is unknown, which is the problem.

### Domain: Thesis part 1 -- a surface with no generator and no gate is a surface the claim does not cover, and today nothing enumerates them. (1 tasks)
- **AGY-1605**: Prove projection completeness over every shipped file  (WS-THESIS | P1 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: zero UNCLASSIFIED files; the projection registry names a generator and a gate for every generated surface; adding an ungoverned file to the image fails the gate.
  - *Why:* "everything is projected" is currently an assertion about an unenumerated set. Until the set is enumerated the claim is unfalsifiable, which is the same defect as a hollow gate.

### Domain: Thesis part 1 -- systemd is the largest surface in the image, so 39 units that do not regenerate is the biggest single hole in "one file defines the OS". (1 tasks)
- **AGY-1603**: Make all 66 units reproduce from SSOT  (WS-THESIS | P0 | L)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `max_drift` reaches 0 with `check_unit_projection` green, and the golden fixtures are regenerated from SSOT rather than copied from the tree they verify.
  - *Why:* the claim is that the OS is a projection. For 39 units it currently is not, and the gate that should have said so was reporting success without comparing anything.

### Domain: Three default Minis must form one cluster, and today they form three. (1 tasks)
- **AGY-2585**: Derive the k3s role from SSOT and stop shipping a join-less server  (WS-MINI | P0 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: The role derives from SSOT, joiners carry `K3S_URL`, the token is out of the Quadlet, and the hazard retires itself because its cause is gone.
  - *Why:* This is half of T-333's Done-When -- a hazard that must not be reachable by adding a second machine.

### Domain: Throttle background daemon resource consumption dynamically based on live PSI pressure events. (1 tasks)
- **AGY-2084**: Dynamic cgroup v2 cpu.max and memory.high pressure-adaptive controller  (WS-SCHED | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Dynamic cgroup controller restricts background slices under pressure and recovers automatically.
  - *Why:* Enforcing cgroup limits under pressure guarantees that foreground interactive tasks always receive required CPU cycles.

### Domain: Topology/HA (1 tasks)
- **T-991**: MINI-05g -- Pacemaker quorum and fencing: unfenced is a one-node-only privilege
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `stonith-enabled=false` is reachable only while the cluster has exactly one member; an even Blade count spawns a third member and retires it when a Blade joins; adding a second member without a fencing device fails closed with a message naming what is missing; the fence agent acts through the Blade; the filler's placement is explicit; the guard reads the running nodelist; and `pacemaker-unfenced` retires itself from `[blades.hazards].accepted`.

### Domain: Topology/Hypervisor (1 tasks)
- **T-988**: MINI-05d -- The hypervisor plane IS the Blade: declare the boundary and the FOUR role shapes
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the Blade-vs-Edge-vs-Node boundary and all four role shapes are declared in SSOT and enforced by one gate the other lanes consume; a gate fails when a CORE service is placed on a plain hosted Node; `[metal].enabled` can be set on one Blade without implying anything about peers; and every key in `[metal.gpu]` either drives a real binder or is removed with the removal recorded.

### Domain: Topology/Mesh (1 tasks)
- **T-986**: MINI-05b -- The HCI mesh VPN: every Blade a member, no guest a peer
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `headscale` ships as a real gated unit with its SSOT keys wired on both ends, the client is installed from a package rather than a bare repo drop and is present on every Blade, a gate fails when `[metal.mesh]` names a coordinator no unit implements, and a test proves an established tunnel survives the coordinator being stopped.

### Domain: Topology/Orchestration (1 tasks)
- **T-990**: MINI-05f -- k3s server/agent election: one cluster, not N control planes sharing a token
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the role derives from SSOT and the generated Quadlet emits `K3S_URL` for joiners; an even Blade count spawns a third server and retires it when a Blade joins; the generated `nodeSelector`s are actually consumed so CORE workloads land only on Blades and Edge nodes; the token moves out of the Quadlet into `secrets.env`; and `k3s-multi-server` retires itself from `[blades.hazards].accepted` because the detector stops reproducing it.

### Domain: Topology/Radio (1 tasks)
- **T-985**: MINI-05a -- Every Blade is an AP in one mesh Wi-Fi, and no hosted image ever is
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `hostapd` ships as a real gated unit on every Blade rendered from SSOT, channels are assigned non-overlapping across the fleet by a generator rather than by hand, `radio` is unclaimable by any hosted-image archetype, and negative tests prove the gate fails both when a node archetype claims `radio` and when two Blades are handed the same channel.

### Domain: Topology/Router (1 tasks)
- **T-987**: MINI-05c -- Router core: one Blade holds the uplink, all Blades serve
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `router` is a Blade-plane capability, singleton across Blades and unclaimable by any hosted-image archetype; nftables and dnsmasq ship as real gated units generated from SSOT; and negative tests prove the gate fails when a guest claims `router` and when two Blades do.

### Domain: Topology/SSOT (7 tasks)
- **T-328**: BLADE-06 -- The seat-floor opt-in, and the OR-gate the activation axis lacks
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: a seat with `FEATURES=seat-floor` in `/etc/mios/role.conf` starts `mios-llm-light` and nothing else it did not start before; a seat without it starts exactly the 6 units it does today; every serving archetype is byte-for-byte unaffected; and the generated comparison counts the floor lane so `metal-vs-hosted.md` stops saying a seat has zero lanes in every configuration.
- **T-329**: BLADE-07 -- blade_reachability_critical was emitted, described in docs, and read by nothing
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: met for the reachability half. `[blade].min_peer_version` -- the other half of D8, making seat/blade upgrade skew visible -- is NOT built and is tracked here.
- **T-331**: MINI-03 -- MiOS-Metal is the BOX; the tree said it was the seat, and shipped that
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the naming correction is landed everywhere (**done** in this change); `[blades]` describes a 2-6 node fleet with a stated quorum rule; and each capability above is either implemented behind a capability gate or carries its own task saying it is not. A gate asserting no doc claims a capability the tree lacks would close the class -- that is what let D9 ship a false claim.
- **T-333**: MINI-05 -- Every capability a MiOS-Metal is defined by is single-node or absent
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: each lane has its own task with a stated target shape for 2-6 nodes, and the two that are dangerous rather than merely missing -- unfenced multi-node Pacemaker, and k3s-server-on-every-controller -- are gated so they cannot be reached accidentally by adding a second machine.
- **T-335**: MINI-07 -- "Offload" means SHED, not thin; and the live mesh (Tailscale) is not installed
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: D9 states the operator's definition (**done**); the generated comparison stops claiming to define MiOS-Metal (**done**); Tailscale is BAKED rather than repo-dropped, with a unit and an SSOT key, so a Mini can reach its mesh without first reaching the network; the radio floor is expressed; and the split-plane doc says whether "Mini" is the host plane or the whole box.
- **T-337**: MINI-08 -- The router plane is further along than reported; three more decorative key families
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the firewall init script is either invoked or deleted; `[network]` is read by its consumer or retired; `[metal]`'s env files are consumed or the generators stop writing them; the two `MIOS_METAL_*` spellings are reconciled; and `NetworkManager-wifi` moves out of `[packages.gnome]` if a headless Mini is to have a radio.
- **T-338**: MINI-09 -- The two products had no declared boundary, so "offload all services" had none either
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: every `owner = "mini"` plane is baked and wired (`radio` and `mesh` are the two open

### Domain: Topology/Storage (1 tasks)
- **T-989**: MINI-05e -- Ceph beyond one MON: an odd monitor count, and an OSD that actually exists
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: `ceph-bootstrap.sh` creates at least one OSD on the block device its Blade presents; the `ConditionVirtualization=no` contradiction is resolved; the MON count is always odd, reached by spawning when the Blade count is even, and the spawned member retires when a Blade joins; a gate fails when an OSD is placed on a plain hosted Node; and the filler's placement is explicit rather than assumed symmetric.

### Domain: Transfer compressed block-level incremental backups to off-site storage targets efficiently. (1 tasks)
- **AGY-2006**: Fast delta snapshot transfer for remote off-site backup synchronization  (WS-DURA | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Remote backup synchronizer transfers incremental deltas with minimal bandwidth consumption.
  - *Why:* Off-site disaster recovery must be bandwidth-efficient to run reliably over residential uplinks.

### Domain: Trigger containerized bootc-image-builder compilation in podman-MiOS-DEV, verify image digest, and stage hot-swap OCI artifacts. (1 tasks)
- **AGY-2564**: Autonomous self-replication daemon and podman-MiOS-DEV build pipeline trigger  (WS-HCI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Self-replication daemon triggers containerized builds and stages verified OCI image digests atomically.
  - *Why:* Self-replication allows the immutable host to rebuild and update its own operating system substrate autonomously.

### Domain: UI/Theme (1 tasks)
- **T-499**: Multi-surface theme renderer with ANSI OSC 4/10/11 PTY injector and GTK/QT CSS generator
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Theme renderer propagates color palette updates across GTK, QT, and active PTYs with zero restarts.

### Domain: UI/ThemeBus (1 tasks)
- **T-500**: Real-time DBus and WebGL wallpaper theme synchronization bus
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Theme broadcast bus synchronizes GNOME settings and living wallpaper shaders in real time.

### Domain: Unpack 16 ternary weights per word via hardware PEXT/PDEP and AVX-512 SIMD for >300 tok/s CPU inference. (1 tasks)
- **AGY-2498**: Parallel bit-manipulating ternary unpacker and fused SIMD accumulator in llama-swap  (WS-AI | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Inference engine executes parallel bit-manipulation ternary unpacking and fused SIMD accumulation at >300 tok/s.
  - *Why:* Hardware-accelerated bit manipulation delivers instant zero-copy ternary unpacking directly in CPU vector registers.

### Domain: Unplugging mid-task loses no write and blocks no merge. (1 tasks)
- **AGY-2578**: Transient-link ledger reconciliation and CRDT type-name correction  (WS-NODE-ANDROID | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Detach, mutate on both sides, reattach: no write lost, no merge blocked; and the type name matches its implementation.
  - *Why:* A USB cable is a transient link by nature, and a CRDT named after an algorithm it does not implement misleads every later reader.

### Domain: Update CDI specs and notify inference daemons of newly available GPU compute lanes dynamically. (1 tasks)
- **AGY-2094**: Zero-downtime CDI re-generation and inference engine live reload daemon  (WS-AI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: CDI specifications update and inference engines recognize hotplugged GPUs with zero session downtime.
  - *Why:* Zero-downtime device updates ensure smooth operator experience when docking or connecting accelerators.

### Domain: Update model endpoint definitions and weights dynamically without restarting the agent-pipe gateway. (1 tasks)
- **AGY-1967**: Hot-reload of model routing tables without dropping active WebSocket and SSE streams  (WS-AI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Routing tables reload dynamically on signal with zero dropped connections or client errors.
  - *Why:* Operator model additions and weight upgrades must not interrupt long-running interactive or background sessions.

### Domain: User/SubUID (1 tasks)
- **T-477**: Deterministic /etc/subuid and /etc/subgid range generator in sysusers automation
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Subordinate UID/GID ranges are generated deterministically with zero collision across user accounts.

### Domain: User/UID1000 (1 tasks)
- **T-964**: Standard Non-System UID 1000 Enforcement & systemd-sysusers Migration Pipeline
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: All user provisioning pathways deterministically assign UID 1000 to mios and systemd user session services start without @system override drop-ins.

### Domain: User/UIDTest (1 tasks)
- **T-965**: Automated UID/GID Range & Systemd User Session Boundary Verification Test Suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates UID 1000 allocation, subuid mapping, and user session service compatibility.

### Domain: Validate candidate daemon patches in a shadow container before promoting to production. (1 tasks)
- **AGY-2139**: Shadow dual-process candidate daemon validator and query mirroring harness  (WS-ORCH | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Shadow testing harness validates candidate daemon patches in isolated namespaces safely.
  - *Why:* Shadow testing catches regressions and unhandled exceptions before candidate code handles production user traffic.

### Domain: Validate newly trained LoRA adapters against canonical regression benchmarks before activation. (1 tasks)
- **AGY-2086**: Automated LoRA adapter benchmark evaluator and catastrophic forgetting guard  (WS-AI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Benchmark evaluator gates adapter deployment on regression-free evaluation passes.
  - *Why:* Preventing catastrophic forgetting ensures that domain fine-tuning does not degrade general reasoning abilities.

### Domain: Vendored content is identified, versioned and justified. (1 tasks)
- **AGY-1912**: Vendored assets are two thirds of the tracked size and unaudited  (WS-PROJ | P3 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every vendored asset has provenance recorded and a check asserts it.
  - *Why:* vendored code is code the project ships and does not review.

### Domain: Verify Merkle tree hash continuity and signature validity across agent execution records. (1 tasks)
- **AGY-2152**: Automated audit chain cryptographic verification and tamper-detection validator  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Audit verifier validates Merkle chain continuity and detects simulated log tampering accurately.
  - *Why:* Continuous audit verification guarantees integrity of historical agent decisions and compliance provenance.

### Domain: Verify container storage directories enforce strict POSIX ACL permissions preventing cross-user snooping. (1 tasks)
- **AGY-2076**: POSIX ACL and user namespace validator in greenboot pre-flight checks  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Greenboot validates container storage ACLs and subordinate namespace isolation on every boot.
  - *Why:* Broken filesystem ACLs compromise container isolation and expose private user data across tenant boundaries.

### Domain: Verify emergency recovery passphrases can restore sealed secrets when TPM unsealing fails. (1 tasks)
- **AGY-2092**: Offline split-key emergency recovery and TPM unseal failure test suite  (WS-SEC | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Emergency recovery tool successfully restores sealed vault data following simulated TPM lockouts.
  - *Why:* Robust emergency recovery ensures operators can regain access to their data if motherboard firmware is updated.

### Domain: Verify in automated CI that .mios queries resolve internally and zero unencrypted DNS leaks occur. (1 tasks)
- **AGY-2296**: Automated split-DNS query routing, .mios local resolution, and DoT leak prevention test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates split-DNS domain isolation, zero hostname leakage, and strict DoT encryption.
  - *Why:* Continuous testing ensures network resolver configurations prevent DNS leakage across cluster blades.

### Domain: Verify in automated CI that 1,500 concurrent swarm tasks consume <=16,000MB memory and circuit breaker triggers on overflow. (1 tasks)
- **AGY-2571**: Automated 1,500-task swarm concurrency memory bounding (<16GB) test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates 1,500-task concurrency capacity and proactive OOM circuit breaker triggering.
  - *Why:* Continuous testing ensures multi-agent swarm scalability optimizations preserve strict workstation memory limits.

### Domain: Verify in automated CI that 10 concurrent subagent worktrees merge and clean up with 0 leftover artifacts. (1 tasks)
- **AGY-2202**: Automated subagent worktree creation, merge, and scratch cleanup test suite  (WS-GIT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates subagent worktree isolation, merging, and zero-residual cleanup.
  - *Why:* Continuous testing ensures autonomous agents do not leak temporary files or lock git working trees.

### Domain: Verify in automated CI that 10,000 speculative branch pruning cycles cause 0 bytes of memory leakage. (1 tasks)
- **AGY-2334**: Automated 16-branch speculative tree pruning, zero VRAM leak, and compaction benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates zero VRAM memory leakage and sub-20us branch compaction latency.
  - *Why:* Continuous testing ensures speculative tree attention optimizations remain leak-free over long-running sessions.

### Domain: Verify in automated CI that 100 concurrent SSE streams deliver token chunks in <1ms without buffer bloat. (1 tasks)
- **AGY-2346**: Automated 100-stream concurrent token chunk latency (<1ms) and backpressure benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-1ms token chunk dispatch and robust backpressure handling across 100 concurrent streams.
  - *Why:* Continuous testing ensures streaming inference gateways maintain real-time responsiveness under high client concurrency.

### Domain: Verify in automated CI that 100 microVMs boot concurrently in <15ms each from a single SquashFS NBD export. (1 tasks)
- **AGY-2405**: Automated 100-microVM concurrent boot latency (<15ms) and shared SquashFS NBD test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates instant microVM concurrency, template sharing, and isolated RAM overlay execution.
  - *Why:* Continuous testing ensures virtualization storage pipelines maintain ultra-fast provisioning and zero disk degradation.

### Domain: Verify in automated CI that 100% memory exhaustion evicts worker cgroups in <5s with 0 system daemon crashes. (1 tasks)
- **AGY-2419**: Automated memory exhaustion stress test, worker eviction, and daemon survival test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates targeted subagent eviction, zero system service degradation, and forensic audit logging.
  - *Why:* Continuous testing ensures memory protection policies reliably prevent system lockups during peak AI loads.

### Domain: Verify in automated CI that 100% of function entry points carry landing pads and illegal jumps are trapped in <5ns. (1 tasks)
- **AGY-2561**: Automated IBT/BTI illegal jump trapping (<5ns) and binary landing pad test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates landing pad opcode presence, hardware exception trapping, and minimal CPU overhead.
  - *Why:* Continuous testing ensures hardware-enforced control-flow integrity instructions are uniformly emitted across all binaries.

### Domain: Verify in automated CI that 100% of return instructions carry post-branch INT3/ISB traps and overhead is <0.3%. (1 tasks)
- **AGY-2541**: Automated SLS post-return trap verification (<5ns barrier) and disassembly test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates post-branch trap opcodes on all unconditional jumps, zero fault rate, and minimal overhead.
  - *Why:* Continuous testing ensures compiler toolchains consistently emit speculative execution traps across all architecture targets.

### Domain: Verify in automated CI that 100,000-token generation maintains stable perplexity (<15.0) and 0 OOM errors. (1 tasks)
- **AGY-2354**: Automated 100,000-token infinite streaming perplexity stability and zero-OOM test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates stable perplexity and constant memory bounds across 100k generated tokens.
  - *Why:* Continuous testing ensures attention sink eviction mechanisms preserve language modeling quality over long runs.

### Domain: Verify in automated CI that 16GB allocations use 2MB pages with <1ms allocation latency and zero TLB stalls. (1 tasks)
- **AGY-2399**: Automated 2MB/1GB huge page allocation, sub-1ms allocation latency, and TLB benchmark suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates instant huge page allocation, high coverage ratio, and low TLB miss rate.
  - *Why:* Continuous testing ensures memory management configurations preserve peak memory bandwidth for large AI workloads.

### Domain: Verify in automated CI that 192kHz audio streams maintain exact sample rates and mixing never causes XRuns. (1 tasks)
- **AGY-2302**: Automated 192kHz/24-bit bit-perfect audio stream verification and concurrent mixing test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates dynamic clock rate switching and glitch-free concurrent audio mixing.
  - *Why:* Continuous testing ensures audio subsystem updates preserve bit-perfect fidelity and mixer stability.

### Domain: Verify in automated CI that 1M token context offloads to NVMe in <2ms per block with 0 OOM crashes. (1 tasks)
- **AGY-2485**: Automated 1M token context offloading, sub-2ms swap latency, and zero-crash test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates massive context support, asynchronous NVMe swapping, and 100% retrieval accuracy.
  - *Why:* Continuous testing ensures memory tiering pipelines reliably expand context limits without risking runtime crashes.

### Domain: Verify in automated CI that 20 concurrent subagent workspaces maintain 100% data isolation and merge safely. (1 tasks)
- **AGY-2290**: Automated 20-subagent concurrent file mutation and atomic git diff promotion test suite  (WS-BUILD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-concurrency subagent isolation and conflict-free patch promotion.
  - *Why:* Continuous testing ensures agent workspace scaling maintains reliable concurrent software development.

### Domain: Verify in automated CI that 2:4 sparse models achieve >1.8x matrix speedup and retain >99.2% code accuracy. (1 tasks)
- **AGY-2411**: Automated 2x Sparse Tensor Core throughput speedup and 2:4 pruning accuracy benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >1.8x matrix acceleration, Sparse Tensor Core execution, and high coding accuracy.
  - *Why:* Continuous testing ensures 2:4 structural sparsity kernels maintain hardware acceleration without degrading code quality.

### Domain: Verify in automated CI that 32B Q4_K_M/Q5_K_M models fit in <16GB VRAM and perplexity delta is <0.03. (1 tasks)
- **AGY-2372**: Automated 32B model VRAM fitting (<16GB) and perplexity parity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates strict VRAM fitting bounds, execution stability, and near-FP16 perplexity.
  - *Why:* Continuous testing ensures quantization profiles maintain high language reasoning fidelity within tight hardware constraints.

### Domain: Verify in automated CI that 4K WebRTC stream achieves 60fps with latency <16ms and CPU load <2%. (1 tasks)
- **AGY-2445**: Automated 60fps 4K WebRTC streaming latency (<16ms) and zero-copy DMA-BUF test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates 60fps frame rates, sub-16ms streaming latency, and zero-copy GPU pipeline execution.
  - *Why:* Continuous testing ensures video streaming components preserve ultra-low latency without CPU degradation.

### Domain: Verify in automated CI that 70B AQLM fits in <16GB VRAM and wikitext-2 perplexity delta is <0.03. (1 tasks)
- **AGY-2469**: Automated 70B AQLM VRAM fitting (<16GB), lookup speed, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-16GB VRAM residency, fast codebook lookup throughput, and low perplexity degradation.
  - *Why:* Continuous testing ensures additive vector quantization algorithms preserve accuracy at extreme sub-2-bit compression levels.

### Domain: Verify in automated CI that 70B AQLM fits in <18.5GB VRAM, achieves >3.5x compression, and perplexity delta <0.025. (1 tasks)
- **AGY-2551**: Automated 2-bit AQLM 18.2GB VRAM fitting, 3.6x speedup, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-18.5GB residency, fast codebook lookup, and high perplexity retention.
  - *Why:* Continuous testing ensures additive multi-codebook vector quantization maintains stable memory usage and exact numerical precision.

### Domain: Verify in automated CI that 70B BiLLM fits in <11GB RAM, achieves >250 tok/s on CPU, and perplexity delta <0.04. (1 tasks)
- **AGY-2463**: Automated 70B BiLLM RAM fitting (<11GB), 250 tok/s CPU throughput, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates strict sub-11GB RAM fitting, >250 tok/s CPU throughput, and low perplexity degradation.
  - *Why:* Continuous testing ensures 1-bit binarization algorithms maintain high reasoning fidelity and extreme speed on consumer hardware.

### Domain: Verify in automated CI that 70B BitNet fits in <14GB RAM, achieves >200 tok/s on CPU, and reduces energy by 10x. (1 tasks)
- **AGY-2403**: Automated 70B BitNet RAM fitting (<14GB), 200 tok/s CPU speedup, and energy benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates strict RAM fitting bounds, >200 tok/s CPU throughput, and 10x energy efficiency.
  - *Why:* Continuous testing ensures BitNet integer kernel updates preserve peak token speeds and minimal energy footprints.

### Domain: Verify in automated CI that 70B EXL2 fits in <24GB VRAM, generates >100 tok/s, and maintains <0.04 perplexity delta. (1 tasks)
- **AGY-2391**: Automated 70B EXL2 model VRAM fitting (<24GB), 100 tok/s speedup, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates strict VRAM fitting bounds, >100 tok/s token throughput, and low perplexity delta.
  - *Why:* Continuous testing ensures EXL2 kernel updates preserve peak token generation speeds and low memory footprints.

### Domain: Verify in automated CI that 70B NVFP4 fits in <18.5GB VRAM, achieves >4.5x speedup, and perplexity delta <0.025. (1 tasks)
- **AGY-2513**: Automated 4.5x FP4 speedup, 18.5GB VRAM fitting, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-18.5GB residency, 4.5x acceleration, and low perplexity degradation.
  - *Why:* Continuous testing ensures FP4 microscaling pipelines maintain maximum hardware acceleration without accuracy loss.

### Domain: Verify in automated CI that 70B QLoRA fits in <24GB VRAM, adapter latency <1ms, and loss convergence = 100%. (1 tasks)
- **AGY-2517**: Automated 70B QLoRA 24GB VRAM fine-tuning, latency (<1ms), and convergence test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-24GB residency, rapid adapter execution, and exact training convergence parity.
  - *Why:* Continuous testing ensures parameter-efficient fine-tuning and adapter execution maintain low resource usage and high fidelity.

### Domain: Verify in automated CI that 70B QuIP# fits in <18GB VRAM and wikitext-2 perplexity delta is <0.030 at 2-bit. (1 tasks)
- **AGY-2479**: Automated 70B QuIP# VRAM fitting (<18GB), FHT-GEMM speedup, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-18GB VRAM residency, fast FHT-GEMM execution, and low perplexity degradation.
  - *Why:* Continuous testing ensures extreme 2-bit vector quantization pipelines maintain high reasoning accuracy.

### Domain: Verify in automated CI that 70B TriLM fits in <14GB VRAM, achieves >3.8x speedup, and perplexity delta is <0.030. (1 tasks)
- **AGY-2527**: Automated 3.8x GPU ternary speedup, 14GB VRAM fitting, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-14GB residency, fast warp-specialized execution, and low perplexity degradation.
  - *Why:* Continuous testing ensures ternary GPU kernels maintain high computational speed and exact numerical stability.

### Domain: Verify in automated CI that AST diffing flags 100% of semantic syntax mutations and merges only on 2/2 approval. (1 tasks)
- **AGY-2379**: Automated AST structural diff calculation and 2-peer review merge gating test suite  (WS-ORCH | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates AST diff precision, cosmetic change filtering, and 2-peer review consensus gating.
  - *Why:* Continuous testing ensures autonomous code merging pipelines maintain high software quality and security.

### Domain: Verify in automated CI that AVX-512 register scrub takes <50ns and prevents 100% of GDS vector register recovery. (1 tasks)
- **AGY-2511**: Automated Downfall/GDS vector register scrub (<50ns latency) and SIMD isolation test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-50ns vector scrubbing, Downfall exploit neutralization, and high compute performance.
  - *Why:* Continuous testing ensures SIMD vector register sanitization remains effective and lightweight across microcode updates.

### Domain: Verify in automated CI that AWQ achieves >3.5x GEMM speedup and retains >99.7% HumanEval code accuracy. (1 tasks)
- **AGY-2443**: Automated 3.5x AWQ matrix speedup, salient channel protection, and coding benchmark test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >3.5x matrix acceleration, salient channel preservation, and high coding accuracy.
  - *Why:* Continuous testing ensures AWQ fused kernel execution delivers maximum speed without compromising reasoning fidelity.

### Domain: Verify in automated CI that BGP VIP routes announce in <1s and BFD detects node failure in <100ms. (1 tasks)
- **AGY-2358**: Automated BGP VIP announcement, sub-100ms ECMP failover, and zero-iptables routing test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates automated BGP peering, ECMP VIP route propagation, and rapid BFD failover.
  - *Why:* Continuous testing ensures Kubernetes networking updates maintain resilient upstream routing and zero downtime.

### Domain: Verify in automated CI that BHI mitigations execute in <150ns and /proc sysfs reports mitigated status. (1 tasks)
- **AGY-2557**: Automated Spectre-BHI mitigation verification (<150ns latency) and /proc test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond BHB clearing, kernel vulnerability reporting, and total Spectre-BHI immunity.
  - *Why:* Continuous testing ensures branch history injection mitigations remain active across microcode and kernel updates.

### Domain: Verify in automated CI that BPF LSM blocks 100% of unauthorized ptrace attempts and logs events in <1ms. (1 tasks)
- **AGY-2441**: Automated container escape blocking, ptrace denial (<1us), and BPF LSM test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates in-kernel LSM denial, microsecond enforcement speed, and complete audit logging.
  - *Why:* Continuous testing ensures kernel security module policies maintain airtight sandboxing across kernel updates.

### Domain: Verify in automated CI that Bcachefs absorbs >10 GB/s writes and migrates blocks without data corruption. (1 tasks)
- **AGY-2360**: Automated Bcachefs tiering burst write throughput (>10 GB/s) and migration test suite  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates Bcachefs burst write performance, transparent migration, and SHA-256 data integrity.
  - *Why:* Continuous testing ensures next-generation filesystem drivers maintain data durability and peak I/O performance.

### Domain: Verify in automated CI that Bi-Attention achieves >5.0x speedup and 100% 1M context needle retrieval. (1 tasks)
- **AGY-2503**: Automated 5x attention speedup, 16x memory reduction, and 1M context needle test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >5x attention acceleration, 16x memory savings, and perfect needle retrieval.
  - *Why:* Continuous testing ensures binary attention approximation algorithms maintain high retrieval accuracy across long context tasks.

### Domain: Verify in automated CI that Bi-LoRA achieves 8x RAM savings, >3.6x speedup, and >99.2% task adaptation accuracy. (1 tasks)
- **AGY-2543**: Automated 8x adapter RAM reduction, 3.6x speedup, and fine-tuning accuracy test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates 8x memory compression, rapid integer forward passes, and high adaptation fidelity.
  - *Why:* Continuous testing ensures binary low-rank adaptation maintains high learning capacity and ultra-low resource usage.

### Domain: Verify in automated CI that BiLLM A1W1 sustains >400 tok/s on CPU, allocates <9.5GB RAM, and uses 0 multipliers. (1 tasks)
- **AGY-2523**: Automated 400 tok/s CPU throughput, multiplier elimination, and RAM fitting test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >400 tok/s CPU decoding speed, zero arithmetic multiplications, and low perplexity degradation.
  - *Why:* Continuous testing ensures fully binarized 1-bit inference pipelines maintain maximum throughput and minimal memory footprints.

### Domain: Verify in automated CI that BitNet A8W1 sustains >350 tok/s on CPU, allocates <12GB RAM, and uses 0 float multipliers. (1 tasks)
- **AGY-2507**: Automated 350 tok/s CPU throughput, multiplier elimination, and RAM fitting test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >350 tok/s CPU decoding speed, zero float multiplications, and low perplexity degradation.
  - *Why:* Continuous testing ensures multiplier-free integer inference pipelines maintain maximum throughput and minimal memory footprints.

### Domain: Verify in automated CI that CPU inference achieves >30 tok/s on AVX-512 systems and zero SIGILL crashes occur. (1 tasks)
- **AGY-2383**: Automated CPU quantized GEMM throughput (>30 tok/s) and SIMD dispatch test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-throughput SIMD vector dispatch, cache tiling efficiency, and architecture compatibility.
  - *Why:* Continuous testing ensures CPU kernel dispatchers maintain peak inference performance across diverse CPU architectures.

### Domain: Verify in automated CI that CPU temperatures stabilize <90°C under continuous 100% stress load. (1 tasks)
- **AGY-2320**: Automated thermal load ramp, EPP frequency stepping, and hysteresis recovery test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates proactive EPP modulation, thermal stabilization, and hysteresis recovery.
  - *Why:* Continuous testing ensures thermal management daemons protect hardware without causing abrupt performance degradation.

### Domain: Verify in automated CI that CUDA Graphs achieve >1.5x token decoding speedup and bit-for-bit parity. (1 tasks)
- **AGY-2308**: Automated CUDA Graph capture latency (<1ms) and token decoding speedup benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates CUDA Graph acceleration and exact mathematical output parity.
  - *Why:* Continuous testing ensures GPU driver and inference updates maintain CUDA Graph replay optimizations.

### Domain: Verify in automated CI that Core Scheduling tags apply in <1us and 0 untrusted tasks co-schedule on SMT siblings. (1 tasks)
- **AGY-2457**: Automated SMT sibling isolation verification (<1us tagging) and core scheduling test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond cookie tagging, strict SMT sibling isolation, and scheduler security guarantees.
  - *Why:* Continuous testing ensures kernel scheduling mitigations remain active and uncompromised across runtime updates.

### Domain: Verify in automated CI that DBQ achieves >350 tok/s on CPU, fits in <18.5GB RAM, and retains perplexity <0.020 delta. (1 tasks)
- **AGY-2559**: Automated 350 tok/s CPU throughput, dual-binary POPCOUNT, and RAM fitting test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >350 tok/s CPU decoding speed, minimal multiplier use, and low perplexity loss.
  - *Why:* Continuous testing ensures double-binarized inference pipelines maintain high computational speed and small memory footprints.

### Domain: Verify in automated CI that DKMS builds test module in <15s and MOK signature passes modinfo verification. (1 tasks)
- **AGY-2364**: Automated out-of-tree module compilation, MOK signature verification, and cache test suite  (WS-BUILD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sandboxed DKMS module compilation, signature validation, and binary caching.
  - *Why:* Continuous testing ensures custom kernel module building remains secure and reliable across kernel updates.

### Domain: Verify in automated CI that DMA-BUF encoding achieves <15ms latency and unapproved streams are blocked. (1 tasks)
- **AGY-2224**: Automated WebRTC zero-copy video encode latency and session authorization test suite  (WS-APP | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates WebRTC encode performance, zero-copy throughput, and portal security gating.
  - *Why:* Continuous testing ensures display server updates do not introduce video lag or bypass screen-sharing permissions.

### Domain: Verify in automated CI that EAGLE-2 achieves >2.5x speedup, draft acceptance rate >80%, and token parity = 100%. (1 tasks)
- **AGY-2495**: Automated 2.5x EAGLE-2 speedup, dynamic draft tree acceptance, and token parity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >2.5x speedup, high draft acceptance rates, and exact output parity.
  - *Why:* Continuous testing ensures feature-level speculative decoding preserves acceleration across diverse reasoning tasks.

### Domain: Verify in automated CI that FP6 KV cache cuts memory by 62.5% and maintains >99.8% reasoning accuracy parity. (1 tasks)
- **AGY-2407**: Automated 62.5% KV memory savings, FP6 reasoning accuracy (>99.8%), and packing benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates 62.5% memory reduction, high reasoning fidelity, and bit-packing alignment.
  - *Why:* Continuous testing ensures intermediate floating-point quantization formats maintain high accuracy across models.

### Domain: Verify in automated CI that FP8 KV cache halves memory usage and degrades perplexity by <0.05. (1 tasks)
- **AGY-2362**: Automated 128k-context FP8 KV capacity (2x) and perplexity parity (<0.05 delta) test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates 50% KV memory savings, 100% retrieval accuracy, and low perplexity delta.
  - *Why:* Continuous testing ensures FP8 attention kernel updates maintain retrieval fidelity over massive context lengths.

### Domain: Verify in automated CI that FlashAttention-3 and CUTLASS achieve >90% of peak theoretical Tensor Core FLOPS. (1 tasks)
- **AGY-2248**: Automated GPU Tensor Core throughput and GEMM dispatch latency benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates Tensor Core FLOPS utilization and low kernel launch latency.
  - *Why:* Continuous testing ensures inference kernel upgrades do not introduce performance regressions.

### Domain: Verify in automated CI that FlashAttention-3 delivers >1,200 TFLOPS and 128k TTFT latency is <10ms. (1 tasks)
- **AGY-2447**: Automated 1,200 TFLOPS attention benchmark, sub-10ms 128k TTFT, and TMA test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >1,200 TFLOPS throughput, sub-10ms 128k prompt prefill, and TMA memory overlapping.
  - *Why:* Continuous testing ensures cutting-edge attention kernels maintain peak hardware acceleration across model updates.

### Domain: Verify in automated CI that GPU compute slices enforce hard memory boundaries and fault isolation. (1 tasks)
- **AGY-2184**: Multi-instance GPU compute isolation and fault boundary verification test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that GPU hardware slices provide complete fault and memory isolation.
  - *Why:* Hardware fault isolation ensures that a crash in background model fine-tuning never takes down interactive OS voice assistance.

### Domain: Verify in automated CI that GPU terminal renders >1,000,000 characters/s with <5ms keystroke latency. (1 tasks)
- **AGY-2326**: Automated terminal glyph rendering throughput and sub-5ms keystroke latency test suite  (WS-APP | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-throughput glyph rendering and sub-5ms keystroke latency.
  - *Why:* Continuous testing ensures terminal configurations maintain ultra-low latency and smooth rendering performance.

### Domain: Verify in automated CI that HQQ quantizes 7B models in <30s with perplexity delta <0.03 and zero dataset deps. (1 tasks)
- **AGY-2423**: Automated sub-30s HQQ model quantization, perplexity parity, and fused GEMM test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates instant calibration-free quantization speed, low perplexity degradation, and fast GEMM execution.
  - *Why:* Continuous testing ensures quantization algorithms provide immediate, high-fidelity compression without dataset friction.

### Domain: Verify in automated CI that HTTPX transport achieves >500 req/s on UDS and parses streaming responses in <20ms. (1 tasks)
- **AGY-2204**: Automated HTTPX async transport, Unix socket adapter, and stream benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates HTTPX connection pooling, stream decoding, and UDS transport performance.
  - *Why:* Continuous testing ensures HTTPX client upgrades do not introduce stream buffering regressions.

### Domain: Verify in automated CI that Hyprland activates direct scanout and living wallpaper consumes <0.5% GPU. (1 tasks)
- **AGY-2377**: Automated Hyprland direct scanout (<1ms latency) and Living Wallpaper render test suite  (WS-APP | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates Hyprland direct scanout, Quickshell initialization, and low-power living wallpaper rendering.
  - *Why:* Continuous testing ensures desktop rendering pipelines maintain ultra-low latency and peak visual fluidity.

### Domain: Verify in automated CI that IBPB barrier applies in <800ns and prevents 100% of branch target poisoning. (1 tasks)
- **AGY-2497**: Automated Spectre v2 BTB mitigation verification (<800ns IBPB) and context-switch test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-800ns barrier execution, branch predictor invalidation, and zero speculative leakage.
  - *Why:* Continuous testing ensures indirect branch barrier mitigations remain active across CPU microcode updates.

### Domain: Verify in automated CI that IMA appraisal blocks modified binaries with EACCES and validates signed files in <50ns. (1 tasks)
- **AGY-2525**: Automated IMA binary appraisal, tampered executable rejection, and latency test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates cryptographic file appraisal, tampered executable denial, and low verification overhead.
  - *Why:* Continuous testing ensures rootfs integrity verification remains active and resilient across kernel upgrades.

### Domain: Verify in automated CI that Intel Arc PagedAttention sustains 30 concurrent streams with >90% VRAM efficiency. (1 tasks)
- **AGY-2368**: Automated Intel Arc PagedAttention concurrency (30 streams) and VRAM utilization test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-concurrency Intel Arc batch capacity and XMX execution correctness.
  - *Why:* Continuous testing ensures Intel GPU drivers and oneAPI optimizations maintain reliable high-density inference.

### Domain: Verify in automated CI that Kangaroo achieves >1.9x speedup, 0MB extra VRAM overhead, and 100% token parity. (1 tasks)
- **AGY-2555**: Automated 1.9x self-speculative speedup, 0MB VRAM overhead, and token parity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >1.9x generation acceleration, zero memory overhead, and exact token parity.
  - *Why:* Continuous testing ensures draftless self-speculative mechanisms maintain maximum acceleration and numerical exactness.

### Domain: Verify in automated CI that L1D flush takes <500ns and prevents 100% of residual cache line snooping. (1 tasks)
- **AGY-2481**: Automated L1TF cache flush latency (<500ns) and context-switch test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond cache flush latency, complete L1D invalidation, and zero side-channel leakage.
  - *Why:* Continuous testing ensures targeted cache flushing mitigations remain active across kernel and virtualization runtime updates.

### Domain: Verify in automated CI that LFENCE barrier executes in <10ns and prevents 100% of Spectre v1 memory leak attempts. (1 tasks)
- **AGY-2501**: Automated Spectre v1 bounds check bypass exploit prevention (<10ns barrier) and SLH test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates nanosecond barrier latency, zero out-of-bounds leak recovery, and minimal runtime overhead.
  - *Why:* Continuous testing ensures compiler and kernel speculation barriers reliably protect memory boundaries against side-channel extraction.

### Domain: Verify in automated CI that Landlock blocks cross-sandbox signals and abstract sockets in <1us. (1 tasks)
- **AGY-2533**: Automated Landlock scoped abstract socket and signal denial (<1us) test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond abstract socket isolation, signal protection, and flawless intra-sandbox IPC.
  - *Why:* Continuous testing ensures inter-process isolation boundaries remain strictly enforced across kernel updates.

### Domain: Verify in automated CI that Landlock negotiates ABI v1..v4, blocks unauthorized ports in <1us, and isolates files. (1 tasks)
- **AGY-2505**: Automated Landlock ABI negotiation, unprivileged network port denial, and file test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates multi-ABI compatibility, microsecond network port denial, and strict directory sandboxing.
  - *Why:* Continuous testing ensures kernel sandbox negotiation reliably protects network and storage resources.

### Domain: Verify in automated CI that Lookahead n-grams achieve >1.8x speedup on code with 0MB extra VRAM. (1 tasks)
- **AGY-2475**: Automated 1.8x code/JSON generation speedup, zero-VRAM overhead, and token parity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >1.8x speedup on structured tokens, zero memory overhead, and exact output parity.
  - *Why:* Continuous testing ensures zero-parameter speculative decoding delivers consistent acceleration on coding workflows.

### Domain: Verify in automated CI that MXFP4 KV cache achieves 4x density and preserves >99.0% attention score parity. (1 tasks)
- **AGY-2370**: Automated 4x context density, MXFP4 attention accuracy (>99.0%), and memory benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates 4x memory density, high attention fidelity, and numerical stability.
  - *Why:* Continuous testing ensures sub-byte microscaling KV caching maintains extreme memory efficiency and numerical precision.

### Domain: Verify in automated CI that MXFP8 achieves >2.75x speedup and retains >99.9% loss convergence on 70B training. (1 tasks)
- **AGY-2547**: Automated 2.8x MXFP8 speedup, dynamic range overflow prevention, and loss test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >2.75x matrix acceleration, automatic dynamic range scaling, and high training convergence.
  - *Why:* Continuous testing ensures OCP microscaling formats reliably preserve gradient accuracy across deep network training.

### Domain: Verify in automated CI that Marlin kernels achieve >3.5x speedup and maintain <0.1 perplexity delta from FP16. (1 tasks)
- **AGY-2356**: Automated multi-format quantization throughput (>3.5x speedup) and perplexity parity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates hardware dequantization acceleration and mathematical precision parity.
  - *Why:* Continuous testing ensures quantization kernel updates maintain peak token speeds without degrading output quality.

### Domain: Verify in automated CI that Marlin kernels achieve >3.5x speedup over FP16 and memory bandwidth utilization >90%. (1 tasks)
- **AGY-2473**: Automated 3.8x Marlin throughput speedup, memory bandwidth, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >3.5x matrix acceleration, >90% memory bus saturation, and low perplexity degradation.
  - *Why:* Continuous testing ensures Marlin kernel dispatching maintains peak hardware utilization across driver updates.

### Domain: Verify in automated CI that Medusa decoding achieves >2.5x speedup and outputs identical tokens to standard sampling. (1 tasks)
- **AGY-2294**: Automated Medusa Tree-Attention throughput (3x) and mathematical token parity benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates Medusa Tree-Attention acceleration and exact output token parity.
  - *Why:* Continuous testing ensures tree attention kernel updates maintain deterministic, high-throughput token generation.

### Domain: Verify in automated CI that Medusa heads achieve >2.0x speedup and 100% token output distribution parity. (1 tasks)
- **AGY-2455**: Automated 2.2x self-speculative speedup, tree attention, and token parity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >2x speedup, tree attention verification correctness, and exact output parity.
  - *Why:* Continuous testing ensures self-speculative decoding algorithms maintain high speedups without changing model outputs.

### Domain: Verify in automated CI that MiOS-USB FIDO2 challenge completes in <10ms and authenticates cluster nodes. (1 tasks)
- **AGY-2553**: Automated MiOS-USB FIDO2 token challenge-response (<10ms) and multi-node auth test suite  (WS-AUTH | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond token challenge verification, multi-node PAM integration, and zero key leakage.
  - *Why:* Continuous testing ensures hardware-bound token authentication remains reliable across host and blade configurations.

### Domain: Verify in automated CI that NCCL AllReduce latency is <50us and TP=2 achieves >1.8x single-GPU throughput. (1 tasks)
- **AGY-2312**: Automated multi-GPU Tensor Parallelism (TP=2/4) throughput and AllReduce latency test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates low AllReduce latency and high multi-GPU Tensor Parallelism scaling efficiency.
  - *Why:* Continuous testing ensures distributed GPU communication parameters remain tuned across library updates.

### Domain: Verify in automated CI that NUMA interleaving achieves >1.8x memory bandwidth over single-node baseline. (1 tasks)
- **AGY-2425**: Automated multi-socket NUMA bandwidth scaling (>400 GB/s) and core pinning test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high aggregate NUMA memory bandwidth, even page distribution, and strict core pinning.
  - *Why:* Continuous testing ensures NUMA tuning scripts maintain optimal memory distribution across complex server topologies.

### Domain: Verify in automated CI that NVFP4 achieves >3.8x GEMM speedup and fits 70B models in <18GB VRAM. (1 tasks)
- **AGY-2437**: Automated 4x matrix throughput speedup, 70B NVFP4 VRAM fitting, and accuracy test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >3.8x matrix acceleration, sub-18GB VRAM residency, and high mathematical reasoning accuracy.
  - *Why:* Continuous testing ensures sub-byte microscaling hardware pipelines maintain extreme throughput and accuracy.

### Domain: Verify in automated CI that OmniQuant optimizes 7B in <15min, achieves >3.5x speedup, and retains >99.4% accuracy. (1 tasks)
- **AGY-2491**: Automated 15-minute OmniQuant optimization, 3.6x speedup, and 3-bit perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates rapid learnable optimization, high GPU speedup, and low 3-bit perplexity degradation.
  - *Why:* Continuous testing ensures differentiable quantization algorithms maintain fast compilation and high numerical fidelity.

### Domain: Verify in automated CI that PAM and SSH reject operations when FIDO2 presence challenge is unacknowledged. (1 tasks)
- **AGY-2190**: Automated FIDO2 user presence challenge and authentication test suite in virtual USB sandbox  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that FIDO2 authentication strictly enforces physical presence challenges.
  - *Why:* Continuous testing ensures PAM security policies cannot be bypassed by automated background attacks.

### Domain: Verify in automated CI that PagedAttention supports 100 concurrent dynamic conversations with 0 fragmentation loss. (1 tasks)
- **AGY-2236**: Automated PagedAttention fragmentation resistance and 100-session concurrency benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-concurrency memory efficiency and zero-fragmentation resilience.
  - *Why:* Continuous testing ensures inference memory algorithms maximize concurrency across multi-agent workflows.

### Domain: Verify in automated CI that Parquet compression achieves >80% reduction and vector queries return in <50ms. (1 tasks)
- **AGY-2198**: Automated journal compaction, Parquet query performance, and vector retrieval benchmark suite  (WS-RAG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates Parquet log compression and semantic diagnostic vector retrieval.
  - *Why:* Continuous testing ensures telemetry systems deliver fast diagnostic answers without bloating host disk usage.

### Domain: Verify in automated CI that PostgreSQL LISTEN/NOTIFY wakes idle agents in <5ms with 0% CPU consumption. (1 tasks)
- **AGY-2250**: Automated reactive agent wakeup latency (<5ms) and zero idle CPU benchmark suite  (WS-ORCH | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-50ms reactive wakeups and zero-polling CPU efficiency.
  - *Why:* Continuous testing ensures event dispatcher optimizations maintain low latency and high concurrency.

### Domain: Verify in automated CI that QServe achieves >3.0x speedup, fits 70B in <22GB VRAM, and retains >99.5% accuracy. (1 tasks)
- **AGY-2459**: Automated 3.2x QServe speedup, 70B VRAM fitting (<22GB), and accuracy test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >3x matrix acceleration, sub-22GB VRAM fitting, and high mathematical reasoning accuracy.
  - *Why:* Continuous testing ensures mixed-precision integer pipelines deliver maximum speed without compromising model quality.

### Domain: Verify in automated CI that ROCm PagedAttention sustains 50 concurrent requests with >92% VRAM efficiency. (1 tasks)
- **AGY-2330**: Automated AMD ROCm PagedAttention concurrency (50 streams) and 95% VRAM utilization test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-concurrency ROCm batch capacity and memory fragmentation resilience.
  - *Why:* Continuous testing ensures AMD GPU inference updates maintain rock-solid stability and high batch density.

### Domain: Verify in automated CI that RSB stuffing executes in <100ns and blocks 100% of ret2spec underflow exploits. (1 tasks)
- **AGY-2537**: Automated ret2spec RSB underflow mitigation (<100ns latency) and context-switch test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-100ns RSB stuffing, complete underflow neutralization, and negligible overhead.
  - *Why:* Continuous testing ensures hardware Return Stack Buffer protections remain effective across kernel and compiler toolchains.

### Domain: Verify in automated CI that SBOM manifests match 100% of installed binaries and Cosign signatures pass verification. (1 tasks)
- **AGY-2310**: Automated in-image SBOM completeness, package inventory hash parity, and signature test suite  (WS-BUILD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates complete package inventory coverage and cryptographically valid Cosign attestations.
  - *Why:* Continuous testing ensures SBOM pipelines never omit newly added dependencies or fail signature validation.

### Domain: Verify in automated CI that SSBD disables store bypass in <500ns and /proc status reports force thread disabled. (1 tasks)
- **AGY-2545**: Automated Spectre v4 / SSB mitigation verification (<500ns MSR toggle) and /proc test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond SSBD activation, /proc kernel status compliance, and complete Spectre v4 neutralization.
  - *Why:* Continuous testing ensures speculative store bypass mitigations remain active and enforceable across CPU microcode updates.

### Domain: Verify in automated CI that SVD-LLM cuts memory bandwidth by 70% and perplexity delta is <0.02. (1 tasks)
- **AGY-2409**: Automated 70% memory bandwidth reduction, outlier preservation, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates 70% bandwidth reduction, outlier preservation, and low perplexity degradation.
  - *Why:* Continuous testing ensures matrix factorization algorithms maintain extreme compression efficiency without degrading output quality.

### Domain: Verify in automated CI that SVDQuant achieves >3.2x speedup and retains >99.8% math reasoning accuracy. (1 tasks)
- **AGY-2483**: Automated 3.4x SVDQuant speedup, outlier absorption, and accuracy test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >3.2x matrix acceleration, outlier error absorption, and high mathematical reasoning accuracy.
  - *Why:* Continuous testing ensures fused low-rank residual quantization maintains extreme speed without compromising model quality.

### Domain: Verify in automated CI that Seat-to-Blade profile transitions clean up 100% of desktop services and release compositor VRAM. (1 tasks)
- **AGY-2569**: Automated Seat-to-Blade profile transition and zero GPU leak verification test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates complete service switching and zero GPU memory retention after Seat-to-Blade transition.
  - *Why:* Continuous testing ensures dynamic host topology transitions maintain clean resource separation and operational agility.

### Domain: Verify in automated CI that SmoothQuant W8A8 achieves >1.9x speedup and perplexity delta is <0.02. (1 tasks)
- **AGY-2431**: Automated 2.0x INT8 Tensor Core speedup, outlier activation smoothing, and test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >1.9x INT8 matrix speedup, low perplexity degradation, and zero numerical exceptions.
  - *Why:* Continuous testing ensures activation smoothing algorithms preserve model accuracy while unlocking peak hardware speed.

### Domain: Verify in automated CI that SpQR achieves >3.4x speedup, outlier density <0.5%, and perplexity delta <0.015. (1 tasks)
- **AGY-2535**: Automated 3.5x SpQR speedup, <0.5% outlier density, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >3.4x matrix acceleration, minimal outlier overhead, and near-zero perplexity loss.
  - *Why:* Continuous testing ensures mixed-precision sparse-quantized pipelines maintain high speed and reasoning accuracy.

### Domain: Verify in automated CI that SparseGPT achieves >1.95x speedup on GPU and retains >99.2% HumanEval pass@1 score. (1 tasks)
- **AGY-2531**: Automated 2.0x sparse speedup, 2:4 structural validation, and accuracy test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >1.95x matrix acceleration, exact 2:4 structural patterns, and high coding accuracy.
  - *Why:* Continuous testing ensures hardware-accelerated structural sparsity maintains high speed and reasoning precision.

### Domain: Verify in automated CI that SpecInfer achieves >2.8x speedup, 1-pass tree evaluation, and 100% token output parity. (1 tasks)
- **AGY-2521**: Automated 2.8x SpecInfer speedup, tree-attention mask validity, and token parity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >2.8x generation speedup, exact tree attention causal masking, and 100% token distribution fidelity.
  - *Why:* Continuous testing ensures multi-draft tree verification maintains high speculative acceptance rates and perfect mathematical output.

### Domain: Verify in automated CI that UEFI bootloader phase takes <300ms and emergency key opens boot menu. (1 tasks)
- **AGY-2298**: Automated sub-1s UEFI boot time, baked UKI signature, and emergency key override test suite  (WS-BOOT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-300ms bootloader handoff and reliable emergency menu triggering.
  - *Why:* Continuous testing ensures bootloader configuration maintains instant boot speed and reliable rescue paths.

### Domain: Verify in automated CI that UFFD write-protect intercepts writes in <1us and tracks 100% of dirty pages. (1 tasks)
- **AGY-2529**: Automated UFFDIO_WRITEPROTECT intercept latency (<1us), dirty page logging test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond fault intercept latency, exact dirty page tracking, and zero memory corruption.
  - *Why:* Continuous testing ensures memory protection and dirty tracking runtimes maintain high performance across kernel updates.

### Domain: Verify in automated CI that VNNI kernels achieve >35 tok/s on capable cores and L1 cache miss rate is <5%. (1 tasks)
- **AGY-2429**: Automated CPU K-Quant VNNI throughput (>35 tok/s) and cache-blocked benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high VNNI token decoding throughput, L1 cache locality, and multicore scaling.
  - *Why:* Continuous testing ensures CPU kernel optimizations preserve peak vector performance across compiler updates.

### Domain: Verify in automated CI that Varlink RPC latency is <1ms and invalid schemas are rejected with type errors. (1 tasks)
- **AGY-2342**: Automated Varlink schema validation, sub-1ms RPC round-trip, and socket activation test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates Varlink interface schemas, sub-1ms RPC throughput, and error handling.
  - *Why:* Continuous testing ensures host IPC interfaces remain robust, fast, and strictly schema-compliant.

### Domain: Verify in automated CI that WebRTC AEC achieves >40dB echo suppression and 0 acoustic feedback squeals. (1 tasks)
- **AGY-2385**: Automated acoustic echo cancellation (>40dB suppression) and full-duplex test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-performance echo cancellation and clean duplex microphone stream filtering.
  - *Why:* Continuous testing ensures audio driver and PipeWire updates preserve feedback-free duplex voice communications.

### Domain: Verify in automated CI that WebRTC stream delivers 60 FPS 4K video with <30ms latency and 0 frame tearing. (1 tasks)
- **AGY-2387**: Automated 4K 60FPS WebRTC desktop stream latency (<30ms) and encoder test suite  (WS-APP | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates hardware-accelerated WebRTC streaming, 60 FPS delivery, and low CPU load.
  - *Why:* Continuous testing ensures remote desktop streaming updates maintain ultra-low latency and peak video fluidity.

### Domain: Verify in automated CI that WebRTC voice turn-around latency is <120ms and packet loss is <0.1%. (1 tasks)
- **AGY-2427**: Automated WebRTC full-duplex voice latency (<120ms) and PipeWire bridge test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-120ms voice loop latency, PipeWire stream stability, and zero packet loss.
  - *Why:* Continuous testing ensures conversational audio pipelines maintain real-time responsiveness and high audio quality.

### Domain: Verify in automated CI that activation tensor payloads match exact theoretical math (32.8KB decode, 64MB prefill) and forward pass succeeds across 3 nodes. (1 tasks)
- **AGY-2573**: Automated distributed 70B layer-split forward pass and network failover test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates exact activation tensor payload sizes and 3-node distributed forward pass execution.
  - *Why:* Continuous testing ensures distributed inference network optimizations maintain exact mathematical precision and communication fidelity.

### Domain: Verify in automated CI that active-active MDS achieves >50,000 ops/s and standby MDS takes over in <2s on rank crash. (1 tasks)
- **AGY-2338**: Automated multi-MDS metadata throughput (>50,000 ops/s) and standby failover test suite  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-throughput active-active MDS scaling and sub-2s metadata failover.
  - *Why:* Continuous testing ensures distributed metadata clusters maintain high throughput and seamless fault tolerance.

### Domain: Verify in automated CI that agent turn switching takes <1ms and GPU memory fragmentation is 0%. (1 tasks)
- **AGY-2435**: Automated multi-agent session handoff latency (<1ms) and VRAM recycling test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond session handoffs, zero memory churn, and stable VRAM residency.
  - *Why:* Continuous testing ensures multi-agent memory pooling maintains maximum speed and memory efficiency.

### Domain: Verify in automated CI that all systemd services maintain exposure score < 3.0 and seccomp filters block dangerous calls. (1 tasks)
- **AGY-2264**: Automated systemd unit security exposure score (<3.0) and seccomp filter verification test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates least-privilege systemd sandboxing and seccomp filter enforcement.
  - *Why:* Continuous testing ensures systemd unit additions maintain strict sandboxing and containment guarantees.

### Domain: Verify in automated CI that an unresponsive daemon triggers systemd service restart via watchdog timeout. (1 tasks)
- **AGY-2210**: Automated systemd daemon freeze watchdog timeout and recovery test suite  (WS-BOOT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that missed watchdog pings trigger automated service recovery.
  - *Why:* Continuous testing ensures systemd watchdog policies recover stalled agent processes without manual operator intervention.

### Domain: Verify in automated CI that attenuated Macaroons enforce caveats and burn nonces in <5ms. (1 tasks)
- **AGY-2322**: Automated subagent token attenuation, caveat enforcement, and replay prevention test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates strict caveat attenuation, expiration enforcement, and nonce burn integrity.
  - *Why:* Continuous testing ensures subagent authorization tokens maintain airtight least-privilege security boundaries.

### Domain: Verify in automated CI that background memory hogs are evicted in <10s while protected daemons survive. (1 tasks)
- **AGY-2266**: Automated memory pressure stall injection and protected service survival test suite  (WS-BOOT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that systemd-oomd reliably kills thrashing slices and preserves critical services.
  - *Why:* Continuous testing ensures memory management updates maintain system responsiveness under severe memory pressure.

### Domain: Verify in automated CI that binary embeddings achieve 32x RAM reduction, >10M comparisons/sec, and MRR >0.95. (1 tasks)
- **AGY-2493**: Automated 32x embedding RAM reduction, 10M comparison/sec, and MRR test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates 32x memory compression, hardware POPCOUNT speed, and high semantic retrieval accuracy.
  - *Why:* Continuous testing ensures binary vector quantization maintains fast retrieval throughput and semantic precision.

### Domain: Verify in automated CI that chunked prefill limits inter-token jitter to <5ms during 64k concurrent prompt prefill. (1 tasks)
- **AGY-2487**: Automated chunked prefill streaming jitter (<5ms) and concurrent throughput test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-5ms streaming jitter, iteration batching correctness, and high GPU saturation.
  - *Why:* Continuous testing ensures batch scheduling updates preserve real-time streaming responsiveness.

### Domain: Verify in automated CI that cluster node clock offsets stay within 1ms and timestamps remain strictly monotonic. (1 tasks)
- **AGY-2164**: Clock offset jitter and monotonic timestamp ordering validation test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates monotonic clock ordering and tight offset tolerance.
  - *Why:* Continuous testing ensures network upgrades do not introduce clock drift that invalidates audit trails.

### Domain: Verify in automated CI that concurrent reindexing succeeds during live read/write queries with zero deadlocks. (1 tasks)
- **AGY-2208**: Automated PostgreSQL dead tuple vacuuming and concurrent HNSW index reindexing test suite  (WS-RAG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that PostgreSQL autovacuum and concurrent reindexing operate safely under active load.
  - *Why:* Continuous testing ensures database maintenance algorithms never disrupt live agent reasoning loops.

### Domain: Verify in automated CI that constrained decoding achieves 100.0% schema validity across 1,000 complex schemas. (1 tasks)
- **AGY-2284**: Automated 1,000-schema structured output generation and zero-syntax-error benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates zero syntax errors and deterministic grammar token masking.
  - *Why:* Continuous testing ensures inference sampler updates maintain reliable structured output generation.

### Domain: Verify in automated CI that council consensus rejects hallucinated/malicious actions and accepts valid patches. (1 tasks)
- **AGY-2252**: Automated multi-agent council voting, hallucination rejection, and shadow sandbox test suite  (WS-ORCH | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates multi-agent Byzantine consensus accuracy and shadow sandbox containment.
  - *Why:* Continuous testing ensures autonomous agent swarms maintain reliable self-governance and safety boundaries.

### Domain: Verify in automated CI that crash triage parses panic callstacks and generates valid bug tickets in <30s. (1 tasks)
- **AGY-2240**: Automated kernel vmcore analysis and PostgreSQL bug ticket creation test suite  (WS-DIAG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates automated vmcore symbol demangling, stack parsing, and database reporting.
  - *Why:* Continuous testing ensures kernel debugging toolchains remain operational across new kernel minor releases.

### Domain: Verify in automated CI that devices in separate IOMMU groups cannot execute unauthorized peer DMA reads. (1 tasks)
- **AGY-2216**: Automated IOMMU group isolation and peer-to-peer DMA containment test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates hardware IOMMU DMA containment and fault logging.
  - *Why:* Continuous testing ensures kernel updates maintain strict IOMMU memory protection boundaries.

### Domain: Verify in automated CI that divergent peer branches reconcile cleanly across multiple git forges. (1 tasks)
- **AGY-2160**: Automated offline divergence simulation and multi-forge synchronization test suite  (WS-GIT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates git reconciliation across divergent multi-master topologies.
  - *Why:* Continuous reconciliation testing guarantees that decentralized git operations remain mathematically robust.

### Domain: Verify in automated CI that draft speculative decoding achieves >2.0x speedup and 100% mathematical token parity. (1 tasks)
- **AGY-2417**: Automated speculative decoding speedup (>2.0x) and target output parity benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >2x throughput acceleration, rejection sampling correctness, and exact output parity.
  - *Why:* Continuous testing ensures speculative drafting algorithms maintain significant speedups without altering model reasoning.

### Domain: Verify in automated CI that drift detection flags all /etc modifications and reconciliation restores base state. (1 tasks)
- **AGY-2218**: Automated configuration drift detection and state reconciliation test suite  (WS-CONFIG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates configuration drift auditing and atomic state reconciliation.
  - *Why:* Continuous testing ensures system configuration integrity remains deterministic across self-rebuilding cycles.

### Domain: Verify in automated CI that eBPF probes attach in <10ms and impose <0.2% CPU overhead during heavy load. (1 tasks)
- **AGY-2318**: Automated eBPF probe attach latency (<10ms) and low-overhead tracing test suite  (WS-DIAG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates instant eBPF probe compilation, low tracing overhead, and database insertion.
  - *Why:* Continuous testing ensures kernel tracing tools remain safe and lightweight for live production diagnostics.

### Domain: Verify in automated CI that embeddings run on NPU/CPU with <1% CPU load and zero discrete GPU wakeups. (1 tasks)
- **AGY-2292**: Automated NPU offload, CPU vector fallback, and discrete GPU sleep power benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates NPU/CPU embedding throughput and persistent discrete GPU sleep states.
  - *Why:* Continuous testing ensures AI routing updates preserve power efficiency across diverse hardware architectures.

### Domain: Verify in automated CI that ephemeral microVMs spawn in <50ms and transfer data at >1GB/s over VSOCK. (1 tasks)
- **AGY-2168**: MicroVM sub-50ms boot latency and VSOCK IPC throughput benchmark suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Benchmark suite confirms microVM boot times and VSOCK throughput meet sub-50ms targets.
  - *Why:* Continuous performance testing ensures virtualization overhead remains imperceptible for rapid agent tool loops.

### Domain: Verify in automated CI that explicit_bzero scrubs memory in <1us and secret keys are never present in swap. (1 tasks)
- **AGY-2477**: Automated secret memory zeroization (<1us scrub) and swap leak prevention test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond DRAM scrubbing, swap protection, and complete compiler optimization resistance.
  - *Why:* Continuous testing ensures memory security allocators prevent secret credential leakage under all compiler optimization levels.

### Domain: Verify in automated CI that failed OSD recovery restores HEALTH_OK and client p99 latency degrades <10%. (1 tasks)
- **AGY-2328**: Automated OSD failure injection, PG backfill recovery, and client I/O latency test suite  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates automated PG rebalancing, healthy pool restoration, and bounded client I/O latency.
  - *Why:* Continuous testing ensures distributed storage failover mechanisms operate autonomously without operator intervention.

### Domain: Verify in automated CI that fan speed controller eliminates rapid oscillations and stabilizes junction temperatures. (1 tasks)
- **AGY-2222**: Automated thermal load ramp, fan curve hysteresis, and acoustic stabilization benchmark suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates PID fan curve smoothness, monotonic ramp rates, and hysteresis damping.
  - *Why:* Continuous testing ensures fan controller updates do not cause acoustic whining or thermal runaways.

### Domain: Verify in automated CI that fused asymmetric GEMM achieves >3.5x speedup and improves perplexity by >0.04. (1 tasks)
- **AGY-2467**: Automated 3.6x asymmetric GEMM speedup, register fusion, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >3.5x matrix acceleration, register-level fusion, and superior asymmetric perplexity.
  - *Why:* Continuous testing ensures fused asymmetric arithmetic kernels maintain peak hardware performance and numerical accuracy.

### Domain: Verify in automated CI that high-concurrency AST merges maintain 100% compiler syntax correctness. (1 tasks)
- **AGY-2214**: Automated AST merge conflict stress test and compiler syntax verification suite  (WS-GIT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-concurrency AST merge stability and compiler correctness.
  - *Why:* Continuous testing ensures that multi-agent development swarms can collaborate without merge collisions.

### Domain: Verify in automated CI that high-priority voice inference achieves <50ms latency during heavy background load. (1 tasks)
- **AGY-2230**: Automated GPU compute preemption latency and training resumption verification test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-50ms high-priority inference execution under heavy compute load.
  - *Why:* Continuous testing ensures kernel driver updates maintain GPU compute preemption guarantees.

### Domain: Verify in automated CI that home enclaves lock on logout and unlock in <200ms with TPM2/FIDO2. (1 tasks)
- **AGY-2344**: Automated systemd-homed LUKS2 unlock, key zeroization, and portable migration test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates LUKS2 home container lifecycle, key zeroization, and cross-node migration.
  - *Why:* Continuous testing ensures user security enclaves protect private files reliably without causing login delays.

### Domain: Verify in automated CI that idle GPU reaches <3W power draw and wakes in <150ms upon query arrival. (1 tasks)
- **AGY-2282**: Automated idle GPU power measurement (<3W) and sub-150ms D3cold wakeup benchmark suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-3W idle power consumption and sub-150ms D3cold wakeup transitions.
  - *Why:* Continuous testing ensures power management optimizations remain functional across kernel and driver updates.

### Domain: Verify in automated CI that injected kernel panics are preserved in ramoops and ingested with 100% trace fidelity. (1 tasks)
- **AGY-2389**: Automated kernel panic injection, ramoops log preservation, and database ingestion test suite  (WS-BOOT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates ramoops log preservation, stack trace parsing, and database recording.
  - *Why:* Continuous testing ensures kernel crash telemetry systems reliably capture diagnostic data during critical failures.

### Domain: Verify in automated CI that intentional Critical CVE injections are blocked and clean images pass. (1 tasks)
- **AGY-2260**: Automated Critical CVE rejection and supply-chain vulnerability gate test suite  (WS-BUILD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that vulnerability gates reliably catch and block vulnerable container images.
  - *Why:* Continuous testing ensures supply-chain scanner rules and feeds remain effective against emerging threats.

### Domain: Verify in automated CI that intentional byte modification in journal files is flagged by journalctl --verify. (1 tasks)
- **AGY-2306**: Automated journal tampering detection and journalctl --verify integrity test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates cryptographic tampering detection and FSS key verification.
  - *Why:* Continuous testing ensures log sealing mechanics reliably detect any forensic tampering attempts.

### Domain: Verify in automated CI that intentional syntax and lint violations are rejected by pre-commit hooks. (1 tasks)
- **AGY-2182**: Automated pre-commit linter violation rejection and auto-format test suite  (WS-GIT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that pre-commit hooks reject malformed syntax and format valid code.
  - *Why:* Continuous hook testing ensures developer and agent workstations enforce uniform code quality gates.

### Domain: Verify in automated CI that inter-bridge container traffic is 100% blocked and 0 internal ports leak to 0.0.0.0. (1 tasks)
- **AGY-2340**: Automated container network isolation, lateral traversal block, and port audit test suite  (WS-APP | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates strict Netavark network isolation, firewall packet dropping, and zero port leaks.
  - *Why:* Continuous testing ensures container networking updates maintain airtight perimeter and lateral defense boundaries.

### Domain: Verify in automated CI that inter-node RPCs require valid mTLS certificates and reject expired keys. (1 tasks)
- **AGY-2166**: Automated mTLS authentication enforcement and certificate rotation verification test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates strict mTLS enforcement and seamless in-memory certificate rotation.
  - *Why:* Continuous testing ensures that cluster workload communications remain mutually authenticated.

### Domain: Verify in automated CI that interconnect profiler samples matrix telemetry with <0.1% CPU overhead. (1 tasks)
- **AGY-2262**: Automated inter-GPU P2P bandwidth telemetry and tensor bottleneck detection test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates P2P bandwidth telemetry precision and low-overhead matrix sampling.
  - *Why:* Continuous testing ensures GPU monitoring daemons do not degrade active inference performance.

### Domain: Verify in automated CI that io_uring SQPOLL sustains >1,000,000 IOPS with latency <50us. (1 tasks)
- **AGY-2439**: Automated 1,000,000 IOPS random I/O benchmark and zero-syscall SQPOLL test suite  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond storage latency, million-IOPS throughput, and syscall elimination.
  - *Why:* Continuous testing ensures storage engine updates preserve peak asynchronous kernel I/O performance.

### Domain: Verify in automated CI that isolated containers cannot establish unauthorized lateral network connections. (1 tasks)
- **AGY-2078**: Container bridge lateral movement penetration test in CI test suites  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Automated CI test verifies container network isolation boundaries continuously.
  - *Why:* Continuous testing ensures firewall rules do not silently regress during system updates.

### Domain: Verify in automated CI that kernel text base address exhibits high statistical variance across reboots. (1 tasks)
- **AGY-2300**: Automated KASLR physical address space variance and entropy validation test suite  (WS-BOOT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-entropy kernel memory address randomization across boot cycles.
  - *Why:* Continuous testing ensures kernel builds maintain robust anti-exploit address space layout randomization.

### Domain: Verify in automated CI that livepatch redirects kernel symbols in <100ms with zero dropped network packets. (1 tasks)
- **AGY-2280**: Automated kernel livepatch injection, zero-downtime CVE neutralization, and ftrace redirection test suite  (WS-BOOT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that kernel livepatching safely redirects functions under heavy I/O load.
  - *Why:* Continuous testing ensures kernel livepatching infrastructure remains reliable across kernel minor updates.

### Domain: Verify in automated CI that livepatching does not destabilize running container or hypervisor processes. (1 tasks)
- **AGY-2144**: Zero-downtime kernel livepatch verification and regression test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates zero-downtime kernel livepatching under active system workload.
  - *Why:* Continuous livepatch testing ensures security hot-fixes do not introduce kernel stability regressions.

### Domain: Verify in automated CI that log forwarders buffer 10,000 logs during network drops and flush on reconnection. (1 tasks)
- **AGY-2258**: Automated multi-node log streaming, partition buffering, and central query test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates cluster log streaming reliability and zero-loss partition recovery.
  - *Why:* Continuous testing guarantees telemetry integrity during mesh network reconnections and blade failovers.

### Domain: Verify in automated CI that mDNS advertises 100% of local services and discovers peers in <200ms offline. (1 tasks)
- **AGY-2415**: Automated local mDNS service advertising, sub-200ms peer discovery, and offline test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates ZeroConf service publication, TXT record parsing, and rapid peer resolution.
  - *Why:* Continuous testing ensures local service discovery mechanics operate seamlessly in offline edge environments.

### Domain: Verify in automated CI that mDNS discovery triggers authenticated WireGuard mesh connection. (1 tasks)
- **AGY-2186**: Automated LAN peer discovery, cryptographic handshake, and mesh join test suite  (WS-NET | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates zero-conf mDNS discovery and authenticated WireGuard tunnel setup.
  - *Why:* Continuous networking tests ensure discovery protocols remain functional across firewall and router topologies.

### Domain: Verify in automated CI that memory compaction reclaims >60% table disk space while queries proceed with <5ms latency. (1 tasks)
- **AGY-2374**: Automated vector memory compaction, disk reclamation, and non-blocking query test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates non-blocking vector reindexing, disk space reclamation, and sustained query throughput.
  - *Why:* Continuous testing ensures long-term database maintenance routines never disrupt real-time agent execution.

### Domain: Verify in automated CI that memory safety negotiator enables MTE/CET or fallback in <1us with 0 crash loops. (1 tasks)
- **AGY-2549**: Automated cross-architecture memory tagging negotiation and violation test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates multi-architecture capability negotiation, accurate violation trapping, and robust fallback handling.
  - *Why:* Continuous testing ensures universal memory safety mechanisms function reliably across diverse hardware topologies.

### Domain: Verify in automated CI that microVM hibernation takes <20ms, resume takes <10ms, and state integrity is 100%. (1 tasks)
- **AGY-2471**: Automated microVM snapshot latency (<20ms), instant resume (<10ms), and state test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-20ms snapshot dump, sub-10ms resume latency, and perfect guest state preservation.
  - *Why:* Continuous testing ensures memory hibernation pipelines maintain rapid wakeup speeds and zero data corruption.

### Domain: Verify in automated CI that microVM state serialization and restore complete in <50ms with 100% memory integrity. (1 tasks)
- **AGY-2567**: Automated MicroVM state handover latency (<50ms) and zero data loss test suite  (WS-HCI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-50ms handover latency and zero register divergence across live migrations.
  - *Why:* Continuous testing ensures microVM virtualization updates preserve ultra-fast state serialization and zero guest data loss.

### Domain: Verify in automated CI that microVMs boot in <50ms and synthetic breakout exploits cannot access host files. (1 tasks)
- **AGY-2272**: Automated sub-50ms microVM boot time, vsock throughput, and breakout containment test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microVM boot speed, vsock bandwidth, and strict virtualization containment.
  - *Why:* Continuous testing ensures virtualization hypervisors maintain impenetrable isolation for autonomous code execution.

### Domain: Verify in automated CI that mios user has UID 1000, GID 1000, valid /etc/subuid allocations, and that systemd user services run cleanly without system UID bypasses. (1 tasks)
- **AGY-2563**: Automated UID/GID Range & Systemd User Session Boundary Verification Test Suite  (WS-USER | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates UID 1000 allocation, subuid mapping, and user session service compatibility.
  - *Why:* Automated CI testing ensures future provisioning updates or base image rebuilds never regress the non-system user class invariant.

### Domain: Verify in automated CI that mios-exec-sandbox spawns in <5ms, blocks 100% of host writes, and isolates network. (1 tasks)
- **AGY-2489**: Automated <5ms sandbox launch latency, write denial, and network isolation test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-5ms sandbox provisioning, read-only host protection, and network isolation.
  - *Why:* Continuous testing ensures execution isolation mechanisms remain active and performant across system updates.

### Domain: Verify in automated CI that mixed-bit models reduce size by >65% and perplexity delta remains <0.020. (1 tasks)
- **AGY-2465**: Automated 68% size reduction, mixed-bit execution, and perplexity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >65% compression, low perplexity degradation, and seamless mixed-bit execution.
  - *Why:* Continuous testing ensures mixed-bit compilation algorithms maintain high model compression without precision collapse.

### Domain: Verify in automated CI that mobile and NAS node profiles discover local AI capabilities and enroll in <200ms. (1 tasks)
- **AGY-2451**: Automated mobile and NAS mesh node enrollment, local inference profiling, and discovery test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates hardware profiling accuracy, dynamic memory bounds, and rapid mesh enrollment.
  - *Why:* Continuous testing ensures hardware profile detection adapts correctly across diverse consumer and mobile tiers.

### Domain: Verify in automated CI that mobile offloading decisions resolve in <50ms and vector sync achieves 100% parity. (1 tasks)
- **AGY-2453**: Automated mobile peer discovery, adaptive prompt routing (<50ms), and memory sync test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates instant mobile offload routing, home cluster execution, and bidirectional vector synchronization.
  - *Why:* Continuous testing ensures mobile device integration operates reliably across diverse network conditions.

### Domain: Verify in automated CI that modified sysctl parameters apply in <50ms and udev rules trigger live updates. (1 tasks)
- **AGY-2421**: Automated zero-reboot sysctl parameter application (<50ms) and live udev test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates instant sysctl reload, live sysfs updates, and udev rule execution.
  - *Why:* Continuous testing ensures system configuration daemons reliably update kernel state without service interruptions.

### Domain: Verify in automated CI that multi-modal WebSocket streams maintain <100ms voice latency under heavy vision load. (1 tasks)
- **AGY-2270**: Automated concurrent multi-modal streaming latency (<100ms) and temporal alignment test suite  (WS-ORCH | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-100ms conversational latency and seamless multi-modal temporal synchronization.
  - *Why:* Continuous testing ensures agent orchestrator optimizations preserve fluid real-time multi-modal interaction.

### Domain: Verify in automated CI that multi-model switching occurs in <500ms and active session state is 100% retained. (1 tasks)
- **AGY-2228**: Automated multi-model VRAM swapping, KV-cache paging latency, and session preservation test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-500ms model swapping and zero-loss KV-cache paging under heavy memory pressure.
  - *Why:* Continuous testing ensures memory management algorithms maintain fast inference switching on consumer hardware.

### Domain: Verify in automated CI that native XDP routes >10M pps and drops flood traffic in <500ns per packet. (1 tasks)
- **AGY-2401**: Automated 10M pps packet routing throughput, sub-microsecond XDP latency, and DDoS test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates line-rate packet processing, sub-microsecond latency, and wire-speed flood filtering.
  - *Why:* Continuous testing ensures eBPF networking programs maintain peak throughput and robust line-rate security.

### Domain: Verify in automated CI that native overlay achieves >10x I/O IOPS over FUSE and preserves POSIX UID permissions. (1 tasks)
- **AGY-2304**: Automated rootless container I/O throughput (10x speedup) and UID mapping test suite  (WS-APP | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-performance native kernel overlay I/O and POSIX UID permissions.
  - *Why:* Continuous testing ensures container storage updates maintain high-speed native filesystem operations.

### Domain: Verify in automated CI that network interface switching updates peer endpoints in <50ms with 0 packet drops. (1 tasks)
- **AGY-2352**: Automated network interface handoff, sub-50ms roaming, and PMTU clamping test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-50ms WireGuard endpoint roaming and adaptive MTU negotiation.
  - *Why:* Continuous testing ensures mesh networking updates preserve resilient roaming across diverse network conditions.

### Domain: Verify in automated CI that network partitions isolate minority nodes and prevent split-brain writes. (1 tasks)
- **AGY-2220**: Automated Raft leader election, split-brain partition prevention, and failover test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates Raft quorum preservation and split-brain write rejection.
  - *Why:* Continuous testing guarantees cluster state machine correctness under real-world network partition failures.

### Domain: Verify in automated CI that no cleartext DNS requests escape to public interfaces. (1 tasks)
- **AGY-2096**: DNS-over-HTTPS leak prevention and encrypted query test suite  (WS-NET | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Automated test suite confirms zero DNS leaks across system and container network interfaces.
  - *Why:* Continuous testing ensures DNS encryption policies remain airtight across system upgrades.

### Domain: Verify in automated CI that partial LFS pull fetches exact requested files and hardlink cache prevents redownloads. (1 tasks)
- **AGY-2314**: Automated targeted Git LFS partial pull, SHA-256 integrity, and deduplicated caching test suite  (WS-BUILD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates targeted LFS fetching, hash verification, and shared blob deduplication.
  - *Why:* Continuous testing ensures Git repository and model caching mechanics operate reliably across model upgrades.

### Domain: Verify in automated CI that peer connections seamlessly fall back from direct UDP to DERP relays. (1 tasks)
- **AGY-2194**: Automated symmetric NAT hole punching and DERP relay failover test suite  (WS-NET | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates NAT traversal negotiation and seamless relay failover.
  - *Why:* Continuous testing ensures mesh nodes maintain connectivity across diverse corporate and home network environments.

### Domain: Verify in automated CI that per-app rollback restores exact working state in <1s with 0 cross-app pollution. (1 tasks)
- **AGY-2244**: Automated Flatpak application state corruption and instant rollback test suite  (WS-APP | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates per-app state snapshots, corruption isolation, and instant rollback integrity.
  - *Why:* Continuous testing ensures filesystem snapshot mechanics preserve reliable per-application rollback capabilities.

### Domain: Verify in automated CI that pipelined speculation achieves >3.2x speedup and 100% greedy token parity. (1 tasks)
- **AGY-2539**: Automated 3.2x pipelined speculative speedup, queue throughput, and token parity test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >3.2x generation acceleration, microsecond queue streaming, and exact token parity.
  - *Why:* Continuous testing ensures asynchronous draft pipelining maintains high concurrency and lock-free memory safety.

### Domain: Verify in automated CI that prctl applies in <1us and blocks 100% of speculative store bypass exploit reads. (1 tasks)
- **AGY-2461**: Automated Spectre v4 SSB mitigation verification (<1us prctl) and memory test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond SSB enforcement, thread-level speculation status, and 0 side-channel leakage.
  - *Why:* Continuous testing ensures speculative side-channel mitigations remain airtight across CPU microcode updates.

### Domain: Verify in automated CI that pre-warmed Quadlets start in <100ms without internet access. (1 tasks)
- **AGY-2348**: Automated Day-0 container start latency (<100ms) and zero-download verification test suite  (WS-BUILD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates offline container startup speed and complete layer pre-warming.
  - *Why:* Continuous testing ensures container image pre-warming scripts never omit enabled Quadlet dependencies.

### Domain: Verify in automated CI that predictive failure thresholds trigger clean CephFS OSD drain and snapshot replication. (1 tasks)
- **AGY-2238**: Automated S.M.A.R.T. predictive failure simulation and proactive data evacuation test suite  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates automated S.M.A.R.T. predictive failure alerting and data evacuation.
  - *Why:* Continuous testing ensures storage clustering algorithms reliably prevent data loss under hardware degradation.

### Domain: Verify in automated CI that preemption halts training in <2s and restarts resume with bit-for-bit weight consistency. (1 tasks)
- **AGY-2268**: Automated training preemption, async checkpoint verification, and zero-loss step resumption test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates async checkpoint timing, zero-loss step recovery, and final model parity.
  - *Why:* Continuous testing ensures training infrastructure withstands power cuts, thermal capping, and node failovers.

### Domain: Verify in automated CI that prefix caching achieves >95% cache hit rate and TTFT is <5ms. (1 tasks)
- **AGY-2395**: Automated shared prompt prefix hit rate (>95%) and sub-5ms TTFT benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high Radix Tree cache hit rates, sub-5ms TTFT acceleration, and token parity.
  - *Why:* Continuous testing ensures prefix caching mechanics maintain extreme responsiveness across multi-turn sessions.

### Domain: Verify in automated CI that prefix caching achieves >95% hit rates and sub-20ms TTFT. (1 tasks)
- **AGY-2234**: Automated prefix cache hit rate and sub-20ms time-to-first-token benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates prefix cache hit efficiency and sub-20ms TTFT performance.
  - *Why:* Continuous testing ensures inference engine upgrades maintain prompt cache reuse and acceleration.

### Domain: Verify in automated CI that process core dumps and swap files contain zero recoverable secrets. (1 tasks)
- **AGY-2226**: Automated memory dump secret leakage and zeroization verification test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that protected secret memory never leaks into process core dumps.
  - *Why:* Continuous testing ensures memory security flags remain effective across C-runtime and compiler upgrades.

### Domain: Verify in automated CI that proxy routing achieves <1ms latency over Unix sockets and propagates trace IDs. (1 tasks)
- **AGY-2200**: Automated service mesh routing, Unix socket latency, and OpenTelemetry trace propagation test suite  (WS-NET | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates service mesh routing speed, Unix socket efficiency, and trace propagation.
  - *Why:* Continuous testing ensures proxy upgrades do not introduce latency overhead or drop distributed trace contexts.

### Domain: Verify in automated CI that quantized HNSW maintains >98% recall accuracy and <5ms query latency. (1 tasks)
- **AGY-2324**: Automated 1,000,000-vector quantized HNSW recall (<5ms) and RAM reduction benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-recall accuracy, sub-5ms search speed, and 70%+ memory savings.
  - *Why:* Continuous testing ensures vector database optimizations maintain precision and throughput across database updates.

### Domain: Verify in automated CI that real-time threads achieve <500us scheduling jitter during heavy background load. (1 tasks)
- **AGY-2256**: Automated vendor-agnostic CPU core pinning, thread isolation, and jitter benchmark suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-500us real-time scheduling latency and robust core isolation under heavy load.
  - *Why:* Continuous testing ensures kernel scheduling updates maintain deterministic real-time audio and microVM execution.

### Domain: Verify in automated CI that rootless containers cannot access unassigned GPU nodes. (1 tasks)
- **AGY-2124**: Rootless container GPU device isolation and cgroup v2 eBPF device filter test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Automated test suite confirms cgroup v2 device filter blocks unauthorized GPU access.
  - *Why:* Continuous device testing ensures container isolation boundaries are preserved across Podman updates.

### Domain: Verify in automated CI that scrub repairs corrupted mirror blocks and interactive I/O latency is unaffected. (1 tasks)
- **AGY-2316**: Automated filesystem bit rot repair, I/O latency throttle, and scrub reporting test suite  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates bit rot error correction and pressure-adaptive background throttling.
  - *Why:* Continuous testing ensures storage scrubbing daemons protect data integrity without causing I/O stutter.

### Domain: Verify in automated CI that seccomp-bpf attaches in <100us, blocks 100% of forbidden syscalls, and handles notifications. (1 tasks)
- **AGY-2509**: Automated seccomp-bpf attachment latency (<100us), syscall denial, and user notification test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-100us filter attachment, complete syscall blocking, and user-space notification handling.
  - *Why:* Continuous testing ensures system call filters remain strict and responsive across libc and kernel updates.

### Domain: Verify in automated CI that seeded random bits pass NIST SP 800-22 statistical randomness tests. (1 tasks)
- **AGY-2278**: Automated hardware entropy harvesting, statistical randomness (NIST SP 800-22), and seeding test suite  (WS-BOOT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates cryptographic entropy density and statistical whitening quality.
  - *Why:* Continuous testing ensures kernel entropy seeding maintains unimpeachable cryptographic randomness.

### Domain: Verify in automated CI that segfaults generate <1MB structured minidumps and zero raw core files persist on disk. (1 tasks)
- **AGY-2350**: Automated crash minidump extraction, secret exclusion, and raw core purge test suite  (WS-DIAG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates structured minidump generation, secret exclusion, and raw core file cleanup.
  - *Why:* Continuous testing ensures crash diagnostics maintain complete privacy protection and zero filesystem bloat.

### Domain: Verify in automated CI that self-replication daemon generates valid SHA-256 image digests and stages updates. (1 tasks)
- **AGY-2565**: Automated self-build trigger, image digest verification, and hot-swap staging test suite  (WS-HCI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates self-build trigger, cryptographic digest verification, and atomic staging.
  - *Why:* Continuous testing ensures autonomous OS rebuilding pipelines maintain strict image integrity and signature validation.

### Domain: Verify in automated CI that semantic compaction retains 100% of pinned architectural rules across 100k tokens. (1 tasks)
- **AGY-2274**: Automated long-horizon (100k+ token) conversation compaction and intent retention test suite  (WS-ORCH | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that compacted context retains critical instructions and constraint facts.
  - *Why:* Continuous testing ensures context management algorithms preserve essential reasoning data across long agent runs.

### Domain: Verify in automated CI that shared-memory rings sustain 60 FPS 4K transfers with <1us latency. (1 tasks)
- **AGY-2366**: Automated 4K 60FPS video frame transfer (<1us latency) and zero-copy benchmark suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond latency, high-bandwidth data transfers, and lock-free ring stability.
  - *Why:* Continuous testing ensures shared memory IPC optimizations maintain rock-solid performance under heavy multi-modal streaming.

### Domain: Verify in automated CI that signed livepatches apply in <100ms and unsigned modules are 100% rejected. (1 tasks)
- **AGY-2381**: Automated livepatch signature verification, unsigned module rejection, and IMA test suite  (WS-BOOT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates strict MOK signature gating, rapid ftrace redirection, and IMA attestation logging.
  - *Why:* Continuous testing ensures kernel livepatching maintains zero downtime without compromising kernel security boundaries.

### Domain: Verify in automated CI that simulated USB over-current faults isolate in <500ms and log to PostgreSQL. (1 tasks)
- **AGY-2276**: Automated USB over-current fault simulation, port isolation, and power recovery test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-500ms USB power cutoff and structured fault database logging.
  - *Why:* Continuous testing ensures hardware protection daemons reliably safeguard physical ports.

### Domain: Verify in automated CI that simulated VPN drops leak 0 public packets and local mesh stays responsive. (1 tasks)
- **AGY-2192**: Automated VPN disconnect IP leak prevention and local mesh routing verification test suite  (WS-NET | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that firewall kill-switch blocks WAN leakage and maintains local mesh traffic.
  - *Why:* Continuous testing ensures firewall rules prevent privacy leaks across VPN reconnect events.

### Domain: Verify in automated CI that snapshot creation takes <10ms and rollback restores 100% SHA-256 data integrity. (1 tasks)
- **AGY-2393**: Automated CephFS snapshot creation (<10ms), retention rotation, and rollback test suite  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates microsecond snapshot creation, data integrity restoration, and automated pruning.
  - *Why:* Continuous testing ensures distributed storage snapshot operations maintain reliable instant recovery capabilities.

### Domain: Verify in automated CI that snapshot deltas replicate in <60s and 1-click failover promotes standby pool in <5s. (1 tasks)
- **AGY-2433**: Automated 15-minute snapshot replication, delta sync, and 1-click failover test suite  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates incremental snapshot delta replication, sub-5s failover, and exact data parity.
  - *Why:* Continuous testing ensures distributed storage mirroring daemons preserve data durability across site failures.

### Domain: Verify in automated CI that speculative decoding achieves >2.5x speedup and outputs identical tokens. (1 tasks)
- **AGY-2254**: Automated speculative decoding speedup (3x) and mathematical output equivalence benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates speculative decoding speedup and mathematical token equivalence.
  - *Why:* Continuous testing ensures draft model pairing maintains deterministic, regression-free acceleration.

### Domain: Verify in automated CI that storage GC reclaims disk space without corrupting active container layers. (1 tasks)
- **AGY-2188**: Automated container layer pruning threshold and deduplication verification test suite  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates storage reclamation and layer integrity across container prune cycles.
  - *Why:* Continuous testing ensures storage garbage collection never removes active or pinned container images.

### Domain: Verify in automated CI that streaming ASR emits words in <100ms with Word Error Rate (WER) < 8.0%. (1 tasks)
- **AGY-2336**: Automated streaming ASR word emission latency (<100ms) and word error rate benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-100ms streaming word emissions and low Word Error Rate accuracy.
  - *Why:* Continuous testing ensures speech recognition optimizations preserve high accuracy and real-time responsiveness.

### Domain: Verify in automated CI that streaming TTS delivers first audio in <50ms with 0 underrun glitches. (1 tasks)
- **AGY-2286**: Automated speech synthesis first-packet latency (<50ms) and buffer underrun benchmark suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-50ms first-packet audio streaming and glitch-free PipeWire buffer feeding.
  - *Why:* Continuous testing ensures audio synthesis optimizations preserve fluid real-time voice performance.

### Domain: Verify in automated CI that synthesized ISO and iPXE netboot artifacts boot and install to disk in <180s. (1 tasks)
- **AGY-2246**: Automated headless QEMU iPXE netboot and live ISO installation test suite  (WS-BOOT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates unattended iPXE netboot and disk deployment in virtualized microVMs.
  - *Why:* Continuous testing ensures that OS image upgrades never produce unbootable ISO or network rescue media.

### Domain: Verify in automated CI that synthetic input events trigger expected UI actions and respect session boundaries. (1 tasks)
- **AGY-2206**: Automated synthetic mouse/keyboard input injection and session boundary test suite  (WS-APP | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates Libei synthetic input delivery and event timing precision.
  - *Why:* Continuous testing ensures Wayland compositor updates do not break autonomous GUI computer use.

### Domain: Verify in automated CI that ternary compilation finishes in <2 min for 7B models with MSE loss <0.02. (1 tasks)
- **AGY-2413**: Automated ternary compilation speed, MSE reconstruction parity (<0.02), and bitpack test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates high-speed ternary model compilation, mathematical MSE parity, and bitpacking fidelity.
  - *Why:* Continuous testing ensures weight quantization toolchains produce accurate, highly compressed model representations.

### Domain: Verify in automated CI that ternary unpacking sustains >300 tok/s on capable cores and allocates 0 bytes auxiliary RAM. (1 tasks)
- **AGY-2499**: Automated 300 tok/s ternary unpacking throughput, zero-allocation, and SIMD test suite  (WS-AI | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates >300 tok/s CPU throughput, zero auxiliary memory allocations, and hardware bit-manipulation execution.
  - *Why:* Continuous testing ensures low-level bit manipulation intrinsics maintain maximum vectorization efficiency across compiler toolchains.

### Domain: Verify in automated CI that thermal daemon responds in <500ms and keeps sustained temperatures <85°C. (1 tasks)
- **AGY-2449**: Automated sustained thermal load, fan curve modulation (<500ms), and power cap test suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-500ms thermal response, proactive PWM fan modulation, and sustained clock stability.
  - *Why:* Continuous testing ensures thermal controllers prevent overheating and maintain reliable node operation under heavy loads.

### Domain: Verify in automated CI that total power consumption strictly respects declared wattage limits. (1 tasks)
- **AGY-2232**: Automated power cap enforcement and carbon-aware batch scheduling benchmark suite  (WS-NODE | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates strict power cap compliance and smooth workload modulation.
  - *Why:* Continuous testing ensures energy management updates maintain power protection guarantees.

### Domain: Verify in automated CI that unapproved USB HID devices are blocked in <10ms and USB storage is 100% read-only. (1 tasks)
- **AGY-2397**: Automated BadUSB device rejection, read-only mount enforcement, and audit test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates instant BadUSB blocking, secure mount flag enforcement, and event logging.
  - *Why:* Continuous testing ensures hardware peripheral security policies remain strictly enforced across OS updates.

### Domain: Verify in automated CI that unsigned modules return EKEYREJECTED and /dev/mem access is blocked by lockdown. (1 tasks)
- **AGY-2515**: Automated unsigned kernel module rejection and lockdown integrity test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates unsigned module rejection, MOK key validation, and lockdown memory protections.
  - *Why:* Continuous testing ensures kernel integrity enforcement remains active across UKI rebuilds and kernel upgrades.

### Domain: Verify in automated CI that user-mode UFFD resolves pages in <1us and kernel fault creation returns EPERM. (1 tasks)
- **AGY-2519**: Automated UFFD_USER_MODE_ONLY demand-paging (<1us latency) and kernel fault test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates kernel-space fault denial, user-space demand-paging latency, and memory isolation.
  - *Why:* Continuous testing ensures memory management virtualization maintains high speed without opening kernel vulnerabilities.

### Domain: Verify in automated CI that virtio-pmem microVMs boot in <25ms and achieve >15 GB/s sequential read throughput. (1 tasks)
- **AGY-2332**: Automated virtio-pmem DAX I/O throughput (>15 GB/s) and sub-25ms boot benchmark suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates sub-25ms microVM boot times and multi-gigabyte memory I/O throughput.
  - *Why:* Continuous testing ensures microVM storage drivers maintain lightning-fast execution speed and zero disk overhead.

### Domain: Verify in automated CI that virtual CCID handles 10 concurrent signing requests without key collisions. (1 tasks)
- **AGY-2288**: Automated virtual CCID multi-tenant multiplexing and MiOS-USB global authentication test suite  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates concurrent virtual CCID forwarding, socket multiplexing, and cryptographic verification.
  - *Why:* Continuous testing ensures virtual smartcard bridges maintain secure multi-tenant cryptographic isolation.

### Domain: Verify in automated CI that virtual USB keyboard devices are blocked until explicitly authorized. (1 tasks)
- **AGY-2242**: Automated BadUSB keystroke injection block and USB authorization test suite in virtual USB sandbox  (WS-SEC | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates that unauthorized USB devices cannot communicate with the kernel.
  - *Why:* Continuous testing ensures kernel USB subsystem updates maintain peripheral authorization security.

### Domain: Verify in automated CI that virtual audio loopbacks prevent acoustic cross-talk and maintain 0 buffer xruns. (1 tasks)
- **AGY-2212**: Automated PipeWire Bluetooth codec negotiation and virtual loopback isolation test suite  (WS-APP | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates audio isolation and zero-crackling performance across virtual audio sinks.
  - *Why:* Continuous testing ensures audio server upgrades maintain acoustic isolation between voice synthesis and microphone input.

### Domain: Verify in automated benchmarks that frequently accessed blocks promote to NVMe and achieve >3GB/s read throughput. (1 tasks)
- **AGY-2196**: Automated Bcachefs tier promotion and hot/cold block migration benchmark suite  (WS-STRG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Benchmark suite confirms in-kernel block promotion delivers high-throughput NVMe read performance.
  - *Why:* Continuous testing ensures filesystem upgrades maintain kernel block caching and promotion efficiency.

### Domain: Verify in automated benchmarks that inter-GPU peer-to-peer memory copies achieve wire speed. (1 tasks)
- **AGY-2118**: Automated inter-GPU P2P bandwidth and memory latency validation benchmark  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Benchmark suite confirms inter-GPU P2P transfer rates meet physical bus capacity.
  - *Why:* Continuous P2P bandwidth validation catches PCIe bridge misconfigurations and IOMMU group issues.

### Domain: Verify in automated benchmarks that inter-VM audio achieves sub-5ms round-trip latency. (1 tasks)
- **AGY-2104**: Automated audio buffer underrun and latency jitter benchmark suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Benchmark suite confirms inter-VM audio latency meets the sub-5ms performance SLA.
  - *Why:* Continuous latency testing ensures audio optimizations do not degrade across kernel updates.

### Domain: Verify in automated benchmarks that remote display encoding maintains 60 FPS under varying network latency. (1 tasks)
- **AGY-2134**: Adaptive bitrate and low-latency frame encoding streaming benchmark suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Benchmark suite confirms adaptive bitrate encoding maintains target frame rates under network jitter.
  - *Why:* Continuous encoding testing ensures remote desktop streaming remains fluid across mobile connections.

### Domain: Verify in automated gates that AST-merged files pass syntax checks and unit tests before staging. (1 tasks)
- **AGY-2154**: Automated AST merge syntax compilation and regression test gate  (WS-GIT | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Validation gate enforces 100% syntax and linter compliance on all auto-merged code.
  - *Why:* Syntax gating guarantees that automated merge operations never break system buildability.

### Domain: Verify in automated integration tests that agents retain knowledge across context compaction events. (1 tasks)
- **AGY-2146**: Automated multi-turn context compaction and trajectory recall test suite  (WS-AI | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates factual recall and goal continuity across context compaction cycles.
  - *Why:* Continuous testing guarantees that context compaction does not cause agent amnesia during long tasks.

### Domain: Verify in automated integration tests that concurrent host-guest writes honor mutual exclusion locks. (1 tasks)
- **AGY-2090**: Cross-platform concurrent write and lock contention test suite in QEMU  (WS-STRG | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates cross-platform file locking integrity in virtualized integration runs.
  - *Why:* Automated verification ensures hypervisor storage upgrades do not break file locking semantics.

### Domain: Verify in automated microVM testing that boot failure triggers automatic bootc rollback. (1 tasks)
- **AGY-2100**: Automated boot-failure and Greenboot atomic rollback recovery test suite  (WS-BUILD | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates automatic greenboot rollback on simulated boot failure.
  - *Why:* Guaranteed atomic rollback is the core reliability foundation of immutable bootc operating systems.

### Domain: Verify in automated stress tests that thermal governor throttling recovers full clock speeds when load drops. (1 tasks)
- **AGY-2142**: Continuous thermal stress and governor modulation recovery test suite  (WS-VFIO | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Test suite validates thermal power cap modulation and automated frequency recovery.
  - *Why:* Continuous thermal testing ensures cooling algorithms operate reliably under sustained AI workloads.

### Domain: Verify in automated tests that package installation recovers from mirror failures without corruption. (1 tasks)
- **AGY-2102**: Upstream mirror failover and RPM transaction integrity verification test  (WS-BUILD | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Automated test suite validates DNF5 mirror failover and transaction integrity.
  - *Why:* Resilient package management prevents intermittent network blips from breaking image compilation.

### Domain: Verify in automated tests that sandboxed Flatpaks cannot bypass XDG portals. (1 tasks)
- **AGY-2088**: XDG Desktop Portal permission and socket boundary verification suite  (WS-APP | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Verification suite confirms sandbox containment for all baked Flatpak applications.
  - *Why:* Continuous portal testing ensures sandbox restrictions are not bypassed by application updates.

### Domain: Verify livepatch signatures against MOK keyring and record hashes in IMA log before applying ftrace redirect. (1 tasks)
- **AGY-2380**: Cryptographic MOK livepatch signature gate and IMA measurement logger in mios-livepatch  (WS-BOOT | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Livepatch manager validates MOK signatures and logs IMA measurements before applying kernel patches.
  - *Why:* Cryptographic livepatch verification allows zero-downtime CVE remediation while preventing unauthorized kernel code injection.

### Domain: Verify remote TPM quotes against pre-enrolled SSOT declarations and onboard authenticated blades automatically. (1 tasks)
- **AGY-2128**: Automated RFC 9334 RATS remote TPM 2.0 quote verifier and zero-touch cluster onboarding daemon  (WS-NODE | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Attestation daemon authenticates pre-enrolled blades and provisions cluster mesh access automatically.
  - *Why:* Automated remote attestation delivers zero-touch bare-metal scaling with complete cryptographic assurance.

### Domain: Virtualization/NBDTest (1 tasks)
- **T-807**: Automated 100-microVM concurrent boot latency (<15ms) and shared SquashFS NBD test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates instant microVM concurrency, template sharing, and isolated RAM overlay execution.

### Domain: Virtualization/SquashFSNBD (1 tasks)
- **T-806**: SquashFS template streaming over Unix-socket NBD with ephemeral RAM overlay in mios-microvm
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Virtualization manager streams SquashFS templates over NBD and boots microVMs in <15ms.

### Domain: Virtualization/VMSnap (1 tasks)
- **T-872**: Ephemeral microVM memory snapshot hibernator and instant RAM restorer in mios-microvm-snap
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Virtualization manager hibernates microVMs in <20ms and restores execution in <10ms.

### Domain: Virtualization/VMSnapTest (1 tasks)
- **T-873**: Automated microVM snapshot latency (<20ms), instant resume (<10ms), and state test suite
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Test suite validates sub-20ms snapshot dump, sub-10ms resume latency, and perfect guest state preservation.

### Domain: Virtualization/vGPU (1 tasks)
- **T-472**: Automated SR-IOV and mdevctl mediated vGPU slice provisioner
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: Mediated vGPU slices provision and attach to virtual machines automatically based on SSOT configuration.

### Domain: WSL/Supply-chain (1 tasks)
- **T-216**: WSL-03 -- `.wslconfig` / image hygiene + WSL self-verify cosign
  - *Acceptance:* WHEN verified THE SYSTEM SHALL satisfy: the `.wslconfig` template ships with `sparseVhd` and `autoMemoryReclaim`; the WSL updater refuses an unsigned or mis-signed image on pull; rootful quadlets carry `UserNS=auto`.

### Domain: Wake sleeping cluster blades securely via authenticated proxy peers using hardware SecureON passwords. (1 tasks)
- **AGY-2121**: Signed Proxy WoL with SecureON payload and peer wake daemon  (WS-NODE | P1 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Proxy WoL daemon wakes sleeping blades securely on incoming workload dispatch.
  - *Why:* Authenticated remote wake enables low-power cluster standby while maintaining instant node availability.

### Domain: Weight recent operational facts higher than obsolete historical records during semantic memory search. (1 tasks)
- **AGY-1973**: Temporal decay scoring on memory retrieval vectors to prioritize recent system state changes  (WS-RAG | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Retrieval scoring balances semantic similarity with recency decay factors dynamically.
  - *Why:* System configuration and environment states change over time; stale memory entries cause agents to make outdated assumptions.

### Domain: Work that was verified and committed stays in the tree. (1 tasks)
- **AGY-1732**: Stop concurrent writers silently reverting committed work  (WS-PROCESS | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a rewrite that drops a registration fails before it can be committed.
  - *Why:* the repository's guarantees are only as good as the edits that survive; a silent revert of a gate removes a guarantee without removing its record.

### Domain: Wrap subagent tool commands in unprivileged Landlock + bwrap namespaces to isolate rootfs and network in <5ms. (1 tasks)
- **AGY-2488**: Declarative Landlock and Bubblewrap ephemeral sandbox wrapper in mios-exec-sandbox  (WS-SEC | P1 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Execution sandbox isolates untrusted commands in <5ms and blocks unauthorized filesystem modifications.
  - *Why:* Unprivileged Landlock and bubblewrap sandboxing guarantees subagents cannot harm host files or escape execution boundaries.

### Domain: `.tmpl` units are declared like the rest. (1 tasks)
- **AGY-1838**: Template units are shipped but not projected  (WS-UNITS | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: every file in the unit directories is either projected or explicitly declared authored.
  - *Why:* the fourth open campaign requires every file to be generated-and-gated or explicitly authored.

### Domain: `After=` and `Requires=` name units that are shipped. (1 tasks)
- **AGY-1841**: Unit ordering constraints are not verified against the units that exist  (WS-UNITS | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: a reference to a nonexistent unit fails, and a reference to a base-OS unit does not.
  - *Why:* a dangling ordering constraint is silently ignored by systemd at boot, so nothing else will report it.

### Domain: `_install_core bootc` runs bootc. (1 tasks)
- **AGY-1751**: Stop mios-bootstrap swallowing the install mode  (WS-DEPLOY | P0 | S)  **DONE**
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: the requested mode is the mode that runs, and an unknown mode is an error.
  - *Why:* the offline kickstart path routes through this file, so an operator asking for the immutable install currently gets the mutable one and is told it succeeded.

### Domain: `apropos mios` and `man -k` answer, not just `man mios`. (1 tasks)
- **AGY-1733**: Give the man pages the reader the operating system indexes  (WS-DOCS | P2 | S)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `apropos mios` returns the verb pages on a booted system, and the mechanism that builds the index is named.
  - *Why:* a manual that only answers when you already know the page name is half a manual.

### Domain: `drift-gate-index.tsv` describes the gate that actually runs. (1 tasks)
- **AGY-1816**: The gate index is generated but its ordinals are never checked against the runner  (WS-GATE | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: reordering two checks in `main()` without regenerating the index fails a check.
  - *Why:* every doc and task that cites "check 31" is citing this file.

### Domain: `env-baseline.txt` reflects the SSOT, not the capturing shell. (1 tasks)
- **AGY-1859**: The env baseline is captured from a clean env but not proven clean  (WS-HOSTDEP | P2 | M)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: capturing with `MIOS_*` set in the shell fails rather than recording them.
  - *Why:* the baseline is the comparison every env drift-check depends on.

### Domain: `stonith-enabled=false` is correct on the one-node cluster the unit creates and is how split-brain corrupts data once a peer exists. (1 tasks)
- **AGY-2586**: Fail closed on unfenced multi-node Pacemaker, reading the live nodelist  (WS-MINI | P0 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: Unfenced is reachable only at exactly one node, the guard reads the live nodelist, and `pacemaker-unfenced` retires itself from `[blades.hazards].accepted`.
  - *Why:* This is the other half of T-333's Done-When, and the one whose failure mode is silent data corruption rather than a service that does not start.

### Domain: `tests/drift-gate-negatives.sh` covers every check, not a subset. (1 tasks)
- **AGY-1813**: Negative tests exist for gates that never had one  (WS-GATE | P1 | L)
  - *Acceptance:* WHEN verified THE SYSTEM SHALL: `check_negative_test_coverage` reports full coverage and the suite passes.
  - *Why:* a gate with no negative test is a gate nobody has ever seen fail.

## 2. Invariants & Lessons Learned
- Task half-lives decay exponentially with commit drift and calendar days.
- Broken file anchors are the strongest leading indicator of task obsolescence.
- Historical reasoning is preserved losslessly for future architectural synthesis.