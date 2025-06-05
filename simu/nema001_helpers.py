#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate.contrib.spect.ge_discovery_nm670 as nm670
from opengate.contrib.spect.spect_helpers import add_fake_table
from spect_helpers import *
from pathlib import Path


def set_nema001_simulation(sim, simu_name):

    # main options
    # sim.visu = True
    sim.visu_type = "vrml_file_only"
    sim.visu_filename = "energy_resolution.wrl"
    sim.random_seed = "auto"
    sim.number_of_threads = 30
    sim.progress_bar = True
    sim.output_dir = Path("energy_resolution") / simu_name
    #sim.verbose_level = "DEBUG"
    #sim.visu_verbose = True

    # units
    sec = gate.g4_units.s
    min = gate.g4_units.min
    mm = gate.g4_units.mm
    cm = gate.g4_units.cm
    m = gate.g4_units.m
    Bq = gate.g4_units.Bq

    # acquisition param
    time = 5 * min
    activity = 3e6 * Bq / sim.number_of_threads
    if sim.visu:
        time = 1 * sec
        activity = 1 * Bq
        sim.number_of_threads = 1

    # world
    world = sim.world
    world.size = [10 * m, 10 * m, 10 * m]
    world.material = "G4_AIR"

    # spect head
    #head, colli, crystal = nm670.add_spect_head(
    #    sim,
    #    "spect",
    #    collimator_type= None,
    #    rotation_deg=15,
    #    crystal_size="5/8",
    #    debug=sim.visu,
    #)
    #nm670.rotate_gantry(head, radius=10 * cm, start_angle_deg=0)

    # spect two head
    head, crystal = nm670.add_spect_two_heads(
        sim,
        "spect",
        collimator_type= "plexi",
        rotation_deg=15,
        crystal_size="5/8",
        debug=sim.visu,
    )
    nm670.rotate_gantry(head[0], radius=0 * cm, start_angle_deg=0)
    nm670.rotate_gantry(head[1], radius=38.5 * cm, start_angle_deg=0)

    # phantom + (fake) table
    table = add_fake_table(sim, "table")
    table.translation = [0, 20.5 * cm, -130 * cm]
    glass_tube = add_phantom_energy_resolution(sim, "phantom")

    # source without AA
    container = sim.volume_manager.get_volume(f"phantom_source_container")
    #src = add_source_energy_resolution(sim, "source", container, "Tc99m")
    src = add_source_energy_resolution(sim, "source", container, "Lu177")
    src.activity = activity

    # source with AA to speedup
    #container = sim.volume_manager.get_volume(f"phantom_source_container")
    #src = add_source_energy_resolution(sim, "source", container, "Tc99m", [head.name])
    #src.activity = activity

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 10 * mm)
    sim.physics_manager.set_production_cut("phantom", "all", 2 * mm)
    # One head
    #sim.physics_manager.set_production_cut(crystal.name, "all", 2 * mm)
    # Two heads
    sim.physics_manager.set_production_cut(crystal[0].name, "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystal[1].name, "all", 2 * mm)

    # digitizer : probably not correct
    # One head
    """ digit = add_digitizer_tc99m_wip(sim, crystal.name, "digitizer", False)

    proj = digit.find_module("projection")
    proj.output_filename = f"{simu_name}_projection.mhd"
    print(f"Projection size: {proj.size}")
    print(f"Projection spacing: {proj.spacing} mm")
    print(f"Projection output: {proj.get_output_path()}")
    digit_blur = digit.find_module("digitizer_sp_blur")
    ener_blur = digit.find_module("digitizer_blur")
    ener_blur.output_filename = f"{simu_name}_energy.root" """

    # Two heads
    #digit0 = add_digitizer_tc99m_wip(sim, crystal[0].name, "digitizer1", False)
    #digit1 = add_digitizer_tc99m_wip(sim, crystal[1].name, "digitizer2", False)
    digit0 = add_digitizer_lu177_wip(sim, crystal[0].name, "digitizer1", False)
    digit1 = add_digitizer_lu177_wip(sim, crystal[1].name, "digitizer2", False)

    proj0 = digit0.find_module("projection")
    proj0.output_filename = f"{simu_name}_projectionhead1.mhd"
    print(f"Projection size: {proj0.size}")
    print(f"Projection spacing: {proj0.spacing} mm")
    print(f"Projection output: {proj0.get_output_path()}")
    digit_blur = digit0.find_module("digitizer1_sp_blur")
    ener_blur = digit0.find_module("digitizer1_blur")
    ener_win = digit0.find_module("digitizer1_energy_window")
    ener_win.output_filename = f"{simu_name}_energywin_head1.root"
    ener_blur.output_filename = f"{simu_name}_energy_head1.root"

    proj1 = digit1.find_module("projection")
    proj1.output_filename = f"{simu_name}_projectionhead2.mhd"
    print(f"Projection size: {proj1.size}")
    print(f"Projection spacing: {proj1.spacing} mm")
    print(f"Projection output: {proj1.get_output_path()}")
    digit_blur = digit1.find_module("digitizer2_sp_blur")
    ener_blur = digit1.find_module("digitizer2_blur")
    ener_blur.output_filename = f"{simu_name}_energy_head2.root"

    
    # add PhaseSpace actor
    phsp = sim.add_actor("PhaseSpaceActor", "PhaseSpace")
    phsp.attached_to = "spect_1_crystal"
    phsp.attributes = [
    "KineticEnergy",
    "TotalEnergyDeposit",
    "Weight",
    "EventPosition",
    ]
    phsp.output_filename = "test019_hits.root"
    f = sim.add_filter("ParticleFilter", "f")
    f.particle = "gamma"
    phsp.filters.append(f)

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.track_types_flag = True
    stats.output_filename = f"{simu_name}_stats.txt"

    # timing
    sim.run_timing_intervals = [[0, time]]

    return head, glass_tube, digit_blur
