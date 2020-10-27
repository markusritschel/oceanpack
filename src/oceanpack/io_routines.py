#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   23/04/2020
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from __future__ import absolute_import, division, print_function, with_statement

import numpy as np
import pandas as pd


def _read_oceanpack_file(file, **kwargs):
    """Read an OceanPack log file. (Files are Windows-formatted.)"""
    with open(file, 'r', encoding='Windows 1252') as f:
        line_counter = 0
        while True:
            line = f.readline()
            line_counter += 1
            if line.startswith('@RATE'):
                break
            elif line.startswith('@SENSOR'):
                sensors = line.strip().split(',')
            elif line.startswith('@NAME'):
                names = line.strip().split(',')
            elif line.startswith('@UNIT'):
                units = line.strip().split(',')

    df = pd.read_csv(file, sep=',', skiprows=line_counter, names=names, parse_dates=[['DATE', 'TIME']],
                     usecols=np.arange(len(names)), **kwargs)  # usecols omits last column which gets created if lines end with a colon

    # parse date and time and set as index
    df['DATE_TIME'] = pd.to_datetime(df['DATE_TIME'])
    df.set_index('DATE_TIME', inplace=True)

    # clear data
    df.drop(['@NAME', 'DATE', 'TIME', 'DATE_TIME'], axis=1, inplace=True, errors='ignore')

    return df  # TODO: maybe export as xarray and also add units etc. as attributes


def read_oceanpack(files):
    """Read a single or multiple log files into a pd.DataFrame dataset."""
    if isinstance(files, str):
        files = [files]
    elif not isinstance(files, list):
        raise IOError("Input must be either str or list")

    df_list = []
    for file in files:
        df = _read_oceanpack_file(file)
        df_list.append(df)

    df = pd.concat(df_list, sort=False)

    df.sort_index(axis=0, inplace=True, ascending=True)

    return df
