#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
import opengate.contrib.spect.siemens_intevo as intevo
from scipy.spatial.transform import Rotation
from spect_helpers import add_digitizer_intevo_lu177
from pathlib import Path

if __name__ == "__main__":

    # folders
    simu_name = "test001"

    # create the simulation
    sim = gate.Simulation()

    # main options
    #sim.visu = True # uncomment to enable visualisation
    #sim.visu_type = "qt"
    sim.random_seed = "auto"
    sim.number_of_threads = 2
    sim.progress_bar = True
    sim.output_dir = Path("./output")

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
    head, colli, crystal = intevo.add_spect_head(
        sim, "spect", collimator_type="melp", debug=(sim.visu and sim.visu_type != "qt")
    )
    head.translation = [0, 0, -280 * mm]
    head.rotation = Rotation.from_euler("xy", (90, 90), degrees=True).as_matrix()

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 10 * mm)
    sim.physics_manager.set_production_cut(crystal.name, "all", 2 * mm)

    # two simple sources
    source1 = sim.add_source("GenericSource", "source1")
    source1.particle = "gamma"
    source1.position.type = "sphere"
    source1.position.radius = 3 * cm
    source1.position.translation = [8 * cm, 0, 0]
    source1.direction.type = "iso"
    source1.direction.acceptance_angle.volumes = [head.name]
    source1.direction.acceptance_angle.intersection_flag = True
    #source1.direction.acceptance_angle.skip_policy = "ZeroEnergy"
    source1.energy.mono = 113 * keV
    source1.activity = 1e4 * Bq / sim.number_of_threads

    # two simple sources
    source2 = sim.add_source("GenericSource", "source2")
    source2.particle = "gamma"
    source2.position.type = "box"
    source2.position.size = [3 * cm, 3 * cm, 3 * cm]
    source2.position.translation = [0, 8 * cm, 0]
    source2.direction.type = "iso"
    source2.direction.acceptance_angle.volumes = [head.name]
    source2.direction.acceptance_angle.intersection_flag = True
    #source2.direction.acceptance_angle.skip_policy = "ZeroEnergy"
    source2.energy.mono = 208 * keV
    source2.activity = 1e4 * Bq / sim.number_of_threads

    # digitizer : probably not correct
    proj = add_digitizer_intevo_lu177(sim, head.name, crystal.name)
    proj.output_filename = f"{simu_name}_projection.mhd"
    print(f'Projection size: {proj.size}')
    print(f'Projection spacing: {proj.spacing} mm')
    print(f'Projection output: {proj.get_output_path()}')

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.track_types_flag = True
    stats.output_filename = f"{simu_name}_stats.txt"

    # go
    time = 300 * sec
    if sim.visu:
        time = 0.01 * sec
    sim.run_timing_intervals = [[0, time]]
    sim.run()

    # print
    print(stats)
