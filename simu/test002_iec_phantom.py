#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
import opengate.contrib.phantoms.nemaiec as gate_iec
import opengate.contrib.spect.siemens_intevo as intevo
from opengate.sources.base import set_source_rad_energy_spectrum
from scipy.spatial.transform import Rotation
from spect_helpers import add_digitizer_intevo_lu177
from pathlib import Path

if __name__ == "__main__":

    # folders
    simu_name = "test002"

    # create the simulation
    sim = gate.Simulation()

    # main options
    # sim.visu = True # uncomment to enable visualisation
    sim.visu_type = "vrml"
    sim.random_seed = "auto"
    sim.number_of_threads = 4
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
    head.translation = [0, 0, 250 * mm]
    # (fake rotation to be in front of the phantom)
    head.rotation = Rotation.from_euler("zx", (90, 90), degrees=True).as_matrix()

    # phantom
    phantom = gate_iec.add_iec_phantom(sim, name="phantom")

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 10 * mm)
    sim.physics_manager.set_production_cut("phantom", "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystal.name, "all", 2 * mm)

    # add sources for all spheres
    a = 1e4 * BqmL / sim.number_of_threads
    activity_Bq_mL = [a] * 6
    sources = gate_iec.add_spheres_sources(
        sim, phantom.name, "sources", "all", activity_Bq_mL, verbose=True
    )
    for source in sources:
        gate.sources.base.set_source_rad_energy_spectrum(source, "lu177")
        source.particle = "gamma"
        source.direction.acceptance_angle.volumes = [head.name]
        source.direction.acceptance_angle.intersection_flag = True

    # digitizer : probably not correct
    proj = add_digitizer_intevo_lu177(sim, head.name, crystal.name)
    proj.output_filename = f"{simu_name}_projection.mhd"
    print(f"Projection size: {proj.size}")
    print(f"Projection spacing: {proj.spacing} mm")
    print(f"Projection output: {proj.get_output_path()}")

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.track_types_flag = True
    stats.output_filename = f"{simu_name}_stats.txt"

    # go
    time = 300 * sec
    if sim.visu:
        time = 0.001 * sec
    sim.run_timing_intervals = [[0, time]]
    sim.run()

    # print
    print(stats)
