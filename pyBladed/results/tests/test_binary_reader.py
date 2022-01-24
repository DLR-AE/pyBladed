"""
All tests for the binary reading
"""

import numpy as np
import os
import json
# python3 only:
import io
import pytest

# specimen
from pyBladed.results.binary import BladedResult, SkipLine
from pyBladed.results import bladed_definitions

# test specific
import pyBladed.results.tests.resources as resources


# -- static methods first --

def test_parse_header_line_formatting():
    """
    Tests _parse_header_line(line)

    Purpose: test different whitespaces that might occur in the input
    :return: None
    """
    # spaces
    k, v = BladedResult._parse_header_line('RECL	4', bladed_definitions.supported_keywords)
    assert k == 'RECL'
    assert v == 4
    # spaces + newline
    k, v = BladedResult._parse_header_line('RECL	4\n', bladed_definitions.supported_keywords)
    assert k == 'RECL'
    assert v == 4
    # tab
    k, v = BladedResult._parse_header_line('RECL\t4', bladed_definitions.supported_keywords)
    assert k == 'RECL'
    assert v == 4
    # tab + spaces
    k, v = BladedResult._parse_header_line('RECL\t  4', bladed_definitions.supported_keywords)
    assert k == 'RECL'
    assert v == 4


def test_parse_header_line_failures():
    """
    Tests _parse_header_line(line)

    Purpose: test invalid inputs
    :return: None
    """

    # invalid line with only one component
    with pytest.raises(SkipLine):
        _, _ = BladedResult._parse_header_line('ABC', bladed_definitions.supported_keywords)

    # invalid line with unknown keyword
    with pytest.raises(KeyError):
        _, _ = BladedResult._parse_header_line('A B', bladed_definitions.supported_keywords)

    # invalid value format
    with pytest.raises(ValueError):
        _, _ = BladedResult._parse_header_line('FORMAT X', bladed_definitions.supported_keywords)


def test_parse_header_line_types():
    """
    Tests _parse_header_line(line)

    Purpose: test the data type interpretations (as specified in "supported_keywords")
    :return: None
    """
    # collect all types to check if the tests are complete
    all_types = set(bladed_definitions.supported_keywords.values())
    # int
    k, v = BladedResult._parse_header_line('RECL	4', bladed_definitions.supported_keywords)
    assert k == 'RECL'
    assert v == 4
    all_types.remove('int')
    # list of ints
    k, v = BladedResult._parse_header_line('DIMENS	1 2', bladed_definitions.supported_keywords)
    assert k == 'DIMENS'
    assert v[0] == 1
    assert v[1] == 2
    all_types.remove('int-list')
    # string
    k, v = BladedResult._parse_header_line('FILE	powprod_12ms.$06', bladed_definitions.supported_keywords)
    assert k == 'FILE'
    assert v == 'powprod_12ms.$06'
    all_types.remove('string')
    # string - remove '
    k, v = BladedResult._parse_header_line("CONTENT	'POWPROD'", bladed_definitions.supported_keywords)
    assert k == 'CONTENT'
    assert v == 'POWPROD'
    all_types.remove('string-remove')
    # list of strings
    k, v = BladedResult._parse_header_line('VARUNIT	FL P P', bladed_definitions.supported_keywords)
    assert k == 'VARUNIT'
    assert v == ['FL', 'P', 'P']
    all_types.remove('string-list')
    # list of strings - remove '
    k, v = BladedResult._parse_header_line(
        "VARIAB	'Generator torque' 'Electrical power' 'Generator power loss'",
        bladed_definitions.supported_keywords)
    assert k == 'VARIAB'
    assert v == ['Generator torque', 'Electrical power', 'Generator power loss']
    all_types.remove('string-list-remove')
    # float
    k, v = BladedResult._parse_header_line('MIN 	0.0000000E+000', bladed_definitions.supported_keywords)
    assert k == 'MIN'
    assert v - 0.0 < 1e-5
    all_types.remove('float')
    # list of floats
    k, v = BladedResult._parse_header_line('AXIVAL 	0.0000000E+000 1.0000E+000', bladed_definitions.supported_keywords)
    assert k == 'AXIVAL'
    assert v[0] - 0.0 < 1e-5
    assert v[1] - 1.0 < 1e-5
    all_types.remove('float-list')
    # number formats
    # 4 byte real
    k, v = BladedResult._parse_header_line('FORMAT	R*4', bladed_definitions.supported_keywords)
    assert k == 'FORMAT'
    a = np.array([1.], dtype=v)
    assert a.dtype == np.dtype('float32')
    # 8 byte real
    k, v = BladedResult._parse_header_line('FORMAT	R*8', bladed_definitions.supported_keywords)
    assert k == 'FORMAT'
    a = np.array([1.], dtype=v)
    assert a.dtype == np.dtype('float64')
    # 4 byte integer
    k, v = BladedResult._parse_header_line('FORMAT	I*4', bladed_definitions.supported_keywords)
    assert k == 'FORMAT'
    a = np.array([1.], dtype=v)
    assert a.dtype == np.dtype('int32')
    all_types.remove('numpy-dtype')
    # check
    assert len(all_types) == 0


def test_parse_header_line_type_failure():
    """
    Tests _parse_header_line

    Purpose: ensure that all exceptions are raised
    :return: None
    """
    # malformed integer
    with pytest.raises(ValueError):
        _, _ = BladedResult._parse_header_line('FORMAT	I*3', bladed_definitions.supported_keywords)
    # use non-standard dict of keywords to provoke missing implementation error
    with pytest.raises(NotImplementedError):
        _, _ = BladedResult._parse_header_line('FORMAT	I*3', {'FORMAT': 'NON_EXISTING_METHOD'})


def test_read_header():
    """
    Test the reading of the header file without actually reading from disk. Only keys are checked here, values are
    addressed in test_bladed_result_scan()

    :return: None
    """
    header = io.StringIO(resources.header_file_content)
    header_dict = BladedResult._read_header(header, bladed_definitions.supported_keywords)
    # check presence of keys
    for keyword in bladed_definitions.mandatory_keywords:
        assert keyword in header_dict


# non-static functionality
def test_bladed_result_constructor():
    bladed_result = BladedResult('test_dir', 'prefix')
    assert bladed_result.result_dir == 'test_dir'
    assert bladed_result.result_prefix == 'prefix'
    assert bladed_result.header_file_names is None
    assert bladed_result.results is None


@pytest.fixture
def bladed_result():
    """
    Sets up an instance for the tests
    :return: the BladedResult instance
    """
    bladed_result = BladedResult(os.path.join('pyBladed', 'results', 'example_data', '2D'), 'powprod_12ms')
    return bladed_result


# test with real data and file IO
def test_bladed_result_scan(bladed_result):
    """
    Test for BladedResult.scan()

    Purpose: Checks if the header is found and parsed correctly (including file IO)

    :param bladed_result: BladedResult object from test fixture
    :return: None
    """
    bladed_result.scan()
    key_name = os.path.join('pyBladed', 'results', 'example_data', '2D', 'powprod_12ms.%06')
    # the expected header is stored in a separate file
    with open(os.path.join('pyBladed', 'results', 'example_data', '2D', 'expected_header.json')) as json_file:
        expected_header = json.load(json_file)
    assert key_name in bladed_result.results
    header = bladed_result.results[key_name]
    assert header['data'] is None

    for key, value in expected_header.items():
        # we don't know the data type, for now equality works for all items
        cmp = value == header[key]
        assert cmp
