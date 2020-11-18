# IMAGINE and GalMag integration

This package allows one to use magnetic fields produced by [GalMag](https://github.com/luizfelippesr/galmag) within the [IMAGINE pipeline](https://github.com/IMAGINE-Consortium/imagine/).

## Installation

1. Install [GalMag](https://github.com/luizfelippesr/galmag#installation) and [IMAGINE](https://imagine-code.readthedocs.io/en/latest/installation.html).
2. Clone this repository or download the desired [release](https://github.com/IMAGINE-Consortium/imagine-galmag/releases)
3. Install it as a regular python package, running:

```console
cd PATH_TO_IMAGINE-GALMAG
pip install -e .
```
## Usage

### Basic Field usage
Each GalMag field component (halo/disk) is imported as a separate IMAGINE field. 

```python
from galmag_imagine import GalMagHaloField, GalMagDiskField 
```

This can be instantiated in the usual way, by providing a grid and a parameters dictionary. 

```python
halo_field = GalMagHaloField(grid=grid, 
                             parameters={'halo_radius': 15*u.kpc,
                                         'halo_ref_Bphi': 1*u.microgauss,
                                         'halo_rotation_characteristic_radius': 3*u.kpc,
                                         'halo_rotation_characteristic_height': 10*u.kpc,
                                         'halo_rotation_normalization': 220*u.km/u.s,
                                         'halo_turbulent_diffusivity': 5e27*u.cm*u.cm/u.s,
                                         'halo_alpha_effect': 1*u.km/u.s}, 
                             halo_symmetric_field=False, 
                             keep_galmag_field=True)
disk_field = GalMagDiskField(grid=grid, 
                             parameters={'mode_1': 4*u.microgauss,
                                         'mode_2': 2*u.microgauss, 
                                         'mode_4': .3*u.microgauss,
                                         'disk_height': 400*u.pc,
                                         'disk_radius': 17*u.kpc,
                                         'disk_alpha_effect': 1*u.km/u.s,
                                         'disk_shear_normalization': -35.36*u.km/u.s/u.kpc,
                                         'disk_turbulent_diffusivity': 5e25*u.cm*u.cm/u.s}, 
                             keep_galmag_field=True)  
```

These fields can then be provided to an IMAGINE `Simulator`.


### Accessing the original GalMag field

If the optional keyword argument `keep_galmag_field` is set to `True`, the GalMag field 
component object is saved to the attribute `galmag` after the field is evaluated. 
Below we exemplify how to use the GalMag associated object to get the &phi; component of 
the magnetic field.

```python
# Evaluates the field
disk_field.get_data()
# Gets the Bphi component
Bphi = disk_field.galmag.phi
```

### Parameters


#### Changes in parametrization

There are some key differences between the way the models are parametrised 
in the native GalMag contex and in IMAGINE-GalMag Field object.

In the original GalMag parametrization, the amplitude of the modes for the disk field
were specified using an array, while here (as it can be seen in the above example),
each mode is treated as a separate parameter, where the name of the n-th mode
is simply `mode_n`. 

Aiming easier interpretation and cleaner prior specifications, the dimensionless
dynamo parameters `disk_dynamo_number`, `disk_turbulent_induction`,
`halo_rotation_induction` and `halo_turbulent_induction` were replaced by
directly observable dimensional counterparts, namely:
 * `halo_alpha_effect`, the normalization of the alpha profile for the halo at the reference position (by default, the Sun's position).
 * `halo_turbulent_diffusivity` - turbulent magnetic diffusivity in the halo (assumed constant)
 * `halo_rotation_normalization` - normalization of the halo circular velocity profile at infinity
 * `disk_alpha_effect` -  normalization of the disk alpha effect at the solar radius
 * `disk_shear_normalization` - the shearing rate of the disk at the solar radius
 * `disk_turbulent_diffusivity` - turbulent magnetic diffusivity in the disk (assumed constant)


Note that all dimensional parameters are specified with explicit units, to avoid 
any unit convertion mistakes.


#### Parameters which became keyword arguments
 
Some of GalMag parameters are *not* treated as IMAGINE parameters, as they are 
understood as part of the model settings, and thus are not meant to varied during
an exploration of the parameter space. 

Particularly important cases of this are the GalMag parameters which set
the functional form of the rotation curve,
disk scale-height or alpha-effect profile. In the example below we create
a disk field based on a smooth exponential rotation curve
(instead of the default case, which is based on the fit obtained by
[Clemens 1985](http://adsabs.harvard.edu/abs/1985ApJ...295..422C)):

```python
from galmag.disk_profiles import simple_rotation_curve, simple_shear_rate

disk_field = GalMagDiskField(grid=grid, 
                             parameters={'mode_1': 4*u.microgauss,
                                         'mode_2': 2*u.microgauss, 
                                         'mode_4': .3*u.microgauss,
                                         'disk_height': 400*u.pc,
                                         'disk_radius': 17*u.kpc,
                                         'disk_alpha_effect': 1*u.km/u.s,
                                         'disk_shear_normalization': -35.36*u.km/u.s/u.kpc,
                                         'disk_turbulent_diffusivity': 5e25*u.cm*u.cm/u.s}, 
                             disk_rotation_function=simple_rotation_curve,
                             disk_shear_function=simple_shear_rate,
                             keep_galmag_field=True)  
```
