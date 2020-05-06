#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   13/04/2020
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from __future__ import absolute_import, division, print_function

import pandas as pd
import numpy as np
import os
import glob
import pytest

from oceanpack import read_oceanpack, ppm2µatm, temperature_correction

base_dir = os.path.dirname(os.path.abspath(__file__))
all_files = glob.glob(os.path.join(base_dir, '*.log'))


press_factors = [1, 100, 1/1013.25]   # hand over pressure as hPa, Pa, atm

@pytest.mark.skipif(not all_files, reason="needs to find file for testing")
@pytest.fixture(scope="session", params=press_factors)
def op_data(request):
    df = read_oceanpack(all_files)
    # df = set_nonoperating_to_nan(df, col=[x for x in df.columns if 'CO2' in x], shift="1min", status_var='STATUS')
    pressure_equ = df['CellPress'] - df['DPressInt'].rolling('2min').mean()  # in mBar
    df['p_equ'] = pressure_equ * request.param
    df['pCO2_wet_equ'] = ppm2µatm(df['CO2'], p_equ=df['p_equ'])

    return df


def test_format(op_data):
    assert type(op_data) == pd.DataFrame


def test_pCO2(op_data):
    assert np.allclose(op_data['pCO2_wet_equ'], op_data['CO2'], rtol=.05), "pCO2 and xCO2 values are not close enough"


def test_temp_correction(op_data):
    temp_equ = op_data['waterTemp']
    test_sst = temp_equ - .25  # create artificial difference in temperature
    op_data['pCO2_wet_sst'] = temperature_correction(op_data['pCO2_wet_equ'], test_sst, temp_equ)
    assert np.allclose(op_data['pCO2_wet_sst'], op_data['pCO2_wet_equ'], rtol=.05), "pCO2_wet_equ and pCO2_wet_sst not close enough"
