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
                       'disk_radius',
                       'disk_regularization_radius',
                       'disk_ref_r_cylindrical',
                       'disk_shear_normalization',
                       'disk_turbulent_diffusivity',
                       'disk_alpha_effect']
    PARAMETER_UNITS = {'disk_height': u.kpc,
                       'disk_radius': u.kpc,
                       'disk_regularization_radius': u.kpc,
                       'disk_ref_r_cylindrical': u.kpc,
                       'disk_shear_normalization': 1/u.s,
                       'disk_turbulent_diffusivity': u.cm*u.cm/u.s,
                       'disk_alpha_effect': u.km/u.s}

    def __init__(self, grid, *, parameters=dict(), ensemble_size=None,
                 ensemble_seeds=None, dependencies={}, keep_galmag_field=False,
                 number_of_modes=None,
                 disk_shear_function=disk_prof.Clemens_Milky_Way_shear_rate, # S(R)
                 disk_rotation_function=disk_prof.Clemens_Milky_Way_rotation_curve, # V(R)
                 disk_height_function=disk_prof.exponential_scale_height, # h(R)
                 disk_field_decay=True, disk_newman_boundary_condition_envelope=False,
                 ):

        if number_of_modes is None:
            number_of_modes = max([int(k[5:]) for k in parameters if 'mode_' in k])

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
        # Constructs GalMag's native disk_modes_normalization parameters
        disk_mode_norm = []
        for i in range(self._number_of_modes):
            name = 'mode_{0:d}'.format(i+1)
            if name in self.parameters:
                disk_mode_norm.append((self.parameters[name] << u.microgauss).value)
            else:
                disk_mode_norm.append(0)
        # Provisionally includes disk modes parameter
        self.parameters['disk_modes_normalization'] = np.array(disk_mode_norm)

        # Shorthands (for clarity)
        h = self.parameters['disk_height']
        S = self.parameters['disk_shear_normalization']
        alpha = self.parameters['disk_alpha_effect']
        beta = self.parameters['disk_turbulent_diffusivity']

        # Computes Ralpha
        Ralpha = ( h*alpha/beta ).to_value(u.dimensionless_unscaled)
        self.parameters['disk_turbulent_induction'] = Ralpha
        # Computes local dynamo number
        Romega = ( h**2*S/beta ).to_value(u.dimensionless_unscaled)
        self.parameters['disk_dynamo_number'] = Ralpha*Romega

        # Constructs field using superclass
        field = super().compute_field(seed)

        # Removes temporary parameters
        del self.parameters['disk_modes_normalization']
        del self.parameters['disk_dynamo_number']
        del self.parameters['disk_turbulent_induction']

        return field


class GalMagHaloField(GalMagMagneticFieldBase):
    """
    An IMAGINE field constructed using GalMag's halo magnetic field
    """
    NAME = 'galmag_halo_magnetic_field'

    PARAMETER_NAMES = ['halo_radius',
                       'halo_ref_radius',
                       'halo_ref_z',
                       'halo_ref_Bphi',
                       'halo_rotation_characteristic_radius',
                       'halo_rotation_characteristic_height',
                       'halo_rotation_normalization',
                       'halo_turbulent_diffusivity',
                       'halo_alpha_effect']

    PARAMETER_UNITS = {'halo_radius': u.kpc,
                       'halo_ref_radius': u.kpc,
                       'halo_ref_z': u.kpc,
                       'halo_ref_Bphi': u.microgauss,
                       'halo_rotation_characteristic_radius': u.kpc,
                       'halo_rotation_characteristic_height': u.kpc,
                       'halo_rotation_normalization': u.km/u.s,
                       'halo_turbulent_diffusivity': u.cm*u.cm/u.s,
                       'halo_alpha_effect': u.km/u.s}


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

    def compute_field(self, seed):
        # Shorthands (for clarity)
        r = self.parameters['halo_radius']
        V = self.parameters['halo_rotation_normalization']
        beta = self.parameters['halo_turbulent_diffusivity']
        alpha = self.parameters['halo_alpha_effect']

        # Computes Ralpha
        Ralpha = ( r*alpha/beta ).to_value(u.dimensionless_unscaled)
        self.parameters['halo_turbulent_induction'] = Ralpha
        # Computes Romega
        Romega = ( -r*V/beta  ).to_value(u.dimensionless_unscaled)
        self.parameters['halo_rotation_induction'] = Romega

        # Constructs field using superclass
        field = super().compute_field(seed)

        # Removes temporary parameters
        del self.parameters['halo_rotation_induction']
        del self.parameters['halo_turbulent_induction']

        return field
