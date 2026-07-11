# Model card: system_gmm_native

## Specification
- Dependent variable: `y`
- Regressors: `L1.y, x1, x2, control`
- Estimator: `System GMM`
- Steps: `twostep`
- Transformation: `fod`
- Collapse instruments: `True`
- Time dummies: `False`

## Instrument classification
### GMM-style
- `y`: lags 2:3
- `x1`: lags 2:2
- `x2`: lags 2:2
### IV-style / assumed exogenous
- `control`

## pydynpd command
```text
y L1.y x1 x2 control | gmm(y, 2:3) gmm(x1, 2:2) gmm(x2, 2:2) iv(control) | collapse
```

## Instrument-pressure heuristic
- Approximate instruments: `9`
- Instrument/entity ratio: `0.100`
- Risk: `low`