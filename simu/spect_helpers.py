#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
from scipy.spatial.transform import Rotation
import opengate.contrib.spect.siemens_intevo as intevo
from opengate.actors.digitizers import Digitizer
import opengate.contrib.phantoms.nemaiecSPECT as gate_iec
from opengate.voxelize import (
    voxelize_geometry,
    write_voxelized_geometry,
    voxelized_source,
)

def add_digitizer_intevo_lu177(sim, name, crystal_name):
    """
    FIXME : to put contrib.spect.siemens_intevo
    """
    # hits
    hits = sim.add_actor("DigitizerHitsCollectionActor", f"hits_{name}")
    hits.attached_to = crystal_name
    hits.output_filename = ""  # No output
    hits.attributes = [
        "PostPosition",
        "TotalEnergyDeposit",
        "PreStepUniqueVolumeID",
        "PostStepUniqueVolumeID",
        "GlobalTime",
    ]

    # singles
    singles = sim.add_actor("DigitizerAdderActor", f"singles_{name}")
    singles.attached_to = crystal_name
    singles.input_digi_collection = hits.name
    # sc.policy = "EnergyWeightedCentroidPosition"
    singles.policy = "EnergyWinnerPosition"
    singles.output_filename = ""  # No output
    singles.group_volume = None

    # efficiency actor
    eff = sim.add_actor("DigitizerEfficiencyActor", f"singles_{name}_eff")
    eff.attached_to = crystal_name
    eff.input_digi_collection = singles.name
    eff.efficiency = 0.86481  # FIXME probably wrong, to evaluate
    eff.efficiency = 1.0
    eff.output_filename = ""  # No output

    # energy blur
    keV = gate.g4_units.keV
    MeV = gate.g4_units.MeV
    ene_blur = sim.add_actor("DigitizerBlurringActor", f"singles_{name}_eblur")
    ene_blur.output_filename = ""
    ene_blur.attached_to = crystal_name
    ene_blur.input_digi_collection = eff.name
    ene_blur.blur_attribute = "TotalEnergyDeposit"
    ene_blur.blur_method = "Linear"
    ene_blur.blur_resolution = 0.13
    ene_blur.blur_reference_value = 80 * keV
    ene_blur.blur_slope = -0.09 * 1 / MeV

    # spatial blurring
    mm = gate.g4_units.mm
    spatial_blur = sim.add_actor(
        "DigitizerSpatialBlurringActor", f"singles_{name}_sblur"
    )
    spatial_blur.output_filename = ""
    spatial_blur.attached_to = crystal_name
    spatial_blur.input_digi_collection = ene_blur.name
    spatial_blur.blur_attribute = "PostPosition"
    spatial_blur.blur_fwhm = 3.9 * mm
    spatial_blur.keep_in_solid_limits = True

    # energy windows
    singles_ene_windows = sim.add_actor(
        "DigitizerEnergyWindowsActor", f"singles_{name}_ene_windows"
    )
    channels = [
        {"name": f"spectrum_{name}", "min": 3 * keV, "max": 515 * keV},
        {"name": f"scatter1_{name}", "min": 96 * keV, "max": 104 * keV},
        {"name": f"peak113_{name}", "min": 104.52 * keV, "max": 121.48 * keV},
        {"name": f"scatter2_{name}", "min": 122.48 * keV, "max": 133.12 * keV},
        {"name": f"scatter3_{name}", "min": 176.46 * keV, "max": 191.36 * keV},
        {"name": f"peak208_{name}", "min": 192.4 * keV, "max": 223.6 * keV},
        {"name": f"scatter4_{name}", "min": 224.64 * keV, "max": 243.3 * keV},
    ]
    singles_ene_windows.attached_to = crystal_name
    singles_ene_windows.input_digi_collection = spatial_blur.name
    singles_ene_windows.channels = channels
    singles_ene_windows.output_filename = ""  # No output

    # projection
    deg = gate.g4_units.deg
    proj = sim.add_actor("DigitizerProjectionActor", f"projections_{name}")
    proj.attached_to = crystal_name
    proj.input_digi_collections = [x["name"] for x in channels]
    proj.spacing = [4.7951998710632 * mm, 4.7951998710632 * mm]
    proj.size = [128, 128]
    proj.output_filename = "proj.mhd"
    proj.origin_as_image_center = True
    # plane orientation
    proj.detector_orientation_matrix = Rotation.from_euler(
        "yx", (90, 90), degrees=True
    ).as_matrix()

    return proj


