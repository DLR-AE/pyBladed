"""
This file contains Bladed result reading tools.

The binary results are represented by two files: a header file and the actual data.
"""
import os
import re
import numpy as np
import glob

from pyBladed.results import bladed_definitions


class SkipLine(NotImplementedError):
    """
    Exception to indicate a line skip
    """
    pass


class BladedResult:
    """
    Interface for Bladed binary data.
    """

    def __init__(self, result_dir, result_prefix, unload=False):
        """
        Parameters
        ----------
        result_dir: str
            Path of Bladed result files
        result_prefix: str
            Result file prefix
        unload: boolean
            flag, if set the binary data is de-referenced after each read (to save memory)
        """
        self.result_dir = result_dir
        self.result_prefix = result_prefix
        self.unload = unload

        # standard: all known keywords
        self.supported_keywords = bladed_definitions.supported_keywords
        self.header_file_names = None
        self.results = None

    def scan(self):
        """
        Reads the header files (%*) and creates a list of known variables. Results are not read here.

        The header file name is used as top-level key in the result dictionary.
        """
        # find the matching header files
        path_pattern = os.path.join(self.result_dir, self.result_prefix + '.%*')
        self.header_file_names = glob.glob(path_pattern)
        if not self.header_file_names:
            raise FileNotFoundError('No header files found, check path')
        self.results = dict()
        for header_file_name in self.header_file_names:
            with open(header_file_name) as file_object:
                self.results[header_file_name] = self._read_header(file_object, self.supported_keywords)
            self.results[header_file_name]['data'] = None

    @staticmethod
    def _read_header(file_object, supported_keywords):
        """
        Reads Bladed header file content into a dict.

        Parameters
        ----------
        file_object: File
            File object to read from
        supported_keywords: dict
            definition of supported keywords, a map of keywords and the requested type transformations

        Returns
        ----------
        result: dict
            The processed header file (filtered and transformed key/value pairs)
        """
        lines = file_object.readlines()
        lines = [line.replace('\n', '') for line in lines]

        result = dict()
        for line in lines:
            try:
                key, value = BladedResult._parse_header_line(line, supported_keywords)
                result[key] = value
            except SkipLine:
                # expected if line does not split into two parts
                pass
            except KeyError:
                # expected if line does not start with one of the known keywords
                pass

        return result

    @staticmethod
    def _parse_header_line(line, supported_keywords):
        """
        Parses a header file line according to its type.

        Parameters
        ----------
        line: str
            Single line of a Bladed header file
        supported_keywords: dict
            Definition of supported keywords (as defined in bladed_definitions.py)

        Returns
        ----------
        key and value as tuple
        """
        # this will fail if
        split_str = line.split(maxsplit=1)
        if len(split_str) == 1:
            raise SkipLine

        keyword = split_str[0]
        rest = split_str[1]

        # select method to extract
        # will raise a KeyError exception (desired) and thus the line is skipped
        method = supported_keywords[keyword]
        if method == 'string':
            value = rest
        elif method == 'string-remove':
            value = rest.replace("'", "")
        elif method == 'string-list':
            value = rest.split(' ')
        elif method == 'string-list-remove':
            # match the names enclosed by ''
            value = re.findall(r"'([\w\s\-()/.]+)'", rest)
        elif method == 'int':
            value = int(rest)
        elif method == 'int-list':
            value = [int(elem) for elem in rest.split()]
        elif method == 'float-list':
            value = [float(elem) for elem in rest.split()]
        elif method == 'float':
            value = float(rest)
        elif method == 'numpy-dtype':
            if rest == 'R*4':
                value = '<f4'
            elif rest == 'R*8':
                value = '<f8'
            elif rest == 'I*4':
                value = '<i4'
            else:
                raise ValueError('Unknown type in Bladed header: ' + rest)
        else:
            raise NotImplementedError('Unknown conversion type: "' + method + '"')

        return keyword, value

    def _find_dataset(self, dataset_name):
        """
        Finds the name of the header file, the set belongs to, and generates a slice
        object for accessing the corresponding data.

        Parameters
        ----------
        dataset_name: str
            Name of the dataset, as appearing in Bladed result.

        Returns
        ----------
        tuple (header name, slice)
            Name of the header file (which is the top-level dict key)
        """
        for key in self.results:
            if 'VARIAB' not in self.results[key]:
                continue
            if dataset_name in self.results[key]['VARIAB']:
                if self.results[key]['NDIMENS'] == 2:
                    i = self.results[key]['VARIAB'].index(dataset_name)
                    dataset_slice = slice(None), slice(i, i+1)
                elif self.results[key]['NDIMENS'] == 3:
                    i = self.results[key]['VARIAB'].index(dataset_name)
                    dataset_slice = slice(None), slice(None), slice(i, i+1)
                else:
                    raise NotImplementedError('Current implementation supports 2D or 3D data only')
                return key, dataset_slice
        raise KeyError('Dataset name not found in any of the known headers')

    def _load_dataset(self, header_file_name):
        """
        Reads the binary data associated with one header file.

        Parameters
        ----------
        header_file_name: str
            Name of the header file, for which data is loaded.
        """
        binary_file_path = os.path.join(self.result_dir, self.results[header_file_name]['FILE'])
        shape = [x for x in reversed(self.results[header_file_name]['DIMENS'])]
        with open(binary_file_path, 'rb') as file_object:
            file_content = file_object.read()
            self.results[header_file_name]['data'] = \
                np.frombuffer(file_content, dtype=self.results[header_file_name]['FORMAT']).reshape(shape)

    def _read_bladed_ascii_file(self, fname):
        """
        Read Bladed ascii result file

        Parameters
        ----------
        fname: str
            Path to Bladed ascii output file

        Returns
        ----------
        success: boolean
            Flag if reading ascii file was successful
        lines: list
            Content of the ascii file, or None
        """
        # check if file exists
        if not os.path.isfile(fname):
            print('{} file could not be found'.format(fname))
            return False, None

        # try to read ascii file
        try:
            with open(fname, 'r') as f:
                lines = f.readlines()
                lines = [line.replace('\n', '') for line in lines]
            return True, lines
        except OSError:
            print('Something went wrong while parsing {} file'.format(fname))
            return False, None

    def _load_campbell_data_CM(self):
        """
        Reads the ascii data with detailed Campell diagram data, if this file is available. This file contains all
        data used for the Campbell diagram representation. If only the frequency and damping progression are of
        interest, they can be obtained more elegantly from the binaries (coupled modes).

        The .$CM has two parts. Part 1 contains a list of each individual point of the campbell diagram with
        operating point, frequency, damping, participation factors. Part 2 contains the information on the mode tracking
        with number of points, operating points, frequencies, (user-defined) mode track name

        Returns
        ----------
        campbell_data_list: list
            List with all Campbell data (freq, damp, part. factors) for each mode track
        coupled_mode_names: list
            List with the names of the mode tracks
        """
        # read the .$CM file
        campbell_data_file = os.path.join(self.result_dir, self.result_prefix+'.$CM')
        success, lines = self._read_bladed_ascii_file(campbell_data_file)
        if not success:
            return None, None

        # read the top part (omega, freq, damping, participation factors for all points in the Campbell diagram)
        omega = list()
        freq = list()
        damp = list()
        particip_str = list()
        start_idx, numpoints = [[lines.index(s), int(s.split()[-1])] for s in lines if 'NUMPTS' in s][0]
        for npoint in range(numpoints):
            omega.append(float(lines[start_idx + npoint * 4 + 1].split()[-1]))
            freq.append(float(lines[start_idx + npoint * 4 + 2].split()[-1]))
            damp.append(float(lines[start_idx + npoint * 4 + 3].split()[-1]))
            particip_str.append(lines[start_idx + npoint * 4 + 4].split("'")[1])

        # read the bottom part -> to get the (possibly user-defined) mode track name
        coupled_mode_names = []
        start_idx, numlines = [[lines.index(s), int(s.split()[-1])] for s in lines if 'NUMLINES' in s][0]
        campbell_data_list = []
        node_ID = 0
        for nline in range(numlines):
            mode_data = dict()
            mode_name = lines[start_idx + nline * 5 + 4].split('DEFLEGEND')[-1].strip()
            coupled_mode_names.append(mode_name)
            mode_data['mode_name'] = mode_name
            mode_data['freq_tracked'] = [float(val) for val in lines[start_idx + nline * 5 + 3].split()[-1].split(',')[:-1]]

            npoints = int(lines[start_idx + nline * 5 + 1].split()[-1])
            mode_data['node_IDs'] = list(np.arange(node_ID, node_ID + npoints))
            mode_data['omegas'] = omega[node_ID : node_ID + npoints]
            mode_data['freq'] = freq[node_ID : node_ID + npoints]
            mode_data['damp'] = damp[node_ID : node_ID + npoints]
            mode_data['particip_str'] = particip_str[node_ID : node_ID + npoints]

            node_ID = node_ID + npoints
            campbell_data_list.append(mode_data)

        for mode in campbell_data_list:
            if mode['freq'] != mode['freq_tracked']:
                print('Individual frequency values (top part .$CM file) do not match with mode tracked frequency '
                      'values (bottom part .$CM file)')

        return campbell_data_list, coupled_mode_names

    def _load_campbell_data_shape(self):
        """
        Reads the .$shape ascii file which contains modal participations for each (mode tracked) mode at each
         operating point.

        Returns
        ----------
        shape_file_data: dict
            Dictionary with detailed participation information for each operating point and each mode track
        """
        campbell_data_file = os.path.join(self.result_dir, self.result_prefix + '.$shape')

        success, lines = self._read_bladed_ascii_file(campbell_data_file)
        if not success:
            return None

        anchor_op = 'operating point'
        anchor_mode = '------ '

        shape_file_data = dict()
        op = None
        mode = None
        for line in lines:
            if anchor_op in line:
                op = line.split(anchor_op)[0]
                shape_file_data[op] = dict()
            elif anchor_mode in line:
                mode = ' '.join(line.split()[1:-1])
                shape_file_data[op][mode] = dict()
                shape_file_data[op][mode]['particip_mode_names'] = list()
                shape_file_data[op][mode]['particip_amplitude'] = list()
                shape_file_data[op][mode]['particip_phase'] = list()
            else:
                # three possibilities:
                #   1) empty line
                #   2) line full with ------
                #   3) line with data (particip_mode   amplitude   phase)
                if len(line) == 0 or line[0] == '-':
                    continue
                else:
                    dat = line.split()
                    shape_file_data[op][mode]['particip_mode_names'].append(' '.join(dat[:-2]))
                    shape_file_data[op][mode]['particip_amplitude'].append(float(dat[-2]))
                    shape_file_data[op][mode]['particip_phase'].append(float(dat[-1][:-1]))

        return shape_file_data

    def __getitem__(self, item):
        """
        Access to data for one item (e.g. time data). Reads the data from the binary file, if not
        yet present.

        Parameters
        ----------
        item: str
            Name of the dataset to access (as showing up in Bladed and the header file)
        Returns
        ----------
        array-like
            The corresponding data from the binary result file.
        """

        # Campbell diagram data is not saved in the same format as all other data, so has to be handled individually
        if item == 'Campbell diagram':
            return self._load_campbell_data_CM()
        else:
            # find the corresponding header file
            header_file_name, dataset_slice = self._find_dataset(item)

            # load data from binary result file if not present
            if self.results[header_file_name]['data'] is None:
                self._load_dataset(header_file_name)

            # make slice according to dimensions
            data = np.copy(self.results[header_file_name]['data'][dataset_slice])

            # limit memory consumption by removing the reference to the binary data
            if self.unload is True:
                self.results[header_file_name]['data'] = None

            if self.results[header_file_name]['NDIMENS'] == 3:
                return data, self.results[header_file_name]
            else:
                return data
