# pcM solid mesh: TRIGA fuel pin + SS304 clad, no gap.
#
# Dimensions from spec/geometry.md. The specification gives only two radii, so
# the clad inner radius equals the fuel outer radius (assumption G1) and the
# two meshes are stitched into direct thermal contact rather than separated by
# a gap as in Cardinal's LWR tutorial.
#
# Build with:  cardinal-opt -i mesh.i --mesh-only pcm_solid_in.e
#
# Blocks: 'fuel' (HEX8) and 'fuel_center' (PRISM6, the annular mesh axis) are
# both fuel - Exodus forbids mixed element types in one block, so they stay
# separate. 'clad' is the SS304 annulus.

fuel_or = 1.815
clad_or = 1.866
height = 60.0
n_axial = 20

[Mesh]
  [fuel]
    type = AnnularMeshGenerator
    nr = 8
    nt = 32
    rmin = 0
    rmax = ${fuel_or}
    quad_subdomain_id = 1
    tri_subdomain_id = 3
  []
  [clad]
    type = AnnularMeshGenerator
    nr = 2
    nt = 32
    rmin = ${fuel_or}
    rmax = ${clad_or}
    quad_subdomain_id = 2
    tri_subdomain_id = 4
  []
  [stitch]
    type = StitchMeshGenerator
    inputs = 'fuel clad'
    stitch_boundaries_pairs = 'rmax rmin'
    clear_stitched_boundary_ids = true
  []
  [extrude]
    type = AdvancedExtruderGenerator
    input = stitch
    heights = '${height}'
    num_layers = '${n_axial}'
    direction = '0 0 1'
  []
  [name_blocks]
    type = RenameBlockGenerator
    input = extrude
    old_block = '1 3 2'
    new_block = 'fuel fuel_center clad'
  []
  parallel_type = replicated
[]
