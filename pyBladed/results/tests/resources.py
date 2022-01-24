"""
If possible, the tests use static objects and not files.
"""

header_file_content = \
    "FILE	powprod_12ms.$06\n" + \
    "ACCESS	D\n" + \
    "FORM	F\n" + \
    "RECL	4\n" + \
    "FORMAT	R*4\n" + \
    "CONTENT	'POWPROD'\n" + \
    "CONFIG	'STATIONARY'\n" + \
    "NDIMENS	2\n" + \
    "DIMENS	3	20001\n" + \
    "GENLAB	'Generator variables'\n" + \
    "VARIAB	'Generator torque' 'Electrical power' 'Generator power loss'\n" + \
    "VARUNIT	FL P P\n" + \
    "AXISLAB	'Time'\n" + \
    "AXIUNIT	T\n" + \
    "AXIMETH	2\n" + \
    "MIN 	0.0000000E+000\n" + \
    "STEP	9.9999998E-003\n" + \
    "NVARS	0\n" + \
    "ULOADS   7.1592855E+006   7.5046815E+006   0.0000000E+000\n" + \
    "   7.0032420E+006   7.3428640E+006   0.0000000E+000\n" + \
    "   7.1592855E+006   7.5046815E+006   0.0000000E+000\n" + \
    "   7.0032420E+006   7.3428640E+006   0.0000000E+000\n" + \
    "   7.1592855E+006   7.5046815E+006   0.0000000E+000\n" + \
    "   7.1592855E+006   7.5046815E+006   0.0000000E+000\n" + \
    "MAXTIME   0.0000000E+000   0.0000000E+000   0.0000000E+000\n" + \
    "MINTIME   9.9999998E-003   9.9999998E-003   0.0000000E+000\n" + \
    "MEAN   7.0889532E+006   7.4307285E+006   0.0000000E+000\n"

header_expected_result = {
    'FILE': 'powprod_12ms.$06',
    'ACCESS': 'D',
    'FORM': 'F',
    'RECL': 4,
    'FORMAT': '',
    'CONTENT': 'POWPROD',
    'CONFIG': 'STATIONARY',
    'NDIMENS': 2,
    'DIMENS': [3, 20001],
    'GENLAB': 'Generator variables',
    'VARIAB': ['Generator torque', 'Electrical power', 'Generator power loss'],
    'VARUNIT': ['FL', 'P', 'P'],
    'AXISLAB': 'Time',
    'AXIUNIT': 'T',
    'AXIMETH:': 2,
    'MIN': 0.0000000E+000,
    'STEP': 9.9999998E-003,
    'NVARS': 0
}
