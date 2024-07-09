# The Command Line Interface

The package also includes a command line interface (CLI) that can be used for some basic tasks, which include:

- processing of the data
- data cleansing
- quality control
- basic plots

If you install the package in your environment (following the instructions [here](index.md#installation)), you will also have access to an executable command `oceanpack` which you can run from the terminal.

The CLI includes basic help messages to guide you through the interface.

## Data conversion

```bash
oceanpack convert-data [OPTIONS] PATH OUTPUT_FILE
```

This command takes a path as the first argument pointing either to a single file or a directory containing multiple files.
These files should stem from the OceanPack and be retreived either via USB-Stick transfer (from the NetDI or the Analyzer unit) or via stream from the OceanView&copy; software provided by SubCtech.

If the source type (Analyzer, NetDI, Stream) is not specified, the CLI will try to infer the source type from the header and the file path.
If you experience issues with this, you can set the source type manually by specifying the option `-t` or `--source-type`.

The second required argument is the path of the output file. This file will be either a CSV or a netCDF file, depending on the file extension you provide.
If you choose netCDF as output format, the CLI will also save attributes to each variable in the file.

The following steps are performed by the `convert-data` command:

1. Read the data from the source file(s)
2. Parse the data
3. Clean the data
4. Save the data to the output file
5. Print a summary/report of the data


## Merging data

The `merge-data` command is used to combine multiple datasets into a single dataset.
This command is useful if you have data from different sources that you want to combine into a single dataset.

```bash
oceanpack merge-data [OPTIONS] [FILES]... -o OUTPUT_FILE
``` 

The command takes a list of files as input and combines them into a single file.
The output file will be a netCDF file containing a selection of variables from the input files that are required for further analysis.
If you want to keep all variables from the input files, you can use the `--keep-all` flag.


