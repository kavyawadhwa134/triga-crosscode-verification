# pcM NekRS fluid mesh: TRIGA coolant subchannel.
#
# Square-pitch cell (4.235 cm) with the clad outer surface (r = 1.866 cm)
# removed. Dimensions in METRES to match Cardinal's NekRS tutorial convention.
#
# NOTE the TRIGA pin is proportionally much fatter than the LWR/SFR tutorial
# pins: r/(pitch/2) = 0.881 here vs 0.758 in the SFR tutorial, leaving a
# minimum gap of only 2.515 mm. Boundary layers are sized to that gap rather
# than copied from the tutorial.
#
# Build:  cardinal-opt -i fluid.i --mesh-only

pin_diameter = 3.732e-2      # 2 * clad outer radius (spec)
pin_pitch = 4.235e-2         # spec
height = 0.60                # spec core height
num_layers = 12
fluid_id = 5

# Boundary layers, measured outward from the clad surface (r = 1.866e-2 m).
# Minimum gap to the flat of the square is 2.515e-3 m.
bl_0 = 1.8680e-2
bl_1 = 1.8710e-2
bl_2 = 1.8770e-2
bl_3 = 1.8890e-2
bl_4 = 1.9110e-2
bl_5 = 1.9510e-2

[Mesh]
  [pin]
    type = PolygonConcentricCircleMeshGenerator
    num_sides = 4
    polygon_size = ${fparse pin_pitch / 2.0}
    num_sectors_per_side = '6 6 6 6'
    uniform_mesh_on_sides = true

    ring_radii = '${fparse pin_diameter / 2.0} ${bl_0} ${bl_1} ${bl_2} ${bl_3} ${bl_4} ${bl_5}'
    ring_intervals = '1 1 1 1 1 1 1'
    ring_block_ids = '${fparse fluid_id + 1} ${fluid_id} ${fluid_id} ${fluid_id} ${fluid_id} ${fluid_id} ${fluid_id}'

    background_block_ids = '${fluid_id}'
    background_intervals = 4
  []
  [pin_surface]
    type = SideSetsBetweenSubdomainsGenerator
    input = pin
    primary_block = ${fluid_id}
    paired_block = ${fparse fluid_id + 1}
    new_boundary = '1'
  []
  [delete_solid]
    type = BlockDeletionGenerator
    input = pin_surface
    block = ${fparse fluid_id + 1}
  []
  [rotate]
    type = TransformGenerator
    input = delete_solid
    transform = rotate
    vector_value = '45.0 0.0 0.0'
  []
  [delete_extra_surfaces]
    type = BoundaryDeletionGenerator
    input = rotate
    boundary_names = '2 3 4 5 6 7'
  []
  [extrude]
    type = AdvancedExtruderGenerator
    input = delete_extra_surfaces
    direction = '0 0 1'
    num_layers = '${num_layers}'
    heights = '${height}'
    bottom_boundary = '2'
    top_boundary = '3'
  []
  # Select only the four planar outer faces. The former sequence of
  # SideSetsAroundSubdomainGenerator objects also matched curved clad faces
  # whose normals happened to point near +/-x or +/-y. Those faces acquired
  # duplicate lateral IDs and exo2nek retained only 59% of the heated wall as
  # boundary 1. A fixed-normal generator leaves the curved wall untouched.
  [lateral]
    type = SideSetsFromNormalsGenerator
    input = extrude
    normals = ' 1  0  0
               -1  0  0
                0  1  0
                0 -1  0'
    fixed_normal = true
    normal_tol = 1e-5
    new_boundary = '4 5 6 7'
  []

  second_order = true
[]
