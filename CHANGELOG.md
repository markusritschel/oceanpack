# Change Log

All notable changes to this project will be documented in this file.
<!-- This project adheres to [Semantic Versioning](http://semver.org/) -->

## Unreleased

- `process-data` now writes the fugacity of CO2 alongside the partial pressure. Output
  variables are `lat`, `lon`, `PressEqu`, `pCO2_wet_equ` and `fCO2_wet_equ`.
- The Takahashi (2009) temperature correction is available via
  `DataProcessor.compute_temperature_correction(sst_var=...)`, but is skipped by default:
  an Analyzer log has no in-situ temperature independent of the equilibrator, and
  correcting a temperature to itself would ship an identity under a corrected label. With
  an intake temperature merged in, `pCO2_wet_sst` / `fCO2_wet_sst` are written instead.
- `lat` / `lon` are now labelled `degrees_north` / `degrees_east` instead of inheriting the
  raw NMEA `ddmm.mmmm` unit from the source variables.
- `remove_non_operating_phases` keeps the variable attributes it used to drop.
- Fixed `set_nonoperating_to_nan` raising on a file that is fully operational throughout.
- Known limitation: the sign convention of `DPressInt` is unconfirmed and `PressEqu` may
  carry a ~2 % bias — see the warning in `docs/cli.md`.

## 0.1.0

- _TODO: Update_
