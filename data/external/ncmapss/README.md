# Fixed N-CMAPSS DS01 application panel

The two checked CSV files in this directory are fixed inputs for the JSS
leakage-control illustration. They were aggregated by unit and cycle from the
NASA N-CMAPSS DS01-005 development HDF5 data. The source processing summary
records 4,906,636 raw development rows, six units, 553 unit-cycle rows, cycles
1--100, and no duplicate unit-cycle keys. The historical generator was
`Scripts/Python/aggregate_ncmapss_ds01_unit_cycle.py` in the author's empirical
paper workspace.

For this replication package the CSV files are intentionally treated as fixed
external inputs: the multi-gigabyte HDF5 source is not redistributed or
downloaded during the reviewer run. The full unit-cycle panel retains the raw
physical sensor aggregates needed to fit the scaler and PCA separately inside
each training window. The compact file is retained for compatibility with the
earlier workflow. Neither file contains a lagged target regressor.

- Full panel: 553 rows, 35 columns, SHA-256
  `0533BF3246AB81516EA93EDBC5C7A2803A5448FC1B22E0C4298940714D4C13FE`.
- Compact panel: 553 rows, 17 columns, SHA-256
  `380F655D5877DAC48A503A0A635F1C16108BD6152D1F5BCBDFC8CEE9A1A2378C`.
- Manuscript use: leakage-controlled lagged-sensor baseline and cycle-ordered
  late-life holdout, not a formal dynamic-GMM application.
