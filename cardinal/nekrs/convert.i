# Convert the HEX27 fluid mesh to the HEX20 format NekRS requires, preserving
# curvature on the clad surface, and non-dimensionalize by the hydraulic
# diameter.
#
# Build:  cardinal-opt -i convert.i --mesh-only && mv convert_in.e convert.exo

pin_diameter = 3.732e-2
pin_pitch = 4.235e-2

flow_area = ${fparse pin_pitch * pin_pitch - pi * pin_diameter * pin_diameter / 4.0}
wetted_perimeter = ${fparse pi * pin_diameter}
hydraulic_diameter = ${fparse 4.0 * flow_area / wetted_perimeter}

[Mesh]
  [file]
    type = FileMeshGenerator
    file = fluid_in.e
  []
  [to_hex20]
    type = NekMeshGenerator
    input = file
    boundary = '1'
    radius = ${fparse pin_diameter / 2.0}
    boundaries_to_rebuild = '1 2 3 4 5 6 7'
    layers = '6'
    geometry_type = cylinder
  []
  [scale]
    type = TransformGenerator
    input = to_hex20
    transform = scale
    vector_value = '${fparse 1.0 / hydraulic_diameter} ${fparse 1.0 / hydraulic_diameter} ${fparse 1.0 / hydraulic_diameter}'
  []
[]
