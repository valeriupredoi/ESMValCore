"""Fixes for NESM3 model."""
from ..cmip5.bcc_csm1_1 import Cl as BaseCl


class Cl(BaseCl):
    """Fixes for ``cl``."""


class Cli(Cl):
    """Fixes for ``cli``."""


class Clw(Cl):
    """Fixes for ``clw``."""
