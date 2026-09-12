# pcM OpenMC sub-app for Cardinal coupling.
#
# Receives temperature from the MOOSE solid app, returns the fission heat
# source. Syntax follows Cardinal's installed lwr_solid tutorial.

[Mesh]
  [file]
    type = FileMeshGenerator
    file = ../moose/pcm_solid_in.e
  []
[]

[AuxVariables]
  [cell_temperature]
    family = MONOMIAL
    order = CONSTANT
  []
[]

[AuxKernels]
  [cell_temperature]
    type = CellTemperatureAux
    variable = cell_temperature
  []
[]

[Problem]
  type = OpenMCCellAverageProblem
  verbose = true

  # Average pin power from pcM's own core calculation:
  # 250 kW / 120 fuelled pins = 2083.33 W. See results/PCM_RESULTS.md.
  power = 2083.33

  temperature_blocks = 'fuel fuel_center clad'
  cell_level = 0

  volume_calculation = vol

  [Tallies]
    [heat_source]
      type = CellTally
      block = 'fuel fuel_center'
      name = heat_source
    []
  []
[]

[UserObjects]
  [vol]
    type = OpenMCVolumeCalculation
    n_samples = 100000
  []
[]

[Executioner]
  type = Transient
[]

[Outputs]
  exodus = true
  csv = true
[]

[Postprocessors]
  [heat_source]
    type = ElementIntegralVariablePostprocessor
    variable = heat_source
    block = 'fuel fuel_center'
  []
  [max_tally_rel_err]
    type = TallyRelativeError
  []
  [k_eff]
    type = KEigenvalue
  []
  [max_heat_source]
    type = ElementExtremeValue
    variable = heat_source
    block = 'fuel fuel_center'
  []
[]
