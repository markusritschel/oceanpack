# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-13
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""Console script for oceanpack."""
import click
from oceanpack.app.controllers.data_controller import DataController


@click.group()
def main():
    pass


@main.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--source-type', '-t', type=click.Choice(['Analyzer', 'NetDI', 'Stream']))
@click.argument('output_file', type=click.Path())
def process_data(path, source_type, output_file):
    """
    Process OceanPack log file(s) from PATH, clean the data, and export to OUTPUT_FILE.
    Important: Handle files from different source types separately.
    """
    controller = DataController(source_type)
    controller.load_data(path)
    controller.display()
    controller.write_output(output_file)


if __name__ == "__main__":
    main()