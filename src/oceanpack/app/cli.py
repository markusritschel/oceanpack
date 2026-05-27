# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-13
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""Command-line interface for OceanPack, providing commands to convert, process, and merge instrument log files."""
import click
from colorama import Fore

from oceanpack.app.controllers.data_controller import (
    DataConversionController,
    DataMergeController,
    DataProcessingController,
)

welcome_msg = Fore.BLUE + r"""
                                                __  
  ____  ________  ____ _____  ____  ____ ______/ /__
 / __ \/ ___/ _ \/ __ `/ __ \/ __ \/ __ `/ ___/ //_/
/ /_/ / /__/  __/ /_/ / / / / /_/ / /_/ / /__/ ,<   
\____/\___/\___/\__,_/_/ /_/ .___/\__,_/\___/_/|_|  
                          /_/                       

    A command line interface for working with data 
          from the OceanPack™ by SubCtech©.
""" + Fore.RESET


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(welcome_msg)
        click.echo(ctx.get_help())


@main.command
@click.argument('path', type=click.Path(exists=True))
@click.option('--source-type', '-t', type=click.Choice(['Analyzer', 'NetDI', 'Stream']))
@click.argument('output_file', type=click.Path())
def convert_data(path, source_type, output_file):
    """
    Process OceanPack log file(s) from PATH, clean the data, and export to OUTPUT_FILE.
    Please process files from different source types separately.
    """
    controller = DataConversionController(source_type)  # DataController(source_model)
    controller.load_data(path)
    controller.display()
    controller.generate_output(output_file)
    click.echo("As a next step, run `merge-data` to merge the converted files into a single dataset. "
               "Consider providing a netCDF file with additional variables such as GPS coordinates"
               "or `SST` measured outside the ship near the water intake. See the documentation for"
               "more information about this.")


@main.command
@click.argument('files', type=click.Path(exists=True), nargs=-1)
@click.option('--output-file', '-o', type=click.Path(), help='Path for the merged netCDF output file.')
@click.option('--tolerance', '-t', type=str, default='2min', show_default=True,
              help='Maximum time offset allowed when aligning timestamps across input files (pandas offset string, e.g. "2min", "30s").')
@click.option('--keep-all', is_flag=True, default=False,
              help='Retain all variables from the input files. By default only the scientifically relevant subset is kept.')
def merge_data(files, output_file, tolerance, keep_all):
    """
    Merge multiple netCDF FILES produced by the convert-data step into a single dataset.
    Timestamps are aligned across files using nearest-neighbour matching within TOLERANCE.
    Unless --keep-all is set, the output is trimmed to a curated set of scientifically
    relevant variables. The merged dataset is written to OUTPUT_FILE in netCDF format.
    """
    kwargs = {'keep_all': keep_all}
    controller = DataMergeController()
    controller.merge(files, tolerance=tolerance, **kwargs)
    controller.generate_output(output_file)


@main.command
@click.argument('path', type=click.Path(exists=True))
def process_data(path):
    """
    Run the physical-variable processing pipeline on the merged netCDF file at PATH.
    The pipeline performs four steps in order: (1) convert raw Latitude/Longitude to
    decimal-degree coordinates, (2) mask CO2 readings during non-operating instrument
    phases, (3) derive equilibrator pressure from cell pressure and internal differential
    pressure, and (4) compute pCO2 in wet air at the equilibrator. The processed dataset
    is written back to PATH, overwriting the input file in place.
    """
    controller = DataProcessingController()
    controller.load_data(path)
    controller.process_data()
    controller.generate_output(path)


if __name__ == "__main__":
    main()
