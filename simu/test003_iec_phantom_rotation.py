#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from spect_helpers import *
import opengate.contrib.phantoms.nemaiec as gate_iec
import opengate.contrib.spect.spect_helpers as spect_helpers
from scipy.spatial.transform import Rotation
from opengate.sources.base import set_source_rad_energy_spectrum
from pathlib import Path

if __name__ == "__main__":

    # folders
    simu_name = "test003"

    # create the simulation
    sim = gate.Simulation()

    # main options
    sim.visu = True  # uncomment to enable visualisation
    sim.visu_type = "qt"
    sim.random_seed = "auto"
    sim.number_of_threads = 8
    sim.progress_bar = True
    sim.output_dir = Path("./output")
    if sim.visu:
        sim.number_of_threads = 1

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

    # spect heads
    heads, crystals = add_intevo_two_heads(sim, "spect", "melp", 40 * cm)

    # phantom
    phantom = gate_iec.add_iec_phantom(sim, name="phantom")

    # table
    table = spect_helpers.add_fake_table(sim, "table")
    table.translation = [0, 31 * cm, 0]

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 10 * mm)
    sim.physics_manager.set_production_cut("phantom", "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystals[0].name, "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystals[1].name, "all", 2 * mm)

    # add sources for all spheres
    a = 1e4 * BqmL / sim.number_of_threads
    activity_Bq_mL = [a] * 6
    sources = gate_iec.add_spheres_sources(
        sim, phantom.name, "sources", "all", activity_Bq_mL, verbose=True
    )
    for source in sources:
        set_source_rad_energy_spectrum(source, "lu177")
        source.particle = "gamma"

    # digitizer : probably not correct (yet)
    for i in range(2):
        proj = add_digitizer_intevo_lu177(sim, heads[i].name, crystals[i].name)
        proj.output_filename = f"{simu_name}_projection_{i}.mhd"
        print(f"Projection size: {proj.size}")
        print(f"Projection spacing: {proj.spacing} mm")
        print(f"Projection output: {proj.get_output_path()}")

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.track_types_flag = True
    stats.output_filename = f"{simu_name}_stats.txt"

    # set the runs
    n = 60
    total_time = 300 * sec
    if sim.visu:
        total_time = 0.001 * sec
    start_time = 0
    step_time = total_time / n
    end_time = step_time
    sim.run_timing_intervals = []
    for r in range(n):
        sim.run_timing_intervals.append([start_time, end_time])
        start_time = end_time
        end_time += step_time

    # compute the gantry rotations
    step_angle = 180 / n
    initial_rot = Rotation.from_euler("X", 90, degrees=True)
    rotate_gantry(heads[0], 40 * cm, initial_rot, 0, step_angle, n)

    initial_rot = Rotation.from_euler("ZX", (180, 90), degrees=True)
    rotate_gantry(heads[1], -40 * cm, initial_rot, 0, step_angle, n)

    # go !
    # sim.running_verbose_level = gate.logger.RUN
    sim.run()
    print("done")

    # print
    print(stats)
