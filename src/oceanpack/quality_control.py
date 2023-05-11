# !/usr/bin/env python3
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   2022-10-26
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""This module contains routines for quality control."""
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import logging
from oceanpack import SYSTEM_STATES

logger = logging.getLogger()


def infer_freq(df: pd.DataFrame):
    """Infer the sampling frequency from a :class:`pandas.DataFrame`."""
    f = pd.infer_freq(df.index[:100])
    print(f"Logging frequency seems to be 1/{f}")
    return


def print_operating_states(df: pd.DataFrame, state_var="STATUS"):
    """Print a list of all operating phases in the dataset."""
    print("The dataset contains the following phases:")
    status_flags = list(df[state_var].unique())
    for i in sorted(status_flags):
        if not i in SYSTEM_STATES.keys():
            logger.warning(f"Couldn't find key `{i}` in SYSTEM_STATES dict")
        else:
            print(f"{i:0>2} : {SYSTEM_STATES[i]}")

    return status_flags


def plot_calibration_overview(data: pd.DataFrame, state_var="STATUS", statusflag: int=1, thrsh=300):
    """Make an overview plot of the calibration phases.

    Parameters
    ----------
    df : pd.DataFrame
        The data set containing the whole time series
    state_var : str
        The variable that holds all the status variables
    statusflag : int
        The flag of the current status
    thrsh : int
        Threshold in seconds that is used to distinguish between phases
    """
    df = data[data[state_var]==statusflag]

    plt.figure(figsize=(15,5))
    gs = plt.GridSpec(nrows=1, ncols=3, width_ratios=[3,1,1])

    status_desc = SYSTEM_STATES.get(statusflag, '-- no description found --')
    logger.info(f"Process status {statusflag} ({status_desc})")
    plt.suptitle(f"Statusflag {statusflag} ({status_desc})")

    if state_var not in df.columns:
        logger.info(f"{state_var} not found in data set. Use fallback `ANA_state`")
        if 'ANA_state' not in df.columns:
            logger.error("`ANA_state` not found in data set. Cannot proceed further.")

    gap_ends = df.index.to_series().diff().dt.seconds > thrsh  # gives a boolean array with True at the end of each interval
    periods = gap_ends.cumsum()

    histkw = dict(binwidth=25, stat='frequency', color='r')

    ax = plt.subplot(gs[0])
    df['CO2'].plot(ls='none', marker='.')
    for g, subdf in df['CO2'].groupby(periods):
        if np.abs(subdf.median() - df['CO2'].median()) > 2.5:
            subdf.plot(ls='none', marker='x', ms=5, color='red')
        plt.text(subdf.index[0], subdf.median()-20, f"{subdf.median():.2f}", fontsize='x-small', ha='center', va='top', rotation=90)
    plt.xlabel('')

    plt.text(.01, .99, f"Median value of all calibration phases: {df['CO2'].median():.2f}", transform=ax.transAxes, va='top', fontsize='small')

    ax = plt.subplot(gs[1])
    sns.histplot(y=df['CO2'], **histkw)

    # Plot H2O and H2O dew for every calibration phase
    ax = plt.subplot(gs[2])
    sgs = gs[2].subgridspec(2, 1)

    ax_h2o = plt.subplot(sgs[0])
    ax_h2o.set_ylabel('H2O', fontsize='small')

    ax_h2odew = plt.subplot(sgs[1])
    ax_h2odew.set_ylabel('H2Odew', fontsize='small')
    ax_h2odew.set_xlabel("Measurements in\nevery calibration phase")

    for i, (g, subdf) in enumerate(df.groupby(periods)):
        if np.abs(subdf['CO2'].median() - df['CO2'].median()) > 2.5:
            logger.warning(f"The median of phase {g} (starting at {subdf.index[0]}) differs by more than 2.5 units from the overall median.")
            continue

        ax_h2o.plot(subdf['H2O'].values, lw=1, alpha=.7)
        ax_h2odew.plot(subdf['H2Odew'].values, lw=1, alpha=.7, label=g)

    plt.tight_layout()