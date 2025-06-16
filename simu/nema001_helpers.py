#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate.contrib.spect.ge_discovery_nm670 as nm670
from opengate.contrib.spect.spect_helpers import add_fake_table
from spect_helpers import *
from pathlib import Path


def set_nema001_simulation(sim, simu_name, distance, collimator, rad):

    # main options
    # sim.visu = True
    sim.visu_type = "vrml_file_only"
    sim.visu_filename = "test.wrl"
    sim.random_seed = "auto"
    sim.number_of_threads = 30
    sim.progress_bar = True
    sim.output_dir = Path("output_iec") / simu_name

    # units
    sec = gate.g4_units.s
    min = gate.g4_units.min
    mm = gate.g4_units.mm
    cm = gate.g4_units.cm
    cm3 = gate.g4_units.cm3
    m = gate.g4_units.m
    Bq = gate.g4_units.Bq
    keV = gate.g4_units.keV
    BqmL = Bq / cm3

    # acquisition param
    time = 20 * min
    activity = 3e6 * Bq / sim.number_of_threads
    conc_a = 10000 * BqmL / sim.number_of_threads
    if sim.visu:
        time = 10 * sec
        activity = 5 * Bq
        conc_a = 10 * BqmL
        sim.number_of_threads = 1
    

    # world
    world = sim.world
    world.size = [2 * m, 2 * m, 2 * m]
    world.material = "G4_AIR"
    world.color = [0, 0, 0, 0]

    # spect head
    head, colli, crystal = nm670.add_spect_head(
        sim,
        "spect",
        collimator_type=collimator,
        rotation_deg=15,
        crystal_size="5/8",
        debug=sim.visu,
    )

    head.translation = [0, 40 * cm, 0]

    # CREATE phantom and source with AA to speedup + (fake) table
    table = add_fake_table(sim, "table")
    table.translation = [0, 30.2 * cm, 0]

    iec_phantom = add_iec_phantom(sim, aa_volumes= [head.name], conc_a=conc_a, rad=rad, name_supp= "phantom")
    spacing = (2.2098 * mm, 2.2098 * mm, 2.2098 * mm)
    labels, image = voxelize_geometry(sim, extent=iec_phantom, spacing=spacing)
    filenames = write_voxelized_geometry(sim, labels, image, Path("output_iec") / "test_iec_vox.mhd")
    print(filenames)
    
    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 10 * mm)
    #sim.physics_manager.set_production_cut("phantom", "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystal.name, "all", 2 * mm)

    # digitizer : probably not correct
    digit = add_digitizer_tc99m_wip(sim, crystal.name, "digitizer", False)
    proj = digit.find_module("projection")
    proj.output_filename = f"{simu_name}_projection.mhd"
    print(f"Projection size: {proj.size}")
    print(f"Projection spacing: {proj.spacing} mm")
    print(f"Projection output: {proj.get_output_path()}")
    digit_blur = digit.find_module("digitizer_sp_blur")

    #rotation
    nb_angle = 120
    rotate_gantry_helpers(head, radius=distance, start_angle_deg=0, step_angle_deg = 3, nb_angle = nb_angle)

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.track_types_flag = True
    stats.output_filename = f"{simu_name}_stats.txt"

    #add attenuation image generation actor
    #mumap = sim.add_actor("AttenuationImageActor", "mumap")
    #mumap.image_volume = iec_phantom  # FIXME volume for the moment, not the name
    #mumap.output_filename = "mumap_iecphantom.mhd"
    #mumap.energy = 140.511 * keV
    #mumap.database = "NIST"  # EPDL
    #mumap.attenuation_image.write_to_disk = True
    #mumap.attenuation_image.active = True

    # timing
    start_time = 0
    step_time = time/nb_angle
    list_time_interval = []
    for i in range(nb_angle):
        list_time_interval.append([step_time*i, step_time*(i+1)])
    sim.run_timing_intervals = list_time_interval
    #sim.run_timing_intervals = [[0, time/2],[time/2, time]]

    return head, iec_phantom, digit_blur