def add_intevo_two_heads(sim, name, colli_type, radius):
    """
    FIXME : to put contrib.spect.siemens_intevo
    """
    heads = []
    crystals = []
    for i in range(2):
        head, colli, crystal = intevo.add_spect_head(
            sim, f"{name}_{i}", collimator_type=colli_type, debug=sim.visu
        )
        heads.append(head)
        crystals.append(crystal)
    # this head translation is not used (only to avoid overlap warning at initialisation)
    heads[0].translation = [radius, 0, 0]
    heads[1].translation = [-radius, 0, 0]

    return heads, crystals


def rotate_gantry_helpers(
    head, radius, start_angle_deg, step_angle_deg, nb_angle, initial_rotation=None
):
    # compute the nb translation and rotation
    translations = []
    rotations = []
    current_angle_deg = start_angle_deg
    if initial_rotation is None:
        initial_rotation = Rotation.from_euler("X", 90, degrees=True)
    for r in range(nb_angle):
        print(f'Angle {r} = {current_angle_deg}')
        t, rot = gate.geometry.utility.get_transform_orbiting(
            [0, radius, 0], "Z", current_angle_deg
        )
        rot = Rotation.from_matrix(rot)
        rot = rot * initial_rotation
        rot = rot.as_matrix()
        translations.append(t)
        rotations.append(rot)
        current_angle_deg += step_angle_deg
    print(translations)

    # set the motion for the SPECT head
    head.add_dynamic_parametrisation(translation=translations, rotation=rotations)



def add_iec_phantom(sim, aa_volumes, conc_a, name_supp):
    # rotation 180 around X to be like in the iec 61217 coordinate system
    mm = gate.g4_units.mm
    iec_phantom = gate_iec.add_iec_phantom(sim, sphere_starting_angle=0)
    iec_phantom.translation = [0 * mm, 0 * mm, 0 * mm]
    iec_phantom.rotation = Rotation.from_euler("x", 0, degrees=True).as_matrix()
    iec_phantom.rotation = Rotation.from_euler("y", 180, degrees=True).as_matrix()

    # add sources for all spheres
    cm3 = gate.g4_units.cm3
    Bq = gate.g4_units.Bq
    BqmL = Bq / cm3
    mm = gate.g4_units.mm
    red = [1, 0.7, 0.7, 0.8]
    #conc_a = 713 * BqmL
    activity_Bq_mL = [0 * conc_a, 8 * conc_a, 8 * conc_a, 8 * conc_a, 8 * conc_a, 0 * conc_a ]
    sources = gate_iec.add_spheres_sources(sim, iec_phantom.name, "sources", "all", activity_Bq_mL, spheres_diam = [37, 13, 17, 22, 28, 28], verbose=True)
    for source in sources:
        set_iec_sources(source, rad = "Tc99m")
        gate.sources.utility.set_source_energy_spectrum(source, rad = "Tc99m")
        if aa_volumes is not None:
            source.direction.acceptance_angle.volumes = aa_volumes
            source.direction.acceptance_angle.intersection_flag = True
            source.direction.acceptance_angle.skip_policy = "SkipEvents"

    # support polystyrene
    #polystyrene = sim.add_volume("Box", f"{name_supp}_polystyrene")
    #polystyrene.size = [470 * mm, 20 * mm, 400 * mm]
    #polystyrene.translation = [
    #    iec_phantom.translation[0],
    #    iec_phantom.translation[1] - 80 - polystyrene.size[1] / 2,
    #    polystyrene.size[2] / 2 - 400 / 2,
    #]
    #polystyrene.material = "G4_POLYSTYRENE"
    #polystyrene.color = red
    
    return iec_phantom

def set_iec_sources(source, rad = "Tc99m"):
        source.particle = "gamma"
        gate.sources.utility.set_source_energy_spectrum(source, rad)
        #gate.sources.base.set_source_rad_energy_spectrum(source, rad)


