"""
Loading a large number of large result files causes a MEMORY_ERROR, if all data is kept in memory. De-referencing it is
of cause slower.
"""

import os
import pytest
# from memory_profiler import profile

# specimen
from pyBladed.results.binary import BladedResult


# @profile
def load_large(num_loads, unload):
    """
    Use this function in the tests
    """

    bladed_results = list()

    for i in range(num_loads):
        bladed_results.append(
            BladedResult(os.path.join('pyBladed', 'results', 'example_data', 'large'), 'stab_analysis_run',
                         unload=unload))

    for bladed_result in bladed_results:
        bladed_result.scan()

    extract = [bladed_result['Blade 1 x-deflection (perpendicular to rotor plane)'] for bladed_result in
               bladed_results]


def test_load_large_fail():
    """
    Will result in a memory error because all data read from the result file stays in memory
    """
    with pytest.raises(MemoryError):
        load_large(num_loads=1000, unload=False)


def test_load_large_success():
    """
    Will pass because only the extracted variables stay in memory
    """
    load_large(num_loads=1000, unload=True)


