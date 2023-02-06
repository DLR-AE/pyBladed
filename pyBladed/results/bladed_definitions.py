"""
Bladed header file keywords and how they are processed (type transformation).
"""

mandatory_keywords = {
    'FILE': 'string',
    'ACCESS': 'string',
    'FORM': 'string',
    'RECL': 'int',
    'FORMAT': 'numpy-dtype',
    'CONTENT': 'string-remove',
    'CONFIG': 'string-remove',
    'NDIMENS': 'int',
    'DIMENS': 'int-list',
    'GENLAB': 'string-remove',
    'VARIAB': 'string-list-remove',
    'VARUNIT': 'string-list',
}

optional_keywords = {
    'AXIVAL': 'float-list',
    'AXISLAB': 'string-remove',
    'AXIUNIT': 'string',
    'AXIMETH': 'int',
    'AXITICK': 'string-list-remove',
    'MIN': 'float',
    'STEP': 'float',
    'NVARS': 'int',
    'HEADREC': 'int',
    'VAROFFSET': 'float',
    'VARSCALE': 'float-list'
}

# join
supported_keywords = {**mandatory_keywords,  **optional_keywords}
