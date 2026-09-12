"""pcM independent material definitions.

Compositions from spec/materials.md (approved problem definition).
Assumption IDs (A1, A3, A5...) refer to that file.
"""

import openmc

REF_TEMPERATURE = 293.0  # K, spec/operating.md O1


def fuel(temperature=REF_TEMPERATURE):
    """U-ZrH(1.65), 20% enriched, 8.5 wt% U total."""
    m = openmc.Material(name="U-ZrH1.65 fuel")
    m.set_density("g/cm3", 6.0)
    m.add_nuclide("U235", 1.7, "wo")
    m.add_nuclide("U238", 6.8, "wo")
    m.add_element("Zr", 89.862, "wo")  # A1: natural isotopics
    m.add_nuclide("H1", 1.638, "wo")
    # A3: hydride-bound scattering. Free-gas H here would be physically wrong
    # and shifts k by thousands of pcm.
    m.add_s_alpha_beta("c_H_in_ZrH")
    m.add_s_alpha_beta("c_Zr_in_ZrH")
    m.temperature = temperature
    return m


def clad(temperature=REF_TEMPERATURE):
    """SS304. A5/A6: density and composition are pcM assumptions, not in spec."""
    m = openmc.Material(name="SS304 clad")
    m.set_density("g/cm3", 8.00)
    m.add_element("Fe", 68.67, "wo")
    m.add_element("Cr", 19.0, "wo")
    m.add_element("Ni", 9.25, "wo")
    m.add_element("Mn", 2.0, "wo")
    m.add_element("Si", 1.0, "wo")
    m.add_element("C", 0.08, "wo")
    m.temperature = temperature
    return m


def water(temperature=REF_TEMPERATURE):
    """Light water moderator/coolant. A7: no boron."""
    m = openmc.Material(name="Light water")
    m.set_density("g/cm3", 1.0)
    m.add_element("H", 2.0)
    m.add_element("O", 1.0)
    m.add_s_alpha_beta("c_H_in_H2O")  # A8
    m.temperature = temperature
    return m


def unit_cell_materials(temperature=REF_TEMPERATURE):
    """Return (fuel, clad, water, Materials collection)."""
    f, c, w = fuel(temperature), clad(temperature), water(temperature)
    return f, c, w, openmc.Materials([f, c, w])


# Volume fractions derived in spec/geometry.md from the specified radii/pitch.
VOL_FRAC = {"fuel": 0.57701, "clad": 0.03290, "water": 0.39009}


def homogenized_core(temperature=REF_TEMPERATURE, sab="zrh"):
    """Single homogenized core zone (G5).

    Volume-weighted smear of the unit-cell constituents.

    KNOWN LIMITATION. Hydrogen exists in two distinct bound states in this
    core - H in ZrH (~56% of all H) and H in H2O (~44%) - but OpenMC permits
    each nuclide to appear in only one thermal-scattering table per material.
    A single smeared zone therefore CANNOT represent both kernels. No choice of
    `sab` is correct; the three options bracket the error instead of hiding it:

        "zrh"  - all H treated as bound in ZrH
        "h2o"  - all H treated as bound in H2O
        "none" - free-gas H (physically worst, included as a bound)

    The heterogeneous lattice core (geometry.lattice_core) has no such defect
    and is pcM's primary core model. See PCM_STATUS.md Q4.
    """
    parts = {
        "fuel": (fuel(temperature), VOL_FRAC["fuel"]),
        "clad": (clad(temperature), VOL_FRAC["clad"]),
        "water": (water(temperature), VOL_FRAC["water"]),
    }

    smeared = {}
    h_by_source = {}
    for label, (constituent, vfrac) in parts.items():
        for nuclide, density in constituent.get_nuclide_atom_densities().items():
            contribution = float(density) * vfrac
            smeared[nuclide] = smeared.get(nuclide, 0.0) + contribution
            if nuclide == "H1":
                h_by_source[label] = h_by_source.get(label, 0.0) + contribution

    total = sum(smeared.values())

    m = openmc.Material(name="Homogenized core zone")
    m.set_density("atom/b-cm", total)
    for nuclide, density in sorted(smeared.items()):
        m.add_nuclide(nuclide, density / total, "ao")

    if sab == "zrh":
        m.add_s_alpha_beta("c_H_in_ZrH")
        m.add_s_alpha_beta("c_Zr_in_ZrH")
    elif sab == "h2o":
        m.add_s_alpha_beta("c_H_in_H2O")
        m.add_s_alpha_beta("c_Zr_in_ZrH")
    elif sab == "none":
        pass
    else:
        raise ValueError(f"unknown sab option {sab!r}")

    m.temperature = temperature
    m.hydrogen_split = {k: v / sum(h_by_source.values())
                        for k, v in h_by_source.items()}
    return m
