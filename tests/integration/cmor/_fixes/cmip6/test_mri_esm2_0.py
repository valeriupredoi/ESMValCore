"""Test fixes for MRI-ESM2-0."""
import unittest

from esmvalcore.cmor._fixes.cmip6.mri_esm2_0 import Cl, Cli, Clw
from esmvalcore.cmor._fixes.fix import Fix


def test_get_cl_fix():
    """Test getting of fix."""
    fix = Fix.get_fixes('CMIP6', 'MRI-ESM2-0', 'Amon', 'cl')
    assert fix == [Cl(None)]


@unittest.mock.patch(
    'esmvalcore.cmor._fixes.cmip6.mri_esm2_0.BaseCl.fix_metadata',
    autospec=True)
def test_cl_fix_metadata(mock_base_fix_metadata):
    """Test ``fix_metadata`` for ``cl``."""
    fix = Cl(None)
    fix.fix_metadata('cubes')
    mock_base_fix_metadata.assert_called_once_with(fix, 'cubes')


def test_get_cli_fix():
    """Test getting of fix."""
    fix = Fix.get_fixes('CMIP6', 'MRI-ESM2-0', 'Amon', 'cli')
    assert fix == [Cli(None)]


@unittest.mock.patch(
    'esmvalcore.cmor._fixes.cmip6.mri_esm2_0.Cl.fix_metadata',
    autospec=True)
def test_cli_fix_metadata(mock_base_fix_metadata):
    """Test ``fix_metadata`` for ``cli``."""
    fix = Cli(None)
    fix.fix_metadata('cubes')
    mock_base_fix_metadata.assert_called_once_with(fix, 'cubes')


def test_get_clw_fix():
    """Test getting of fix."""
    fix = Fix.get_fixes('CMIP6', 'MRI-ESM2-0', 'Amon', 'clw')
    assert fix == [Clw(None)]


@unittest.mock.patch(
    'esmvalcore.cmor._fixes.cmip6.mri_esm2_0.Cl.fix_metadata',
    autospec=True)
def test_clw_fix_metadata(mock_base_fix_metadata):
    """Test ``fix_metadata`` for ``clw``."""
    fix = Clw(None)
    fix.fix_metadata('cubes')
    mock_base_fix_metadata.assert_called_once_with(fix, 'cubes')
