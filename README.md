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
They will fall back to default parameters if any parameter is missing.

```python
halo_field = GalMagHaloField(grid=grid, 
                             parameters={'disk_turbulent_induction': 0.386392513})
disk_field = GalMagDiskField(grid=grid, parameters={}, 
                             keep_galmag_field=True)
```

These fields can than be provided to an IMAGINE `Simulator`.


### Accessing the original GalMag field

If the optional keyword argument `keep_galmag_field` is set to `True`, the GalMag field 
component object is saved to the attribute `galmag` after the field is evaluated. 
Below we exemplify how to use the GalMag associated object to get the Phi component of 
the magnetic field.

```python
# Evaluates the field
disk_field.get_data()
# Gets the Bphi component
Bphi = disk_field.galmag.phi
```

### Parameters

Some of GalMag parameters are *not* treated as IMAGINE parameters, as they are 
understood as part of the model settings, and are not meant to varied during 
an exploration of the parameter space. For example, `number_of_modes` is a 
regular parameter in GalMag, and here is a keyword argument, which changes the 
behaviour of the `Field` object. Another important change is the array-valued 
`'disk_modes_normalization'` which is in the IMAGINE context is substituted by
parameter which is broken into several 'mode_1', 'mode_2', etc, parameters. 
The example below illustrated these changes:

```python
disk_field = GalMagDiskField(grid=grid, 
                             parameters={'mode_1':1, 'mode_2':0, 'mode_3':4
                                         'disk_dynamo_number'= -20},
                             number_of_modes=3, 
                             disk_height_function=personalised_scaleheight_function)
```
