# %% IMPORTS

# Package imports
import astropy.units as u
import numpy as np

# GalMag imports
from galmag.B_generators import B_generator_disk
from galmag.B_generators import B_generator_halo
import galmag.disk_profiles as disk_prof
import galmag.halo_profiles as halo_prof


# IMAGINE imports
import imagine
from imagine.fields import MagneticField
from imagine.tools import req_attr

__all__ = ['GalMagDiskField', 'GalMagHaloField']

class GalMagMagneticFieldBase(MagneticField):
    """
    Base class for GalMag fields
    """
    def __init__(self, grid, *, parameters=dict(), ensemble_size=None,
                 ensemble_seeds=None, dependencies={}, keep_galmag_field=False):

        self.keep_galmag_field = keep_galmag_field
        # GalMag uses standard units
        box_dimensionless = grid.box.to_value(u.kpc)

        # Prepares a GalMag field generator with grid details
        self.galmag_gen = self.galmag_generator_class(box=box_dimensionless,
                                                      resolution=grid.resolution,
                                                      grid_type=grid.grid_type)
        # Caches galmag object
        self.galmag = None
        # Any functions (e.g. profiles) and switches (e.g. 'disk_field_decay')
        # are stored (by subclasses) in the following attribute
        self._field_options = {}

        super().__init__(grid=grid, parameters=parameters, ensemble_size=ensemble_size,
                         ensemble_seeds=ensemble_seeds, dependencies=dependencies)

    @property
    @req_attr
    def parameter_units(self):
        """
        Units used by GalMag for the parameters
        """
        return self.PARAMETER_UNITS

    def compute_field(self, seed):

        if self.galmag is not None:
            galmag_B = self.galmag
        else:
            parameters = {}
            for pname, pval in self.parameters.items():
                if pname in self.parameter_units:
                    # Converts to default parameter units
                    # (if unit is absent, assumes default)
                    pval = (pval << self.parameter_units[pname]).value
                parameters[pname] = pval

            # Includes GalMag "switch-like" parameters
            parameters.update(self._field_options)
            # Creates the field using GalMag's generator
            galmag_B = self.galmag_gen.get_B_field(**parameters)

            if self.keep_galmag_field:
                self.galmag = galmag_B

        B_array = np.empty(self.data_shape)
        # and saves the pre-computed components
        B_array[:,:,:,0] = galmag_B.x
        B_array[:,:,:,1] = galmag_B.y
        B_array[:,:,:,2] = galmag_B.z

        return B_array << u.microgauss


