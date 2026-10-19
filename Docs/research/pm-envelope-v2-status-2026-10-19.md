# PM envelope v2: incomplete run; process no longer present

## Current process and qualification audit

A read-only audit on 19 October 2026 finds original PID `31589` absent, no matching `measure_pm_envelope_v2.py` command, and the original tool session `75295` missing. The directory contains 73 of 93 completed coarse-control results, no nested-grid result, and no final `result.json`. The exit cause was not captured; this is neither a successful completion nor evidence of an out-of-memory failure. No process was stopped or restarted by this audit.

All eight prospective informative controls completed. None passes the frozen joint late carrier/beta requirement: four have informative late carrier ranges, but all eight fail late beta precision. Their truth-coverage flags remain preserved. This is already a failed necessary gate, while the full 93-control/12-grid evaluation remains incomplete. Missing cases and all 73 result hashes are retained in the [state-audit receipt](pm-envelope-v2-state-2026-10-19.json). No new Bass inference is permitted from this attempt.

The original run was invoked without `--source`; its source-request flag is false and there are no source-result artifacts. The design, execution binding and original tool hashes still match their frozen identities. The audit performs no extraction, recording decode, numerical rerun, threshold change or production change.

## Earlier preregistration status

At the earlier preregistration, status on19October2026: the complete93-control and12 nested-grid evaluation is **incomplete**. No recording inference or source PCM decoding has occurred in this attempt. Early passing synthetic controls cannot qualify the full method. This preregistration commit preserves the unchanged protocol and implementations while the original complete run continues. It does not change production synthesis, factory voices, noise behavior or the b14 release.

The [protocol](pm-envelope-v2-protocol-2026-10-19.json) was frozen before implementation/evaluation. The [original tool](../../Tools/measure_pm_envelope_v2.py) must finish every numerical gate before its explicit source option can decode the fixed recording. All56 reused control-waveform identities were checked before new extraction. Independent high-precision finite-cell enclosure checks passed; these are finite numerical tests, not certified error bounds or demonstrated envelope recovery.

A [separate performance wrapper](../../Tools/measure_pm_envelope_v2_fast.py) skips only phase constraints whose complete candidate radius is at least pi and whose centers are finite. Six completed synthetic cases produced identical scientific structures and NPZ arrays. Mixed wall timings under concurrent load do not establish a speedup, and no full fast-run replacement was started. The authoritative original evaluation remains unchanged.

Original binding: `build/pm-envelope-v2-20261019/execution-binding-v1.json` SHA256 `4f8781d50a8f82fa8d5673c7fb225e72c0950c50707889f44aa50a00a42409b7`. Independent enclosure receipt: `build/pm-envelope-v2-independent-run-001/result.json` SHA256 `d39880b1b5d5d1d264cd532c7d7d0bbf1dc368fc8f49c64766bfeaa650f54d42`. Performance equivalence: `build/pm-envelope-v2-performance-20261019/equivalence-result.json` SHA256 `a858f0ca42db6078a5776a1fb61a82e36be4adb009ad48b08b2900f0e0d35590`. These local artifacts are retained; they are not hardware recordings or a final successful method receipt.

- `Docs/research/pm-envelope-v2-protocol-2026-10-19.json`: `7f36c537159b609f4b620d8c9b24271bbf83c0fceb7a49ee6e8d1e78f3d37e25`
- `Tools/measure_pm_envelope_v2.py`: `a07e815c6f4307988e7a536826040be95b1c85a7fe009fe0dc2cd354a5c68367`
- `Tools/measure_pm_envelope_v2_fast.py`: `bd47b38e5135c7f33b9e381d77c00ffd18ba1a7b831cc2b090e8568446d5c0c9`
