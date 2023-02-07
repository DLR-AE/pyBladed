"""
This file contains methods to setup and run Bladed .prj files
"""
import clr  # part of the pythonnet package
import os
import tempfile

# load library
clr.AddReference('GH.Bladed.Api.Facades')  # This loads the dll which provides the Bladed API into Python
from GH.Bladed.Api.Facades.EntryPoint import Bladed  # This imports the entry point to the Bladed API into this script
from GH.Bladed.DataModel import Facades  # This provides the enum "look up codes" for things like "TurbulentWind"


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
        self.add_to_batch(result_directory, prefix)
        self.run_batch()

    def add_to_batch(self, result_directory=os.path.join(tempfile.gettempdir(), r'model', r'Results'),
                       prefix='bladed_api_run'):
        """
        Adds the current project calculation to the batch

        Parameters
        ----------
        result_directory: str
            Path of directory the results are written to
        prefix: str
            Prefix for output files
        """
        Bladed.ProjectApi.QueueJob(self.prj, result_directory, prefix)
        Bladed.ProjectApi.AddQueuedJobsToBatch()

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

    def set_calculation_type(self, calculation_type='power_production'):
        """
        Sets the calculation type of the provided prj.

        Parameters
        ----------
        calculation_type: str, default='power_production'
            string identifier for the desired calculation type.
        """
        # Changing the calculation type to "Wind Turbulence"
        if calculation_type == 'modal_analysis':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.ModalAnalysis
        elif calculation_type == 'wind_turbulence':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.WindTurbulence
        elif calculation_type == 'earthquake_generation':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.EarthquakeGeneration
        elif calculation_type == 'sea_state':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.SeaState
        elif calculation_type == 'aerodynamic_information':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.AerodynamicInformation
        elif calculation_type == 'performance_coefficients':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.PerformanceCoefficients
        elif calculation_type == 'steady_power_curve':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.SteadyPowerCurve
        elif calculation_type == 'steady_operational_loads':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.SteadyOperationalLoads
        elif calculation_type == 'steady_parked_loads':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.SteadyParkedLoads
        elif calculation_type == 'model_linearisation':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.ModelLinearisation
        elif calculation_type == 'electrical_performance':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.ElectricalPerformance
        elif calculation_type == 'power_production_loading':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.PowerProduction
        elif calculation_type == 'normal_stop':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.NormalStop
        elif calculation_type == 'emergency_stop':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.EmergencyStop
        elif calculation_type == 'start':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.Start
        elif calculation_type == 'idling':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.Idling
        elif calculation_type == 'parked':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.Parked
        elif calculation_type == 'hardware_test':
            self.prj.Simulation.SimulationType = Facades.SimulationTypeEnumFacade.HardwareTest
        else:
            raise NotImplementedError('Requested simulation type can not be set (from this function). '
                                      'Check self.prj.Simulation.SimulationType for all calculation options')

    def set_turbulence_settings(self, num_points_y=None, num_points_z=None, volume_width_y=None, volume_width_z=None,
                           duration_wind_file=None, frequency_along_x=None, mean_wind_speed=None, turbulence_seed=None):
        """
        Modifies the basic turbulence box settings.
        The spectrum type and settings or other advanced options are not changed.

        Parameters
        ----------
        num_points_y: int, default=None
            Number of points in the rotor plane in horizontal direction
        num_points_z: int, default=None
            Number of points in the rotor plane in vertical direction
        volume_width_y: float, default=None
            Width of the rotor plane in horizontal direction
        volume_width_z: float, default=None
            Width of the rotor plane in vertical direction
        duration_wind_file: float, default=None
            Duration of the wind file in seconds
        frequency_along_x: float, default=None
            Sampling frequency of the wind time series
        mean_wind_speed: float, default=None
            The mean wind speed for the wind file [m/s].
        turbulence_seed: int, default=None
            The random number seed for the wind file generation
        """
        # Note: This usage example assumes that the provided prj already has a valid Wind Turbulence definition
        # using the desired Spectrum Type

        # Modify the turbulent wind definition as necessary
        if num_points_y is not None:
            self.prj.PreProcessing.TurbulenceGeneration.NumPointsY = num_points_y
        if num_points_z is not None:
            self.prj.PreProcessing.TurbulenceGeneration.NumPointsZ = num_points_z
        if volume_width_y is not None:
            self.prj.PreProcessing.TurbulenceGeneration.VolumeWidthY = volume_width_y
        if volume_width_z is not None:
            self.prj.PreProcessing.TurbulenceGeneration.VolumeWidthZ = volume_width_z
        if duration_wind_file is not None:
            self.prj.PreProcessing.TurbulenceGeneration.Duration = duration_wind_file
        if frequency_along_x is not None:
            self.prj.PreProcessing.TurbulenceGeneration.FrequencyAlongX = frequency_along_x
        if mean_wind_speed is not None:
            self.prj.PreProcessing.TurbulenceGeneration.MeanSpeed = mean_wind_speed
        if turbulence_seed is not None:
            self.prj.PreProcessing.TurbulenceGeneration.TurbulenceSeed = turbulence_seed

    def set_turbulent_wind(self, turbulent_wind_filepath=None, mean_wind_speed=None, ti_u=None, ti_v=None, ti_w=None,
                           direction=None, inclination=None, refer_to_hub=None):
        """
        Sets the wind model of the prj to turbulent wind, and populates some of the required fields.

        Parameters
        ----------
        turbulent_wind_filepath: str
            The full file path to a .wnd file.
        mean_wind_speed: float
            A mean wind speed that is compatible with the wind file.
        ti_u: float
            The longitudinal turbulence intensity [%].
        ti_v: float
            The latitudinal turbulence intensity [%].
        ti_w: float
            The vertical turbulence intensity [%].
        direction: float
            The horizontal angle between the approaching wind and the rotor disk
            normal, in radians (optional, with default 0.0).
        inclination: float
            The vertical angle between the approaching wind and the rotor disk
            normal, in radians (optional, with default 0.0).
        refer_to_hub: bool
            Refer the turbulence characteristics to hub height.
        """

        # Changing the wind model to "turbulent wind"
        self.prj.Environment.Wind.TimeVaryingWind.ModelType = Facades.WindModelEnumFacade.TurbulentWind

        # Setting all of the turbulent wind parameters
        if turbulent_wind_filepath is not None:
            assert os.path.exists(turbulent_wind_filepath), "Wind file {} does not exist".format(
                turbulent_wind_filepath)
            self.prj.Environment.Wind.TimeVaryingWind.TurbulentWind.WindFile = turbulent_wind_filepath
        if mean_wind_speed is not None:
            self.prj.Environment.Wind.TimeVaryingWind.TurbulentWind.MeanSpeed = mean_wind_speed
        if ti_u is not None:
            self.prj.Environment.Wind.TimeVaryingWind.TurbulentWind.TI_U = ti_u
        if ti_v is not None:
            self.prj.Environment.Wind.TimeVaryingWind.TurbulentWind.TI_V = ti_v
        if ti_w is not None:
            self.prj.Environment.Wind.TimeVaryingWind.TurbulentWind.TI_W = ti_w
        if direction is not None:
            self.prj.Environment.Wind.TimeVaryingWind.TurbulentWind.Direction = direction
        if inclination is not None:
            self.prj.Environment.Wind.TimeVaryingWind.TurbulentWind.Inclination = inclination
        if refer_to_hub is not None:
            self.prj.Environment.Wind.TimeVaryingWind.TurbulentWind.ReferToHub = refer_to_hub

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
