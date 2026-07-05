# N-CMAPSS DS01 Unit-Cycle Processing Artifact

This artifact documents processing of NASA Turbofan Engine Degradation Simulation Data Set 2 / N-CMAPSS DS01.

The raw HDF5 development split contains 4,906,636 high-frequency observations. These were aggregated to a unit-cycle panel with one row per engine unit and cycle.

Processed output:

- Panel rows: 553
- Units: 6
- Cycle range: 1 to 100
- Duplicate unit-cycle rows: 0

Entity index: `unit`  
Time index: `cycle`

Core modelling variables:

- `risk`
- `rul`
- `degradation_index`
- `sensor_mean_z`
- `pc1`
- `pc2`
- `pc3`
- `op_setting1`
- `op_setting2`
- `op_setting3`
- `op_setting4`
- `Fc`
- `hs`

This dataset is used as an extended data-processing and workflow smoke artifact, not as the sole dynamic-GMM validation benchmark.
