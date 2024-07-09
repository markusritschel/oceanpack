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

For more details, see the corresponding section in the [CLI documentation](cli.md#processing-data).
