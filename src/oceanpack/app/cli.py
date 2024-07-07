# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-13
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""Console script for oceanpack."""
import click
from colorama import Fore, Back, Style
from oceanpack.app.controllers.data_controller import DataController


welcome_msg = Fore.BLUE + """
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
    controller = DataController(source_type)
    controller.load_data(path)
    controller.display()
    controller.write_output(output_file)


if __name__ == "__main__":
    main()