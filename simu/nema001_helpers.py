#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate.contrib.spect.ge_discovery_nm670 as nm670
from opengate.contrib.spect.spect_helpers import add_fake_table
from spect_helpers import *
from pathlib import Path


def set_nema001_simulation(sim, simu_name, scatter, collimator):

    # main options
    # sim.visu = True
    sim.visu_type = "vrml_file_only"
    sim.visu_filename = "spatial_resolution.wrl"
    sim.number_of_threads = 32
    sim.progress_bar = True
    sim.output_dir = Path("planar_spatial_res") / simu_name

    # units
    sec = gate.g4_units.s
    min = gate.g4_units.min
    mm = gate.g4_units.mm
    cm = gate.g4_units.cm
    m = gate.g4_units.m
    Bq = gate.g4_units.Bq

    # acquisition param
    time = 5 * min
    activity = 3e7 * Bq / sim.number_of_threads
    if sim.visu:
        time = 1 * sec
        activity = 100 * Bq
        sim.number_of_threads = 1

    # world
    world = sim.world
    world.size = [2 * m, 2 * m, 2 * m]
    world.material = "G4_AIR"

    # spect head
    head, colli, crystal = nm670.add_spect_head(
        sim,
        "spect",
        collimator_type= collimator,
        rotation_deg=15,
        crystal_size="5/8",
        debug=sim.visu,
    )
    #nm670.rotate_gantry(head, radius=0 * cm, start_angle_deg=0)

    # phantom + (fake) table
    table = add_fake_table(sim, "table")
    table.translation = [0, 31.2 * cm, 0]
    glass_tube = add_phantom_spatial_resolution(sim, "phantom", scatter)
    if scatter is True:
        top_plates, bottom_plates = add_PMMA_plates(sim, "PMMA_plates")
        top_plates.translation = [0, 5.075 * cm, 0]
        bottom_plates.translation = [0,  -2.575* cm, 0]

    # source with AA to speedup
    # setup for 1 source
    container = sim.volume_manager.get_volume(f"phantom_source_container")
    src = add_source_spatial_resolution(sim, "source", container, "Lu177") # , [head.name]
    src.activity = activity

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 10 * mm)
    sim.physics_manager.set_production_cut("phantom", "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystal.name, "all", 2 * mm)

    # digitizer : probably not correct
    digit = add_digitizer_lu177_wip(sim, crystal.name, "digitizer", False)
    proj = digit.find_module("projection")
    proj.output_filename = f"{simu_name}_projection.mhd"
    print(f"Projection size: {proj.size}")
    print(f"Projection spacing: {proj.spacing} mm")
    print(f"Projection output: {proj.get_output_path()}")
    digit_blur = digit.find_module("digitizer_sp_blur")

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.track_types_flag = True
    stats.output_filename = f"{simu_name}_stats.txt"

    # timing
    sim.run_timing_intervals = [[0, time]]

    return head, glass_tube, digit_blur

def set_nema001_simulation_2sources(sim, simu_name, scatter, collimator):

    # main options
    # sim.visu = True
    sim.visu_type = "vrml_file_only"
    sim.visu_filename = "spatial_resolution.wrl"
    sim.number_of_threads = 32
    sim.progress_bar = True
    sim.output_dir = Path("planar_spatial_res") / simu_name

    # units
    sec = gate.g4_units.s
    min = gate.g4_units.min
    mm = gate.g4_units.mm
    cm = gate.g4_units.cm
    m = gate.g4_units.m
    Bq = gate.g4_units.Bq

    # acquisition param
    time = 5 * min
    activity = 3e7 * Bq / sim.number_of_threads
    if sim.visu:
        time = 1 * sec
        activity = 100 * Bq
        sim.number_of_threads = 1

    # world
    world = sim.world
    world.size = [2 * m, 2 * m, 2 * m]
    world.material = "G4_AIR"

    # spect head
    head, colli, crystal = nm670.add_spect_head(
        sim,
        "spect",
        collimator_type= collimator,
        rotation_deg=15,
        crystal_size="5/8",
        debug=sim.visu,
    )
    nm670.rotate_gantry(head, radius=10 * cm, start_angle_deg=0)

    # phantom + (fake) table
    table = add_fake_table(sim, "table")
    table.translation = [0, 20.5 * cm, 0]
    glass_tube, glass_tube2 = add_phantom_spatial_resolution_2sources(sim, "phantom", scatter)
    if scatter is True:
        top_plates, bottom_plates = add_PMMA_plates(sim, "PMMA_plates")
        top_plates.translation = [0, 0 * cm, 0]
        bottom_plates.translation = [0, 0 * cm, 0]

    # source with AA to speedup
    #setup for 2 sources
    container = sim.volume_manager.get_volume(f"phantom_source_container")
    container2 = sim.volume_manager.get_volume(f"phantom_source2_container")
    src, src2 = add_2sources_spatial_resolution(sim, "source", "source2", container, container2, "Lu177") #, [head.name] # to add for acceptance angle
    src.activity = activity
    src2.activity = activity

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 10 * mm)
    sim.physics_manager.set_production_cut("phantom", "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystal.name, "all", 2 * mm)

    # digitizer : probably not correct
    digit = add_digitizer_tc99m_wip(sim, crystal.name, "digitizer", False)
    proj = digit.find_module("projection")
    proj.output_filename = f"{simu_name}_projection.mhd"
    print(f"Projection size: {proj.size}")
    print(f"Projection spacing: {proj.spacing} mm")
    print(f"Projection output: {proj.get_output_path()}")
    digit_blur = digit.find_module("digitizer_sp_blur")

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.track_types_flag = True
    stats.output_filename = f"{simu_name}_stats.txt"

    # timing
    sim.run_timing_intervals = [[0, time]]

    return head, glass_tube, glass_tube2, digit_blur