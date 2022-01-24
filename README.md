# pyBladed

## Purpose
This is the DLR-AE (Institute of Aeroelasticity, German 
Aerospace Center) Python wrapper for Bladed. It 
supports manipulation of Bladed models to support the
automated setup of models (mainly through) the 
Bladed API as well as routines to access (binary)
Bladed results. It is not meant to be a comprehensive tool
that covers the full API functionality. Only required features
have been wrapped so far.

## Requirements

#### General

* OS: Windows (for Bladed) 
* Python >=3.7
* Bladed installed (we used v4.9)
* a Bladed license (e.g. the license dongle plugged in)
* the location of the Bladed API DLL is in your PYTHONPATH

#### Required Python packages
* numpy >= 1.12
* pytest >= 5.0 (for unit tests)

## Installing
* to use: `pip install --user https+git://github.com/DLR-AE/pyBladed.git`
* to develop
  * clone repository
  * `pip install -e <local_repo_path>`

## Examples

The repository contains example data to demonstrate the functionalities 
of the result reader (clone it). They are also used to run unit tests.

Accessing data in Bladed results becomes pretty simple:

```
    from pyBladed.result.binary import BladedResult
    
    bladed_result = BladedResult(os.path.join('example_data', '2D'), 'powprod_12ms')
    bladed_result.scan()
    torque = bladed_result['Generator torque']
    power = bladed_result['Electrical power']
```

## Running unit tests

Unit tests are currently only available for the result reader 
part. Simply run `py.test` in the root directory of the repository.

## Contributors

Thanks go to Hendrik Verdonck (hendrik.verdonck@dlr.de) for his contributions.
