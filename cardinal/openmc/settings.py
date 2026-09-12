"""pcM independent OpenMC settings.

Batch/particle counts are pcM's own numerical choices and are subject to the
Phase 11 convergence study. They are never adjusted to move k.
"""

import openmc

# Two-group structure from spec/operating.md
THERMAL_CUTOFF = 0.625  # eV
GROUP_EDGES = [0.0, THERMAL_CUTOFF, 20.0e6]  # eV

# Named numerical configurations
SMOKE = dict(particles=1000, inactive=10, batches=40)
BASELINE = dict(particles=10000, inactive=50, batches=250)
PRODUCTION = dict(particles=40000, inactive=100, batches=500)


def eigenvalue_settings(particles, inactive, batches, bounds, seed=1,
                        entropy_dimension=(8, 8, 8),
                        temperature_method="interpolation"):
    """k-eigenvalue settings with a uniform starting source in `bounds`."""
    s = openmc.Settings()
    s.run_mode = "eigenvalue"
    s.particles = particles
    s.inactive = inactive
    s.batches = batches
    s.seed = seed

    s.source = openmc.IndependentSource(
        space=openmc.stats.Box(bounds[:3], bounds[3:], only_fissionable=True)
    )

    # Shannon entropy for source-convergence diagnosis (Phase 5)
    entropy = openmc.RegularMesh()
    entropy.lower_left = bounds[:3]
    entropy.upper_right = bounds[3:]
    entropy.dimension = list(entropy_dimension)
    s.entropy_mesh = entropy

    s.temperature = {"method": temperature_method, "tolerance": 100.0}
    s.output = {"tallies": False, "summary": True}
    return s


def unit_cell_settings(config, pitch, half_z, seed=1):
    """2-D reflective slab cell: entropy mesh is flat in z."""
    h = pitch / 2.0
    bounds = [-h, -h, -half_z, h, h, half_z]
    return eigenvalue_settings(
        bounds=bounds, seed=seed, entropy_dimension=(8, 8, 1), **config
    )


def core_settings(config, radius, height, seed=1):
    bounds = [-radius, -radius, -height / 2.0, radius, radius, height / 2.0]
    return eigenvalue_settings(bounds=bounds, seed=seed, **config)