class GalMagDiskField(GalMagMagneticFieldBase):
    """
    An IMAGINE field constructed using GalMag's disk magnetic field
    """
    NAME = 'galmag_disk_magnetic_field'
    # The following is updated dynamically with the normalization of
    # different eigenmodes
    PARAMETER_NAMES = ['disk_height',
                       'disk_radius', 'disk_turbulent_induction',
                       'disk_dynamo_number', 'disk_regularization_radius',
                       'disk_ref_r_cylindrical']
    PARAMETER_UNITS = {'disk_height': u.kpc,
                       'disk_radius': u.kpc,
                       'disk_turbulent_induction': u.dimensionless_unscaled,
                       'disk_dynamo_number': u.dimensionless_unscaled,
                       'disk_regularization_radius': u.kpc,
                       'disk_ref_r_cylindrical': u.kpc}

    def __init__(self, grid, *, parameters=dict(), ensemble_size=None,
                 ensemble_seeds=None, dependencies={}, keep_galmag_field=False,
                 number_of_modes=4,
                 disk_shear_function=disk_prof.Clemens_Milky_Way_shear_rate, # S(R)
                 disk_rotation_function=disk_prof.Clemens_Milky_Way_rotation_curve, # V(R)
                 disk_height_function=disk_prof.exponential_scale_height, # h(R)
                 disk_field_decay=True, disk_newman_boundary_condition_envelope=False,
                 ):

        self._number_of_modes = number_of_modes
        self.galmag_generator_class = B_generator_disk

        super().__init__(grid=grid, parameters=parameters,
                         ensemble_size=ensemble_size,
                         ensemble_seeds=ensemble_seeds,
                         dependencies=dependencies,
                         keep_galmag_field=keep_galmag_field)

        self._field_options = {'disk_shear_function': disk_shear_function,
                               'disk_rotation_function': disk_rotation_function,
                               'disk_height_function': disk_height_function,
                               'disk_field_decay': disk_field_decay,
                               'disk_newman_boundary_condition_envelope':
                               disk_newman_boundary_condition_envelope}
    @property
    def parameter_names(self):
        # Includes individual parameters for each disk mode
        modes_list = ['mode_{0:d}'.format(i+1)
                      for i in range(self._number_of_modes)]
        return self.PARAMETER_NAMES + modes_list

    @property
    def parameter_units(self):
        # Includes individual parameters for each disk mode
        param_units_actual = {'mode_{0:d}'.format(i+1): u.microgauss
                              for i in range(self._number_of_modes)}
        param_units_actual.update(self.PARAMETER_UNITS)
        return param_units_actual

    def compute_field(self, seed):
        disk_mode_norm = []
        for i in range(self._number_of_modes):
            name = 'mode_{0:d}'.format(i+1)
            if name in self.parameters:
                disk_mode_norm.append((self.parameters[name] << u.microgauss).value)
            else:
                disk_mode_norm.append(0)
        # Provisionally includes disk modes parameter
        self.parameters['disk_modes_normalization'] = np.array(disk_mode_norm)
        field = super().compute_field(seed)
        # Restores actual parameters
        del self.parameters['disk_modes_normalization']
        return field


class GalMagHaloField(GalMagMagneticFieldBase):
    """
    An IMAGINE field constructed using GalMag's halo magnetic field
    """
    NAME = 'galmag_halo_magnetic_field'

    PARAMETER_NAMES = ['halo_turbulent_induction',
                       'halo_rotation_induction',
                       'halo_radius',
                       'halo_ref_radius',
                       'halo_ref_z',
                       'halo_ref_Bphi',
                       'halo_rotation_characteristic_radius',
                       'halo_rotation_characteristic_height']

    PARAMETER_UNITS = {'halo_turbulent_induction': u.dimensionless_unscaled,
                       'halo_rotation_induction': u.dimensionless_unscaled,
                       'halo_radius': u.kpc,
                       'halo_ref_radius': u.kpc,
                       'halo_ref_z': u.kpc,
                       'halo_ref_Bphi': u.kpc,
                       'halo_rotation_characteristic_radius': u.kpc,
                       'halo_rotation_characteristic_height': u.kpc}


    def __init__(self, grid, *, parameters=dict(), ensemble_size=None,
                 ensemble_seeds=None, dependencies={}, keep_galmag_field=False,
                 halo_symmetric_field=True,
                 halo_rotation_function=halo_prof.simple_V,
                 halo_alpha_function=halo_prof.simple_alpha,
                 halo_n_free_decay_modes=4,
                 halo_dynamo_type='alpha2-omega',
                 halo_compute_only_one_quadrant=True,
                 halo_growing_mode_only=False,
                 halo_Galerkin_ngrid=501):

        self.galmag_generator_class = B_generator_halo
        super().__init__(grid=grid, parameters=parameters,
                         ensemble_size=ensemble_size,
                         ensemble_seeds=ensemble_seeds,
                         dependencies=dependencies,
                         keep_galmag_field=keep_galmag_field)

        self._field_options = {'halo_n_free_decay_modes': halo_n_free_decay_modes,
                               'halo_growing_mode_only': halo_growing_mode_only,
                               'halo_compute_only_one_quadrant': halo_compute_only_one_quadrant,
                               'halo_Galerkin_ngrid': halo_Galerkin_ngrid,
                               'halo_symmetric_field': halo_symmetric_field,
                               'halo_dynamo_type': halo_dynamo_type,
                               'halo_rotation_function': halo_rotation_function,
                               'halo_alpha_function': halo_alpha_function}