def add_digitizer_tc99m_wip(sim, crystal_name, name, spectrum_channel=True):
    # create main chain
    mm = gate.g4_units.mm
    digitizer = Digitizer(sim, crystal_name, name)

    # Singles
    sc = digitizer.add_module("DigitizerAdderActor", f"{name}_singles")
    sc.group_volume = None
    sc.policy = "EnergyWinnerPosition"

    # detection efficiency
    # ea = digitizer.add_module("DigitizerEfficiencyActor", f"{name}_eff")
    # ea.efficiency = 0.86481  # FAKE

    # energy blurring
    keV = gate.g4_units.keV
    # (3/8” Crystal) = Intrinsic Energy Resolution (Tc-99m @ 20 kcps) UFOV FWHM ≤ 6.3%
    eb = digitizer.add_module("DigitizerBlurringActor", f"{name}_blur")
    eb.blur_attribute = "TotalEnergyDeposit"
    eb.blur_method = "InverseSquare"
    eb.blur_resolution = 0.0965  # ???
    eb.blur_reference_value = 140.57 * keV

    # spatial blurring
    sb = digitizer.add_module("DigitizerSpatialBlurringActor", f"{name}_sp_blur")
    sb.attached_to = crystal_name
    sb.blur_attribute = "PostPosition"
    sb.blur_fwhm = 7.6 * mm  # ???
    sb.keep_in_solid_limits = True

    # energy windows (Energy range. 35-588 keV)
    cc = digitizer.add_module("DigitizerEnergyWindowsActor", f"{name}_energy_window")
    channels = [
        {"name": f"spectrum", "min": 3 * keV, "max": 160 * keV},
        {"name": f"scatter", "min": 114 * keV, "max": 126 * keV},
        {"name": f"peak140", "min": 126.45 * keV, "max": 154.55 * keV},
    ]
    if not spectrum_channel:
        channels.pop(0)
    cc.channels = channels

    # projection
    proj = digitizer.add_module("DigitizerProjectionActor", f"{name}_projection")
    channel_names = [c["name"] for c in channels]
    proj.input_digi_collections = channel_names
    proj.spacing = [2.2098 * mm, 2.2098 * mm]
    proj.size = [256, 256]
    proj.write_to_disk = True

    # end
    return digitizer


def add_digitizer_iodine_wip(sim, crystal_name, name, spectrum_channel=True):
    # create main chain
    mm = gate.g4_units.mm
    digitizer = Digitizer(sim, crystal_name, name)

    # Singles
    sc = digitizer.add_module("DigitizerAdderActor", f"{name}_singles")
    sc.group_volume = None
    sc.policy = "EnergyWinnerPosition"

    # detection efficiency
    # ea = digitizer.add_module("DigitizerEfficiencyActor", f"{name}_eff")
    # ea.efficiency = 0.86481  # FAKE

    # energy blurring
    keV = gate.g4_units.keV
    # (3/8” Crystal) = Intrinsic Energy Resolution (Tc-99m @ 20 kcps) UFOV FWHM ≤ 6.3%
    eb = digitizer.add_module("DigitizerBlurringActor", f"{name}_blur")
    eb.blur_attribute = "TotalEnergyDeposit"
    eb.blur_method = "InverseSquare"
    eb.blur_resolution = 0.089  # ???
    eb.blur_reference_value = 140.57 * keV

    # spatial blurring
    sb = digitizer.add_module("DigitizerSpatialBlurringActor", f"{name}_sp_blur")
    sb.blur_attribute = "PostPosition"
    sb.blur_fwhm = 7.6 * mm  # ???
    sb.keep_in_solid_limits = True

    # energy windows (Energy range. 35-588 keV)
    cc = digitizer.add_module("DigitizerEnergyWindowsActor", f"{name}_energy_window")
    channels = [
        {"name": f"spectrum", "min": 3 * keV, "max": 800 * keV},
        {"name": f"scatter", "min": 232 * keV, "max": 291 * keV},
        {"name": f"peak364", "min": 291 * keV, "max": 436 * keV},
    ]
    if not spectrum_channel:
        channels.pop(0)
    cc.channels = channels

    # projection
    proj = digitizer.add_module("DigitizerProjectionActor", f"{name}_projection")
    channel_names = [c["name"] for c in channels]
    proj.input_digi_collections = channel_names
    proj.spacing = [1.1049 * mm, 1.1049 * mm]
    proj.size = [512, 512]
    proj.write_to_disk = True

    # end
    return digitizer
