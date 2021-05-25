"""Fixes for cesm2-waccm-fv2."""
from iris.cube import CubeList

from ..fix import Fix
from ..shared import fix_ocean_depth_coord

import numpy as np
import cf_units

class AllVars(Fix):
    """Fixes for thetao."""

    def fix_metadata(self, cubes):
        """
        Fix cell_area coordinate.

        Parameters
        ----------
        cubes: iris CubeList
            List of cubes to fix

        Returns
        -------
        iris.cube.CubeList

        """
        cube = self.get_cube_from_list(cubes)
        if cube.coords('latitude'):
            cube.coord('latitude').var_name = 'lat'
        if cube.coords('longitude'):
            cube.coord('longitude').var_name = 'lon'
        return CubeList([cube])


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
            if cube.coords(axis='Z'):
                 z_coord = cube.coord(axis='Z')
                 if str(z.coords.units) == 'cm' and np.max(z.points)>10000.:
                     z_coord.units = cf_units.Unit('m')

#                if z_coord.var_name == 'olevel':
                fix_ocean_depth_coord(cube)
        return cubes
