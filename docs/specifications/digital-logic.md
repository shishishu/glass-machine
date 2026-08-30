# Digital logic specification v1

## Values

M0 uses four explicit states:

- `0`: driven logical low;
- `1`: driven logical high;
- `X`: unknown or conflicting logical value;
- `Z`: undriven/high-impedance value.

Vectors are non-empty, explicitly sized and written most-significant bit first. Width mismatches are
errors; GlassMachine does not silently truncate or extend values.

## NOT

The M0 ground-truth table is:

| Input | Output |
| --- | --- |
| `0` | `1` |
| `1` | `0` |
| `X` | `X` |
| `Z` | `X` |

`Z` becomes `X` because an undriven input does not establish a known Boolean level. This is a
digital abstraction, not a transistor-voltage claim.

## Drivers

M0 permits exactly one registered driver per signal. External input signals are driven by the
experiment API. Multiple-driver resolution is intentionally deferred; attempting to register a
second driver fails during circuit construction.
