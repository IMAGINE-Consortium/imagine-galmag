from imagine import MagneticField
import astropy.units as u
import numpy as np
from galmag.B_generators import B_generator_disk
from galmag.B_generators import B_generator_halo
import galmag.disk_profiles as disk_prof
import galmag.halo_profiles as halo_prof

__all__ = ['GalMagDiskField', 'GalMagHaloField']



class GalMagMagneticFieldBase(MagneticField):
    """
    Base class for GalMag fields
    """
    def __init__(self, grid=None, parameters=dict(), ensemble_size=None,
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
        
        super().__init__(grid, parameters, ensemble_size, ensemble_seeds, dependencies)
    
    def compute_field(self, seed):
        
        if self.galmag is not None:
            galmag_B = self.galmag
        else:
            parameters = self.parameters.copy()
            parameters.update(self._field_options)
            galmag_B = self.galmag_gen.get_B_field(**parameters)
        
        B_array = np.empty(self.data_shape)
        # and saves the pre-computed components
        B_array[:,:,:,0] = galmag_B.x
        B_array[:,:,:,1] = galmag_B.y
        B_array[:,:,:,2] = galmag_B.z
        
        if self.keep_galmag_field:
            self.galmag = galmag_B

        return B_array << u.microgauss

    
    
class GalMagDiskField(GalMagMagneticFieldBase):
    """
    An IMAGINE field constructed using GalMag's disk magnetic field
    """
    field_name = 'galmag_disk_magnetic_field'

    stochastic_field = False 

    def __init__(self, grid=None, parameters=dict(), ensemble_size=None,
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
    def field_checklist(self):
        checklist = {'disk_modes_normalization': True,
                     'disk_height': True,
                     'disk_radius': True,
                     'disk_turbulent_induction': True,
                     'disk_dynamo_number': True,
                     'disk_regularization_radius': True,
                     'disk_ref_r_cylindrical': True}
        
        # Includes individual parameters for each disk mode
        checklist.update( {'mode_{0:d}'.format(i):True 
                          for i in range(self._number_of_modes)} )
        return checklist

    
        
class GalMagHaloField(GalMagMagneticFieldBase):
    """
    An IMAGINE field constructed using GalMag's halo magnetic field
    """
    field_name = 'galmag_halo_magnetic_field'

    stochastic_field = False 

    def __init__(self, grid=None, parameters=dict(), ensemble_size=None,
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
         
    @property
    def field_checklist(self):
        return {'halo_turbulent_induction': True,
                'halo_rotation_induction': True,
                'halo_radius': True,
                'halo_ref_radius': True,
                'halo_ref_z': True,
                'halo_ref_Bphi': True,
                'halo_rotation_characteristic_radius': True,
                'halo_rotation_characteristic_height': True}
    