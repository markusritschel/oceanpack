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

import glob
import os
import pandas as pd
import pytest

from oceanpack import read_oceanpack

base_dir = os.path.dirname(os.path.abspath(__file__))
all_files = glob.glob(os.path.join(base_dir, '*.log'))


@pytest.mark.skipif(not all_files, reason="needs to find file for testing")
def test_read_single_file():
    df = read_oceanpack(all_files[0])
    assert type(df) == pd.DataFrame, "Should be pandas DataFrame object"


@pytest.mark.skipif(not all_files, reason="needs to find file for testing")
def test_read_multi_files():
    df = read_oceanpack(all_files)
    assert type(df) == pd.DataFrame, "Should be pandas DataFrame object"
