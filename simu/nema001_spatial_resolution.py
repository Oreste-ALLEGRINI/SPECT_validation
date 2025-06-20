#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate.contrib.spect.ge_discovery_nm670 as nm670
from opengate import g4_units
from nema001_helpers import set_nema001_simulation, set_nema001_simulation_2sources
from opengate.contrib.spect.siemens_intevo import (
    compute_plane_position_and_distance_to_crystal,
)
from spect_helpers import *
import click

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--source_orientation", "-s", default="X", help="Orientation of the source X or Y"
)
@click.option("--fwhm_blur", default=4.6, help="FWHM spatial blur in digitizer")
@click.option(
    "--distance", "-d", default=0 * g4_units.cm, help="Distance source-detector in mm"
)
@click.option(
    "--source_config", "-c", default="1_source", help="Configuration of the source(s) : 1_source or 2_sources if you want simulate the NEMA acquisition of pixel size assessment"
)
@click.option(
    "--scatter", "-sc", default=False, help="Set PMMA plates for scattering medium (NEMA NU 1 2023)"
)
@click.option(
    "--collimator", "-col", default="lehr", help="Set the collimator type : lehr, megp, hegp or plexi"
)
@click.option(
    "--radionuclide", "-rad", default="Tc99m", help="Set the radionuclide type : Tc99m, Lu177 or other radionuclide contained in ICRP 107 database"
)

def go(source_orientation, fwhm_blur, distance, source_config, scatter, collimator, radionuclide):
    run_simulation(source_orientation, fwhm_blur, distance, source_config, scatter, collimator, radionuclide)

def run_simulation(source_orientation, fwhm_blur, distance, source_config, scatter, collimator, radionuclide):

    # folders
    simu_name = f"nema001_{source_orientation}_blur_{fwhm_blur:.2f}_d_{distance:.2f}"

    # create the simulation
    sim = gate.Simulation()

    # main options
    # sim.visu = True

    pos, crystal_distance, psd = nm670.compute_plane_position_and_distance_to_crystal(collimator)
    print("User distance =", distance)
    print("Plane position =", pos)
    print("crystal_distance =", crystal_distance)
    print("psd=", psd)
    distance = distance + pos
    print("final radius =", distance)

    # create simulation
    if source_config == "1_source":
        head, glass_tube, digit_blur = set_nema001_simulation(sim, simu_name, scatter, collimator, radionuclide)
    if source_config == "2_sources":
        head, glass_tube, glass_tube2, digit_blur = set_nema001_simulation_2sources(sim, simu_name, scatter, collimator, radionuclide)

    # orientation of the linear source
    # Mode 1 source
    if source_config == "1_source":
        if source_orientation == "X":
            glass_tube.rotation = Rotation.from_euler("Y", 90, degrees=True).as_matrix()
    # Mode 2 sources
    if source_config == "2_sources":
        if source_orientation == "X":
            glass_tube.rotation = Rotation.from_euler("Y", 90, degrees=True).as_matrix()
            glass_tube2.rotation = Rotation.from_euler("Y", 90, degrees=True).as_matrix()
            glass_tube2.translation = [ 0, 0, -100 * g4_units.mm]

    # camera distance
    nm670.rotate_gantry(head, radius=distance, start_angle_deg=0)
    print(head.translation)

    # digitizer
    digit_blur.blur_fwhm = fwhm_blur

    # go
    sim.run()

    # print
    stats = sim.actor_manager.get_actor("stats")
    print(stats)


# --------------------------------------------------------------------------
if __name__ == "__main__":
    go()