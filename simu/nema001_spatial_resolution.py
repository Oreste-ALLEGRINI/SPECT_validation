#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate.contrib.spect.ge_discovery_nm670 as nm670
from opengate import g4_units
from nema001_helpers import set_nema001_simulation
from opengate.contrib.spect.siemens_intevo import (
    compute_plane_position_and_distance_to_crystal,
)
from spect_helpers import *
import click

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--source_orientation", "-s", default="Y", help="Orientation of the source X or Y"
)
@click.option("--fwhm_blur", default=6.3, help="FWHM spatial blur in digitizer")
@click.option(
    "--distance", "-d", default=10 * g4_units.cm, help="Distance source-detector in mm"
)
def go(source_orientation, fwhm_blur, distance):

    # folders
    simu_name = f"nema001_{source_orientation}_blur_{fwhm_blur:.2f}_d_{distance:.2f}"

    # create the simulation
    sim = gate.Simulation()

    # main options
    sim.visu = False

    pos, crystal_distance, psd = compute_plane_position_and_distance_to_crystal("lehr")
    print("User distance =", distance)
    print("Plane position =", pos)
    print("crystal_distance =", crystal_distance)
    print("psd=", psd)
    distance = distance - pos
    print("final radius =", distance)

    # create simulation
    head, syringue, digit_blur = set_nema001_simulation(sim, simu_name)

    # orientation of the linear source
    if source_orientation == "X":
        syringue.rotation = Rotation.from_euler("Y", 90, degrees=True).as_matrix()

    # camera distance
    nm670.rotate_gantry(head, radius=distance, start_angle_deg=270)
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
