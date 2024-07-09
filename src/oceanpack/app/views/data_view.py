# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-14
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import pandas as pd
from oceanpack.app.models.filesource import FileSourceModel



class DataConversionView:
    @staticmethod
    def display(model: FileSourceModel):
        print( "-------------+------------------------")
        print(f" Data source : {model.source_type.value}")
        print(f" Start date  : {pd.to_datetime(model.ds.time[0].values)}")
        print(f" End date    : {pd.to_datetime(model.ds.time[-1].values)}")
        print( "-------------+------------------------")
