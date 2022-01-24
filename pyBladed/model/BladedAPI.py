"""
This file contains methods to setup and run Bladed .prj files
"""
import clr  # part of the pythonnet package
import os
import tempfile

# load library
clr.AddReference('GH.Bladed.Api.Facades')  # This loads the dll which provides the Bladed API into Python
from GH.Bladed.Api.Facades.EntryPoint import Bladed  # This imports the entry point to the Bladed API into this script


class BladedModel:
    """
    Python wrapper around Bladed prj file. Uses BladedAPI.
    """

    def __init__(self, project_file_path, has_batch=False):
        """

        Parameters
        ----------
        project_file_path: str
            Path to Bladed .prj file
        has_batch: Boolean
            Flag to indicate whether batch process has to be initialized
        """
        self.suppress_logs()
        self.prj = self.get_project(project_file_path)
        if not has_batch:
            self.setup_batch()

    @staticmethod
    def suppress_logs():
        """
        Disable console logging.
        """
        Bladed.LoggingSettings.LogToConsole = False
        Bladed.LoggingSettings.DisableDebugLogs()
        Bladed.LoggingSettings.SuppressBladedM72Logs = True

    @staticmethod
    def get_project(project_file_path):
        """
        Creates a new project instance in the Bladed API.

        Parameters
        ----------
        project_file_path: str
            Path of an existing Bladed project file.
        Returns
        -------
        BladedProject instance
        """
        prj_template = Bladed.ProjectApi.GetProject(project_file_path)
        prj = prj_template.Clone()
        return prj

    @staticmethod
    def setup_batch(batch_directory=os.path.join(tempfile.gettempdir(), r'model', r'Batch')):
        """
        Start batch framework, set the working directory and job list.

        Parameters
        ----------
        batch_directory: str
            Path of the directory to be used in the batch run, defaults to a local temp folder.
        """
        Bladed.BatchApi.StartFramework()
        Bladed.BatchApi.SetDirectory(batch_directory)
        Bladed.BatchApi.SetJobList('default')

    @staticmethod
    def run_batch():
        """
        Starts a batch computation.
        """
        Bladed.BatchApi.RunBlocking()
        if Bladed.BatchApi.HasCompleted():
            print('Batch runs have completed successfully.')
        else:
            print('Batch runs have not completed successfully.')

    def run_simulation(self, result_directory=os.path.join(tempfile.gettempdir(), r'model', r'Results'),
                       prefix='bladed_api_run'):
        """
        Executes a simulation with the Bladed model.

        Parameters
        ----------
        result_directory: str
            Path of directory the results are written to
        prefix: str
            Prefix for output files
        """
        Bladed.ProjectApi.QueueJob(self.prj, result_directory, prefix)
        Bladed.ProjectApi.AddQueuedJobsToBatch()
        self.run_batch()

    def modify_blade(self, blade_data):
        """
        Modifies structural blade data in a Bladed model.

        Parameters
        ----------
        blade_data: dict
            Dictionary with bladed structural blade description,
            Values: 1D array with value for each blade section
                    Optional keys:
                        CentreOfMass.X
                        CentreOfMass.Y
                        massPerUnitLength
                        IntertiaPerUnitLength
                        RadiiOfGyrationRatio
                        MassAxisOrientationRadians
                        bendingStiffnessXp
                        bendingStiffnessYp
                        PrincipalAxisOrientationRadians
                        torsionalStiffness
                        AxialStiffness
                        ShearCentre.X
                        ShearCentre.Y
                        shearStiffnessXp
                        shearStiffnessYp
        """
        blade = self.prj.LegacyModel.BladeMB.BladeStations  # just to make code cleaner
        for param in blade_data:
            if '.' in param:
                # special cases: CentreOfMass.X, CentreOfMass.Y, ShearCentre.X, ShearCentre.Y
                for sect, param_value in enumerate(blade_data[param]):
                    # INBOARD
                    cpoint = getattr(blade[sect].InboardProperties, param[:-2])
                    setattr(cpoint, param[-1], param_value)
                    setattr(blade[sect].InboardProperties, param[:-2], cpoint)
                    # OUTBOARD
                    cpoint = getattr(blade[sect].OutboardProperties, param[:-2])
                    setattr(cpoint, param[-1], param_value)
                    setattr(blade[sect].OutboardProperties, param[:-2], cpoint)
            else:
                for sect, param_value in enumerate(blade_data[param]):
                    # INBOARD
                    setattr(blade[sect].InboardProperties, param, param_value)
                    # OUTBOARD
                    setattr(blade[sect].OutboardProperties, param, param_value)

    def modify_wind(self, wind_data):
        """
        To be implemented: modify wind field

        Parameters
        ----------
        wind_data: TBD
        """
        raise NotImplementedError

    def modify_simulation_parameter(self, simulation_parameter_data):
        """
        To be implemented: modify arbitrary simulation parameter

        Parameters
        ----------
        simulation_parameter_data: TBD
        """
        raise NotImplementedError

    def save(self, filename):
        """
        To be implemented: save model (.prj file) without hanging it in the queue

        Parameters
        ----------
        filename: str
        """
        raise NotImplementedError
