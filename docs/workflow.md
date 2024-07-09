# An example workflow

This page demonstrates a typical workflow from raw log files retrieved from the OceanPack to a processed dataset ready for further analysis.

```{admonition} Using the command line interface (CLI)
:class: tip

Once the package is installed, you have access to a [command-line interface](cli.md) that helps you convert and process the log files from the OceanPack.
While the final data analysis should be done in form of individual Python scripts or Jupyter notebooks, the processing of the raw files follows a standardized routine for which the CLI provides a set of easy-to-use commands.
```

## Convert raw OceanPack log files to netCDF

Before we can actually evaluate the data, we must convert the raw data into a more accessible format.
The CLI provides a command to convert the raw data into a netCDF file.
We perform this step for each type of logging unit of the OceanPack.

```bash
oceanpack convert-data ./Analyzer/ analyzer.nc
oceanpack convert-data ./NetDI/ netdi.nc
```

Here, we assume that the raw files retrieved from the OceanPack reside in the respective directories `Analyzer` and `NetDI`.


## Combine the datasets

Next, we combine the two datasets into a single dataset.
This will create a new netCDF file, thereby dropping all variables that are not needed for common analysis.

```bash
oceanpack merge-data ./analyzer.nc ./netdi.nc -o ./combined.nc
```

```{note}
If you need to keep all data from the original files even in the combined file, you can use the `--keep-all` flag.
```


## Process the data

The final step is to process the data to convert coordinates from the GPS unit, compute the pressure at the equilibrator, and perform some CO2 calculations.

```bash
oceanpack process-data ./combined.nc
```

This command will perform the following steps:

1. Coordinate conversion
2. Remove non-operating phases
3. Pressure at the equilibrator
4. Compute the pCO2 at the equilibrator in wet air
5. Temperature correction (not implemented yet)
6. Compute the fugacity (not implemented yet)


```{warning}
Keep in mind that this command will overwrite the input file.
However, it will only create new variables in the file, so you can always get back to the original data.
```

### Coordinate conversion

Coordinates retrieved from the OceanPack NetDI unit have the format `ddmm.mmmm`.
The first step in the data processing is to convert these coordinates into decimal degrees.


### Remove non-operating phases

The OceanPack typically undergoes different phases during measurement.
These include calibration phases with different span gases, zero gases, and the actual measurement phase (for more details see the official documentation).
To work with the final CO2 data, we want to remove the non-operating state phases.
This is done by removing all data points where the `Status` variable is not `Operational` (usually value 5).
Here, all phases in which the values are different than 5 are removed, plus a buffer period afterward to account for the time it takes for the OceanPack to stabilize after a phase change.


### Pressure at the equilibrator

To be able to convert the xCO2 concentration registered by the OceanPack into actual partial pressure, we need to do some preparation.

According to {cite:t}`dickson_guide_2007`, SOP 4, the partial pressure of carbon dioxide in air, which is in equilibrium with a sample of seawater, is defined as the product of the mole fraction of CO2 in the equilibrated gas phase and the total pressure of equilibration $p_\text{equ}$:

$$
\begin{equation*}
pCO_2 = xCO_2 \cdot p_\text{equ}
\end{equation*}
$$

However, the pressure at the equilibrator is not registered by the OceanPack.
Instead, the OceanPack registers the pressure in the measurement cell (`CellPress`) and the difference pressure to the equilibrator (`DPressInt`).
Here, to estimate the pressure at the equilibrator/membrane, we build a 2-minutes rolling mean of the `DPressInt` and subtract it from the `CellPress`.


### Compute the pCO2 at the equilibrator in wet air

After having computed the pressure at the equilibrator, we can now compute the partial pressure of CO2 in wet air, corresponding to the formula shown above.
The OceanPack's analyzer measures the xCO2 concentration in wet air.
Note that $p_\text{equ}$ must be in units of Pa!


### Temperature correction
:::{warning}
This is not implemented yet.
:::

Often, when doing measurements at sea, the temperature at the equilibrator and the temperature at the water intake differ.
This can be taken into account by correcting the xCO2 concentration to the sea surface temperature (SST).
The correction used here follows {cite:t}`takahashi_climatological_2009`:

$$
\begin{equation*}
{(xCO_2)}_{SST} = {(xCO_2)}_{T_\text{equ}} \cdot \exp{\Big(0.0433\cdot(SST - T_\text{equ}) - 4.35\times 10^{-5}\cdot(SST^2 - T_\text{equ}^2)\Big)}
\end{equation*}
$$

```{tip}
If the measurements were taken onboard a ship, the way for the water from the intake to the OceanPack might be quite long. In that case, one should first perform a lag analysis and correct the time series of the intake temperature accordingly.
```


### Compute the fugacity
:::{warning}
This is not implemented yet.
:::

Finally, we compute the fugacity by hands of the before calculated partial pressure, the pressure at the equilibrator, and the SST.

According to {cite:t}`dickson_guide_2007` (e.g. the example in SOP 24, page 4 f.), the fugacity can be calculated via

$$
\begin{equation*}
(fCO_2)^\text{wet}_\text{SST} = (pCO_2)^\text{wet}_\text{SST} \cdot
        \exp{\Big(p_\text{equ}\cdot\frac{\left[ B(CO_2,SST) + 2\,\left(1-(xCO_2)^\text{wet}_{SST}\right)^2 \, \delta(CO_2,SST)\right]}{R\cdot SST}\Big)}
\end{equation*}
$$

where $SST$ is the sea surface temperature in Kelvin, $R$ the gas constant and $B(CO_2,SST)$ and $\delta(CO_2,SST)$ are the virial coefficients for CO2 (both in $\text{cm}^3\,\text{mol}^{-1}$), which are given as

$$
\begin{equation*}
B(CO_2,T) = -1636.75 + 12.0408\,T - 0.0327957\,T^2 + 0.0000316528\,T^3
\end{equation*}
$$

and

$$
\begin{equation*}
\delta(CO_2,T) = 57.7 - 0.188\,T
\end{equation*}
$$

following {cite:t}`weiss_carbon_1974`.
Again, $p_\text{equ}$ is in units of Pa.