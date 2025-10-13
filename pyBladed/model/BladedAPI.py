"""
This file contains methods to setup and run Bladed .prj files
"""
import clr  # part of the pythonnet package
import os
import tempfile
import numpy as np

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
        todo: this method takes a lot of time, is it really necessary or can it be accelerated?

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
                       prefix='bladed_api_run', mp_lock=None):
        """
        Executes a simulation with the Bladed model.

        Parameters
        ----------
        result_directory: str
            Path of directory the results are written to
        prefix: str
            Prefix for output files
        """
        if mp_lock is not None:
            mp_lock.acquire()

        self.add_to_batch(result_directory, prefix)

        if mp_lock is not None:
            mp_lock.release()

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


    def get_polars(self):
        """ Polar informations can be found in self.prj.LegacyModel.AerofoilSections """

        polars = self.prj.LegacyModel.AerofoilSections
        cleaned_up_polars = []
        for polar_ID in range(polars.Count):
            polar_info = dict()
            polar_info['name'] = polars[polar_ID].sName
            polar_info['alpha'] = [polars[polar_ID].fAlpha[ii] for ii in range(polars[polar_ID].fAlpha.Count)]
            polar_info['cl'] = [polars[polar_ID].fCl[ii] for ii in range(polars[polar_ID].fCl.Count)]
            polar_info['cd'] = [polars[polar_ID].fCd[ii] for ii in range(polars[polar_ID].fCd.Count)]
            polar_info['cm'] = [polars[polar_ID].fCm[ii] for ii in range(polars[polar_ID].fCm.Count)]
            cleaned_up_polars.append(polar_info)
        return cleaned_up_polars

    def get_blade(self):
        blade = self.prj.LegacyModel.BladeMB.BladeStations
        blade_data = {'DistanceAlongBlade': [],
                      'DistanceAlongPitchAxis': [],
                      'Chord': [],
                      'TwistRadians': [],
                      'massPerUnitLength': [],
                      'IntertiaPerUnitLength': [],
                      'RadiiOfGyrationRatio': [],
                      'MassAxisOrientationRadians': [],
                      'bendingStiffnessXp': [],
                      'bendingStiffnessYp': [],
                      'PrincipalAxisOrientationRadians': [],
                      'torsionalStiffness': [],
                      'AxialStiffness': [],
                      'shearStiffnessXp': [],
                      'shearStiffnessYp': [],
                      'NeutralAxis.X': [],
                      'NeutralAxis.Y': [],
                      'CentreOfMass.X': [],
                      'CentreOfMass.Y': [],
                      'ShearCentre.X': [],
                      'ShearCentre.Y': []}

        for sect in range(blade.Count):
            for param in ['DistanceAlongBlade', 'DistanceAlongPitchAxis']:
                blade_data[param].append(getattr(blade[sect], param))

            for param in ['Chord', 'TwistRadians', 'massPerUnitLength', 'IntertiaPerUnitLength', 'RadiiOfGyrationRatio',
                          'MassAxisOrientationRadians', 'bendingStiffnessXp', 'bendingStiffnessYp',
                          'PrincipalAxisOrientationRadians', 'torsionalStiffness', 'AxialStiffness',
                          'shearStiffnessXp', 'shearStiffnessYp']:

                if getattr(blade[sect].InboardProperties, param) != getattr(blade[sect].OutboardProperties, param):
                    print(
                        'Inboard and outboard value of the same parameter is not the same. I am not prepared for this...')

                blade_data[param].append(getattr(blade[sect].InboardProperties, param))

            for param in ['CentreOfMass.X', 'CentreOfMass.Y', 'ShearCentre.X', 'ShearCentre.Y']:

                value_inboard = getattr(getattr(blade[sect].InboardProperties, param[:-2]), param[-1])
                value_outboard = getattr(getattr(blade[sect].OutboardProperties, param[:-2]), param[-1])
                if value_inboard != value_outboard:
                    print(
                        'Inboard and outboard value of the same parameter is not the same. I am not prepared for this...')

                blade_data[param].append(value_inboard)

            for param in ['NeutralAxis.X', 'NeutralAxis.Y']:
                blade_data[param].append(getattr(getattr(blade[sect], param[:-2]), param[-1]))

        for param, value_list in blade_data.items():
            blade_data[param] = np.array(value_list)

        return blade_data

    def get_nacelle_mass(self):
        return self.prj.LegacyModel.NMASS.fMass

    def get_nacelle_cog_vertical(self):
        return self.prj.LegacyModel.NMASS.fMassY

    def get_nacelle_cog_horizontal(self):
        return self.prj.LegacyModel.NMASS.fMassZ

    def get_nacelle_yaw_inertia(self):
        return self.prj.LegacyModel.NMASS.fInertia

    def get_nacelle_nodding_inertia(self):
        return self.prj.LegacyModel.NMASS.fINOD

    def get_nacelle_rolling_inertia(self):
        return self.prj.LegacyModel.NMASS.fIROLL

    def get_cone_angle(self):
        return self.prj.LegacyModel.RCON.fCone

    def get_LSS_stiffness(self):
        return self.prj.LegacyModel.DTRAIN.fLowSpeedStiffness.GetElement([4])

    def get_LSS_damping(self):
        return self.prj.LegacyModel.DTRAIN.fLowSpeedDamping.GetElement([4])

    def get_blade_damping(self, mode_ID_python_numbering=0):
        Bladed.ProjectApi.Settings.SuppressReadonlyInvisibleException = True
        return self.prj.Turbine.Blades.FlexibilityModel.WholeBladeModes[mode_ID_python_numbering].Damping

    def get_tower_E_mod(self, material_ID=0):
        # not a good idea -> you can change the material property, but it will not be automatically applied, i.e.
        # the bending stiffness and other tower properties will remain unchanged -> You have to press the button
        # 'apply' in the GUI
        # Same problem exists when changing thickness
        raise NotImplementedError
        # return self.prj.LegacyModel.TMASS.fTowYoungsMod[material_ID]

    def get_tower_bending_stiffness(self):
        bending_stiffnesses = []
        for sect in range(self.prj.LegacyModel.fStiffness.Count):
            bending_stiffnesses.append(self.prj.LegacyModel.fStiffness[sect])
        return np.array(bending_stiffnesses)

    def get_tower_torsional_stiffness(self):
        torsional_stiffnesses = []
        for sect in range(self.prj.LegacyModel.fTowerTorsionalStiffness.Count):
            torsional_stiffnesses.append(self.prj.LegacyModel.fTowerTorsionalStiffness[sect])
        return np.array(torsional_stiffnesses)

    def get_tower_shear_stiffness(self):
        shear_stiffnesses = []
        for sect in range(self.prj.LegacyModel.fShearStiffness.Count):
            shear_stiffnesses.append(self.prj.LegacyModel.fShearStiffness[sect])
        return np.array(shear_stiffnesses)

    def get_tower_mass(self):
        tower_masses = []
        for sect in range(self.prj.LegacyModel.fTowerMass.Count):
            tower_masses.append(self.prj.LegacyModel.fTowerMass[sect])
        return np.array(tower_masses)

    def get_tower_damping(self, mode_ID_python_numbering=0):
        # Does not seem to be necessary -> Bladed.ProjectApi.Settings.SuppressReadonlyInvisibleException = True
        return self.prj.Turbine.SupportStructure.FlexibilityModel.Modes[mode_ID_python_numbering].Damping

    def get_DS_separation_time_constant(self):
        return self.prj.Aerodynamics.SeparationTimeConstant

    def get_DS_pressure_lag_time_constant(self):
        return self.prj.Aerodynamics.PressureLagTimeConstant

    def get_DS_vortex_lift_time_constant(self):
        return self.prj.Aerodynamics.VortexLiftTimeConstant

    def modify_blade(self, blade_data):
        """ allow backward compatibility -> renamed from modify_ to set_ """
        self.set_blade(blade_data)

    def set_blade(self, blade_data):
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
                        Chord
                        TwistRadians
                        NeutralAxis.X
                        NeutralAxis.Y
        """
        blade = self.prj.LegacyModel.BladeMB.BladeStations  # just to make code cleaner
        for param in blade_data:
            if param in ['CentreOfMass.X', 'CentreOfMass.Y', 'ShearCentre.X', 'ShearCentre.Y']:
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

            elif param in ['NeutralAxis.X', 'NeutralAxis.Y']:
                for sect, param_value in enumerate(blade_data[param]):
                    cpoint = getattr(blade[sect], param[:-2])
                    setattr(cpoint, param[-1], param_value)
                    setattr(blade[sect], param[:-2], cpoint)

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
                                duration_wind_file=None, frequency_along_x=None, mean_wind_speed=None,
                                turbulence_seed=None):
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

    def set_simulation_parameter(self, simulation_parameter_data):
        """
        To be implemented: modify arbitrary simulation parameter

        Parameters
        ----------
        simulation_parameter_data: TBD
        """
        raise NotImplementedError

    def set_nacelle_mass(self, new_nacelle_mass):
        self.prj.LegacyModel.NMASS.fMass = new_nacelle_mass

    def set_nacelle_cog_vertical(self, new_nacelle_cog_vertical):
        self.prj.LegacyModel.NMASS.fMassY = new_nacelle_cog_vertical

    def set_nacelle_cog_horizontal(self, new_nacelle_cog_horizontal):
        self.prj.LegacyModel.NMASS.fMassZ = new_nacelle_cog_horizontal

    def set_nacelle_yaw_inertia(self, new_nacelle_yaw_inertia):
        self.prj.LegacyModel.NMASS.fInertia = new_nacelle_yaw_inertia

    def set_nacelle_nodding_inertia(self, new_nacelle_nodding_inertia):
        self.prj.LegacyModel.NMASS.fINOD = new_nacelle_nodding_inertia

    def set_nacelle_rolling_inertia(self, new_nacelle_rolling_inertia):
        self.prj.LegacyModel.NMASS.fIROLL = new_nacelle_rolling_inertia

    def set_cone_angle(self, new_cone_angle):
        """
        Parameters
        ----------
        new_cone_angle: float
            New cone angle in degrees
        """
        self.prj.LegacyModel.RCON.fCone = new_cone_angle

    def set_LSS_stiffness(self, new_LSS_stiffness):
        self.prj.LegacyModel.DTRAIN.fLowSpeedStiffness.SetElement([4], new_LSS_stiffness)

    def set_LSS_damping(self, new_LSS_damping):
        self.prj.LegacyModel.DTRAIN.fLowSpeedDamping.SetElement([4], new_LSS_damping)

    def set_blade_damping(self, new_blade_damping, mode_ID_python_numbering=0):
        Bladed.ProjectApi.Settings.SuppressReadonlyInvisibleException = True
        self.prj.Turbine.Blades.FlexibilityModel.WholeBladeModes[mode_ID_python_numbering].Damping = new_blade_damping

    def set_tower_E_mod(self, new_tower_E_mod, material_ID=0):
        # not a good idea -> you can change the material property, but it will not be automatically applied, i.e.
        # the bending stiffness and other tower properties will remain unchanged -> You have to press the button
        # 'apply' in the GUI
        # Same problem exists when changing thickness
        raise NotImplementedError
        # self.prj.LegacyModel.TMASS.fTowYoungsMod[material_ID] = new_tower_E_mod

    def set_tower_bending_stiffness(self, new_bending_stiffness):
        """
        Note: This will not be visible in the .$PJ file..., but it will apply, in contrast to the thickness our
        material properties, which will be visibly changed in the .$PJ file, but will not effectively apply or change
        the tower stiffnesses.
        """
        for sect in range(self.prj.LegacyModel.fStiffness.Count):
            self.prj.LegacyModel.fStiffness[sect] = new_bending_stiffness[sect]

    def set_tower_torsional_stiffness(self, new_torsional_stiffness):
        """
        Note: This will not be visible in the .$PJ file..., but it will apply, in contrast to the thickness our
        material properties, which will be visibly changed in the .$PJ file, but will not effectively apply or change
        the tower stiffnesses.
        """
        for sect in range(self.prj.LegacyModel.fTowerTorsionalStiffness.Count):
            self.prj.LegacyModel.fTowerTorsionalStiffness[sect] = new_torsional_stiffness[sect]

    def set_tower_shear_stiffness(self, new_shear_stiffness):
        """
        Note: This will not be visible in the .$PJ file..., but it will apply, in contrast to the thickness our
        material properties, which will be visibly changed in the .$PJ file, but will not effectively apply or change
        the tower stiffnesses.
        """
        for sect in range(self.prj.LegacyModel.fShearStiffness.Count):
            self.prj.LegacyModel.fShearStiffness[sect] = new_shear_stiffness[sect]

    def set_tower_mass(self, new_tower_mass):
        """
        Note: This will not be visible in the .$PJ file..., but it will apply, in contrast to the thickness our
        material properties, which will be visibly changed in the .$PJ file, but will not effectively apply or change
        the tower stiffnesses.
        """
        for sect in range(self.prj.LegacyModel.fTowerMass.Count):
            self.prj.LegacyModel.fTowerMass[sect] = new_tower_mass[sect]

    def set_tower_damping(self, new_tower_damping, mode_ID_python_numbering=0):
        # Bladed.ProjectApi.Settings.SuppressReadonlyInvisibleException = True
        self.prj.Turbine.SupportStructure.FlexibilityModel.Modes[mode_ID_python_numbering].Damping = new_tower_damping

    def set_DS_separation_time_constant(self, new_separation_time_constant):
        self.prj.Aerodynamics.SeparationTimeConstant = new_separation_time_constant

    def set_DS_pressure_lag_time_constant(self, new_pressure_lag_time_constant):
        self.prj.Aerodynamics.PressureLagTimeConstant = new_pressure_lag_time_constant

    def set_DS_vortex_lift_time_constant(self, new_vortex_lift_time_constant):
        self.prj.Aerodynamics.VortexLiftTimeConstant = new_vortex_lift_time_constant

    def set_polar_cl(self, sectionID, cl_new):
        if self.prj.LegacyModel.AerofoilSections[sectionID].fAlpha.Count != len(cl_new):
            raise ValueError('Number of new cl values does not match with length of available alpha array')
        else:
            for i in range(self.prj.LegacyModel.AerofoilSections[sectionID].fAlpha.Count):
                self.prj.LegacyModel.AerofoilSections[sectionID].fCl[i] = cl_new[i]

    def set_polar_cd(self, sectionID, cd_new):
        if self.prj.LegacyModel.AerofoilSections[sectionID].fAlpha.Count != len(cd_new):
            raise ValueError('Number of new cl values does not match with length of available alpha array')
        else:
            for i in range(self.prj.LegacyModel.AerofoilSections[sectionID].fAlpha.Count):
                self.prj.LegacyModel.AerofoilSections[sectionID].fCd[i] = cd_new[i]

    def save(self, filename):
        """
        To be implemented: save model (.prj file) without hanging it in the queue

        Parameters
        ----------
        filename: str
        """
        raise NotImplementedError
