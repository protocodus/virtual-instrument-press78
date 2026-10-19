# Third-party notices

Press78's original source code is covered by the project's `LICENSE` file.
The build downloads or consumes the separate dependencies below; they are not
relicensed by Press78.

## JUCE 8.0.14

JUCE is Copyright (c) Raw Material Software Limited.

Repository: <https://github.com/juce-framework/JUCE/tree/8.0.14>

A copy of the JUCE licence text is vendored at
[`ThirdParty/JUCE-LICENSE.md`](ThirdParty/JUCE-LICENSE.md) so that it can be
included in every distributed bundle and installer package alongside Press78's
own licence, as the packaging script does.

License: JUCE framework modules are dual-licensed under the GNU Affero General
Public License version 3 (AGPLv3) and the commercial JUCE licence. Building or
distributing Press78 with JUCE therefore requires either compliance with the
AGPLv3 for the complete combined work or an appropriate commercial JUCE
licence. Review the JUCE 8 licence terms before distribution:
<https://github.com/juce-framework/JUCE/blob/8.0.14/LICENSE.md>

JUCE includes or interfaces with additional third-party components. The
bundled components' licence texts are collected in
[`ThirdParty/JUCE-DEPENDENCY-NOTICES.txt`](ThirdParty/JUCE-DEPENDENCY-NOTICES.txt),
with upstream paths and hashes. This file accompanies each distribution.
Regenerate it from the pinned JUCE checkout using
`Tools/collect_juce_notices.py`; JUCE's own `LICENSE.md` also indexes the sources. The VST3 SDK portions used through JUCE are identified
there as MIT-licensed; Apple's Audio Unit frameworks are supplied by the macOS
SDK and remain subject to Apple's terms.

## CLAP support

The CLAP plug-in uses the MIT-licensed `clap-juce-extensions` wrapper, pinned
to commit `c1a5ad025f95d01e03267857fa8276ebeed16500`:
<https://github.com/free-audio/clap-juce-extensions/tree/c1a5ad025f95d01e03267857fa8276ebeed16500>.
It is Copyright 2019-2020, Paul Walker. The complete upstream licence is
included in [`ThirdParty/CLAP-JUCE-EXTENSIONS-LICENSE.md`](ThirdParty/CLAP-JUCE-EXTENSIONS-LICENSE.md).

The wrapper brings in two dependencies at the revisions recorded by its
submodules:

- CLAP 1.2.7, commit `29ffcc273be7c7c651f6c9953b99e69700e2387a`:
  <https://github.com/free-audio/clap/tree/29ffcc273be7c7c651f6c9953b99e69700e2387a>.
  Its MIT licence is included in [`ThirdParty/CLAP-LICENSE.md`](ThirdParty/CLAP-LICENSE.md).
- CLAP helpers, commit `a61bcdf0ecc2c8db1e80bfe8bf9cb7e8d9fd2bbc`:
  <https://github.com/free-audio/clap-helpers/tree/a61bcdf0ecc2c8db1e80bfe8bf9cb7e8d9fd2bbc>.
  Its MIT licence is included in [`ThirdParty/CLAP-HELPERS-LICENSE.md`](ThirdParty/CLAP-HELPERS-LICENSE.md).

Both dependencies are Copyright (c) 2021 Alexandre BIQUE. These licence files
are included in every distribution archive and macOS installer package.

## Factory voice parameters

The 100 `PSS 00` … `PSS 99` factory voices in `Assets/FactoryBank/` and
`Source/DSP/FactoryVoices.h` are 33-byte parameter sets decoded from the
PSS-780 ROM voice SysEx archive published at
<https://github.com/BobanSpasic/PSS-Revive>. They are parameter data, not
sampled recordings or firmware, and they are **not** covered by this
repository's `LICENSE`. Their redistribution rights are unresolved: public
availability of the archive does not establish Yamaha's authorization. See
[`Assets/FactoryBank/provenance.json`](Assets/FactoryBank/provenance.json).
A commercial release needs a bank-specific rights review first.

Yamaha and PSS-780 are trademarks of their owners and are used here only to
identify the reference instrument. No sample, impulse response, recording or
firmware is included in this repository.
