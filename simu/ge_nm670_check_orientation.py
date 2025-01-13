#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import opengate as gate
import opengate.contrib.spect.ge_discovery_nm670 as nm670
from opengate.contrib.spect.spect_helpers import add_fake_table


if __name__ == "__main__":

    # create the simulation
    sim = gate.Simulation()

    # main options
    sim.visu = True
    sim.visu_type = "qt"
    sim.random_seed = "auto"
    sim.number_of_threads = 1
    sim.progress_bar = True

    # units
    sec = gate.g4_units.s
    deg = gate.g4_units.deg
    mm = gate.g4_units.mm
    cm = gate.g4_units.cm
    m = gate.g4_units.m
    cm3 = gate.g4_units.cm3
    Bq = gate.g4_units.Bq
    BqmL = Bq / cm3
    keV = gate.g4_units.keV

    # world
    world = sim.world
    world.size = [2 * m, 2 * m, 2 * m]
    world.material = "G4_AIR"

    # spect head
    head, colli, crystal = nm670.add_spect_head(
        sim, "spect", collimator_type="lehr", debug=sim.visu, crystal_size="5/8"
    )
    nm670.rotate_gantry(head, radius=10 * cm, start_angle_deg=0)

    # phantom + (fake) table
    table = add_fake_table(sim, "table")
    table.translation = [0, 20.5 * cm, 0]
    sim.run()
