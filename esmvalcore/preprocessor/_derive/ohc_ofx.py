"""Derivation of variable `ohc_ofx`."""
import iris
from iris import Constraint

from dask import array as da
from cf_units import Unit
import  numpy as np
from ._baseclass import DerivedVariableBase

RHO_CP = iris.coords.AuxCoord(4.09169e+6, units=Unit('kg m-3 J kg-1 K-1'))


class DerivedVariable(DerivedVariableBase):
    """Derivation of variable `ohc_ohx`."""

    @staticmethod
    def required(project):
        """Declare the variables needed for derivation."""
        required = [
            {
                'short_name': 'thetao'
            },
            {
                'short_name': 'volcello',
                'mip': 'fx'
            },
        ]
        if project == 'CMIP6':
            required = [
                {
                    'short_name': 'thetao'
                },
                {
                    'short_name': 'volcello',
                    'mip': 'Ofx',
                },

            ]
        return required

    @staticmethod
    def calculate(cubes):
        """
        Compute ocean heat content.

        Use c_p*rho_0= 4.09169e+6 J m-3 K-1
        (Kuhlbrodt et al., 2015, Clim. Dyn.)

        Arguments
        ---------
        cube: iris.cube.Cube
           input cube.

        Returns
        -------
        iris.cube.Cube
              Output OHC cube.
        """
        # 1. Load the thetao and volcello cubes
        cube = cubes.extract_strict(
            Constraint(cube_func=lambda c: c.var_name == 'thetao'))
        volume = cubes.extract_strict(
            Constraint(cube_func=lambda c: c.var_name == 'volcello'))
        # 2. multiply with each other and with cprho0
        # some juggling with coordinates needed since Iris is very
        # restrictive in this regard
        try:
            t_coord_dims = cube.coord_dims('time')
        except iris.exceptions.CoordinateNotFoundError:
            time_coord_present = False
        else:
            time_coord_present = True
            t_coord_dim = t_coord_dims[0]
            dim_coords = [(coord, cube.coord_dims(coord)[0])
                          for coord in cube.coords(
                              contains_dimension=t_coord_dim, dim_coords=True)]
            aux_coords = [
                (coord, cube.coord_dims(coord))
                for coord in cube.coords(contains_dimension=t_coord_dim,
                                         dim_coords=False)
            ]
            for coord, dims in dim_coords + aux_coords:
                cube.remove_coord(coord)
        if cube.data.shape == volume.data.shape:
            cube.data = cube.data * volume.data
        elif cube.ndim == 4 and volume.ndim == 3:
            print('tiling', [cube.data.shape[0], 1, 1, 1])
            volume = np.tile(volume.data, [cube.data.shape[0], 1, 1, 1])
            cube.data = cube.data * volume.data
        else:
            print(cube.data.shape , 'does not match', volume.data.shape)
            assert 0
       
        const = 4.09169e+6 
        cube.data = cube.data * const # RHO_CP
        if time_coord_present:
            for coord, dim in dim_coords:
                cube.add_dim_coord(coord, dim)
            for coord, dims in aux_coords:
                cube.add_aux_coord(coord, dims)
        return cube
