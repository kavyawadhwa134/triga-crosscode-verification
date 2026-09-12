# pcM MOOSE solid heat conduction, master app driving OpenMC through Cardinal.
#
# Units: cm, W, K (mesh is in cm, so conductivities are W/cm-K).
#
# Thermal properties are NOT in the approved specification and are pcM
# assumptions, documented in spec/thermal.md:
#   T1  k_fuel = 0.18 W/cm-K   (U-ZrH1.65, ~18 W/m-K)
#   T2  k_clad = 0.16 W/cm-K   (SS304, ~16 W/m-K)
#   T3  h      = 0.109778 W/cm^2-K, Dittus-Boelter at Re=4755, Pr=7.01
#   T4  coolant bulk rise 3.57 K over the channel, from an energy balance
#       at the specified 0.2 m/s and 250 kW/120 pins
# T3 and T4 are placeholders for the NekRS solution.

T_inlet = 293.0
dT_coolant = 3.57
height = 60.0

[Mesh]
  [file]
    type = FileMeshGenerator
    file = ../moose/pcm_solid_in.e
  []
[]

[Variables]
  [temp]
    initial_condition = ${T_inlet}
  []
[]

[AuxVariables]
  [heat_source]
    family = MONOMIAL
    order = CONSTANT
  []
[]

[Kernels]
  [hc]
    type = HeatConduction
    variable = temp
  []
  [heat]
    type = CoupledForce
    variable = temp
    v = heat_source
  []
[]

[Functions]
  [T_fluid]
    type = ParsedFunction
    expression = '${T_inlet} + ${dT_coolant} * (z / ${height})'
  []
[]

[BCs]
  [clad_surface]
    type = ConvectiveFluxFunction
    variable = temp
    boundary = 'rmax'
    T_infinity = T_fluid
    coefficient = 0.109778
  []
[]

[Materials]
  [k_fuel]
    type = GenericConstantMaterial
    prop_names = 'thermal_conductivity'
    prop_values = '0.18'
    block = 'fuel fuel_center'
  []
  [k_clad]
    type = GenericConstantMaterial
    prop_names = 'thermal_conductivity'
    prop_values = '0.16'
    block = 'clad'
  []
[]

[Executioner]
  type = Transient
  nl_abs_tol = 1e-8
  num_steps = 5
  petsc_options_iname = '-pc_type -pc_hypre_type'
  petsc_options_value = 'hypre boomeramg'
[]

[MultiApps]
  [openmc]
    type = TransientMultiApp
    input_files = 'openmc.i'
    execute_on = timestep_end
  []
[]

[Transfers]
  [heat_source_from_openmc]
    type = MultiAppGeneralFieldShapeEvaluationTransfer
    from_multi_app = openmc
    variable = heat_source
    source_variable = heat_source
    from_postprocessors_to_be_preserved = heat_source
    to_postprocessors_to_be_preserved = source_integral
  []
  [temp_to_openmc]
    type = MultiAppGeneralFieldShapeEvaluationTransfer
    to_multi_app = openmc
    variable = temp
    source_variable = temp
  []
[]

[Postprocessors]
  [source_integral]
    type = ElementIntegralVariablePostprocessor
    variable = heat_source
    execute_on = transfer
  []
  [max_T_fuel]
    type = NodalExtremeValue
    variable = temp
    block = 'fuel fuel_center'
  []
  [avg_T_fuel]
    type = ElementAverageValue
    variable = temp
    block = 'fuel fuel_center'
  []
  [max_T_clad]
    type = NodalExtremeValue
    variable = temp
    block = 'clad'
  []
  [avg_T_clad]
    type = ElementAverageValue
    variable = temp
    block = 'clad'
  []
  [max_T]
    type = NodalExtremeValue
    variable = temp
  []
[]

[Outputs]
  exodus = true
  csv = true
  print_linear_residuals = false
[]
