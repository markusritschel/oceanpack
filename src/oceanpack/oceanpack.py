#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-12
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from __future__ import absolute_import, division, print_function, with_statement

import logging

logger = logging.getLogger(__name__)


def dummy_function(a: int, b: str) -> str:
    """This is a dummy function to showcase auto-generation of source code documentation. 
    Takes an integer and string as arguments and returns a string.
    
    Parameters
    ----------
    a : int
        The integer argument
    b : str
        The string argument

    Example
    -------
    >>> dummy_function(7, 'letters')
    '7 letters'
    """
    return f"{a} {b}"
