"""Fixes for CESM2-FV2 model."""
from .cesm2 import Cl as BaseCl
from .cesm2 import Tas as BaseTas
from ..fix import Fix
from ..shared import fix_ocean_depth_coord


Cl = BaseCl


Cli = Cl


Clw = Cl


Tas = BaseTas


class Omon(Fix):
    """Fixes for ocean variables."""

    def fix_metadata(self, cubes):
        """Fix ocean depth coordinate.

        Parameters
        ----------
        cubes: iris CubeList
            List of cubes to fix

        Returns
        -------
        iris.cube.CubeList

        """
        for cube in cubes:
            if cube.coords('latitude'):
                cube.coord('latitude').var_name = 'lat'
            if cube.coords('longitude'):
                cube.coord('longitude').var_name = 'lon'

            if cube.coords(axis='Z'):
                z_coord = cube.coord(axis='Z')
                if z_coord.var_name == 'olevel':
                    fix_ocean_depth_coord(cube)
        return cubes

