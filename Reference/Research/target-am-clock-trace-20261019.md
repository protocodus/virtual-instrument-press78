# Target AM-board clock area: partial copper ledger, 2026-10-19

The existing PSS-780 board photos reveal **nine local copper-connected pad groups and a corrected package orientation**, but still do not establish a numbered MN3102/MN3206 netlist. No new clock frequency, RC value association, supply voltage, BBD delay or DSP change follows from this pass. The [original source report](target-am-board-20261019.md) and its acquired images remain unchanged.

The originals are deepsonic's [component-side photograph](https://www.flickr.com/photos/deepsonic/10090241086/) and [copper-side photograph](https://www.flickr.com/photos/deepsonic/10090216715/), previously acquired from Commons under CC BY 2.0. Coordinates below refer to the original 2000 × 1335 copper JPEG, approximately ±3 pixels, rather than a transformed overlay. The [machine-readable ledger](target-am-clock-trace-20261019.json) binds originals, inspection crops, the earlier four-edge snapshot and the separate failed-registration record. Downloaded photographs remain ignored research artifacts, outside the instrument package.

## Orientation and registration

An unmirrored, rotation-only enlargement shows a centered **short-edge notch**, rather than a corner pin-1 dot, on IC2/MN3206 and the neighboring dark package. With the component-side top view rotated so that notch faces left, the near row reads pins 1–4 from left to right and the far row 8–5. Two independent inspections agree. The neighboring package's MN3102 reading remains provisional; the exact model's parts inventory supports that candidate but does not supply a reference-designator map.

The [independent registration pass](target-am-registration-v2-20261019.md) has not validated a whole-board transform. Its best exploratory fit still gives omitted-row errors up to 28.62 pixels, exceeding one pad pitch. The marked 68P, 390K and 2.7K parts therefore remain unassigned to copper-pad pairs. Their photographed bent leads do not securely reveal every board-plane entry point. The notch observation does not cure this geometric uncertainty.

## Direct copper observations

These are local visible connections, **not complete nets**. Group labels are deliberately anonymous: none is designated ground, supply, bias, clock or signal. A branch continuing outside the listed area is not considered absent.

| Group | Pad centers in the original copper image | Visible connection |
| --- | --- | --- |
| 01 | (1625,391), (1645,392) | Short broad horizontal bridge. |
| 02 | (1665,391), (1685,428) | Narrow diagonal between adjacent four-pad rows. |
| 03 | (1685,391), (1720,381) | Broad rising arm to the neighboring single pad. |
| 04 | (1665,428), (1720,411) | Broad U below the four-pad row. |
| 05 | (1647,483), (1654,518), (1692,518), (1673,571), (1711,571) | Connected branching copper area extending into both passive-pad rows. |
| 06 | (1684,483), (1673,518) | Descending branch; another branch continues outside this local group. |
| 07 | (1627,518), (1654,571) | Broad diagonal between passive-pad rows. |
| 08 | (1711,518), (1750,518) | U-shaped copper below the upper passive-pad row. |
| 09 | (1692,571), (1730,571), (1750,571) | Shared lower horizontal copper trace, with further continuation. |

The land near (1665,483), third in the lower four-pad row, has **no visible outgoing copper trace in this image**. This is a bounded photographic observation, not proof of an electrically unconnected component pin: the package-to-footprint identity is unaccepted, and a component-side connection or an unresolved small feature has not been excluded. It is particularly unsuitable as a basis for importing an oscillator example circuit.

Two nearby parallel routes initially looked joined in a coarse crop. The larger unwarped crop shows a separating gap, so that proposed join was rejected before inclusion in the ledger. This preserves the distinction between observed copper and an expected circuit topology. The original four anonymous edges were recorded before the later registration attempts and are retained unchanged.

## Manufacturer constraints and remaining unknowns

The previously acquired Panasonic MN3102 sheet places the illustrative resistor between OX2 pin 6 and OX1 pin 7, and the illustrative capacitor between OX3 pin 5 and OX1 pin 7. Their shared node is **not ground**. Those are example connections, not recovered target-board connections. The complementary CP outputs operate at half the oscillator frequency; neither a generic 555 equation nor a guessed resistor/capacitor pairing can establish the target clock.

The visible 68P, 390K and 2.7K markings remain useful component-location leads. Their exact electrical roles, tolerances, oscillator control input, rail/bias assignments and modulation path remain unresolved. No named target net, timing constant or nonlinear transfer is accepted here. This ledger can constrain a later trace reconstruction once independent footprint and component-hole correspondences are available.
