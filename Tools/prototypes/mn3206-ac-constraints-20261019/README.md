# MN3206 AC constraint oracle

This standard-library prototype reads only the retained manufacturer's typical
THD-versus-level graph under its explicit 5 V / 40 kHz CP / 1 kHz conditions.
It is not an audio processor or a model of the target keyboard's signal level.
Its input is a named manufacturer-axis dBm coordinate: the retained p76 table
does not define a voltage reference, so this component provides no Vrms/dBm
conversion. The p76 0.25 Vrms THD anchor remains separate.

The entire reading design, 13 raw coordinates, omitted grid-confounded point,
condition policy and 64 coordinate scenarios were frozen before implementation
in `design-frozen.json`. The source checks that exact design's hash.

```python
from fractions import Fraction
from mn3206_ac import MN3206AC
model = MN3206AC()
conditions = dict(mode='typical_thd_graph_only',
    axis_reference='manufacturer_dbm_reference_unspecified',
    vdd_v=5, vgg_v=Fraction(14,3), vss_v=0, cp_hz=40000,
    signal_hz=1000, temperature_c=25, lpf_hz=20000,
    lpf_db_per_octave=-48)
reading = model.thd_constraint(-12, **conditions)
```

Every condition is mandatory and exact. VGG also accepts its one nearest
binary64 representation; this is a representation alias, not a voltage tolerance.
Extrapolation, unspecified-reference substitutions, other conditions and invalid
numbers reject. The returned range spans declared reading scenarios, not part
variability, measurement confidence, or all possible traces within pixel boxes.

Run `python3 -S Tools/prototypes/mn3206-ac-constraints-20261019/check.py PATH.json`
from the repository root. The output path must not exist. Local retained source
images/PDF are required for the acquisition hash checks; model queries themselves
need only the prototype's small tracked source and design. The check creates no
sound and needs no third-party modules.
