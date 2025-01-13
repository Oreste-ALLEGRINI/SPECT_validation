#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import opengate
import SimpleITK as sitk
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
import click

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--source_orientation", "-s", default="Y", help="Orientation of the source X or Y"
)
@click.option("--fwhm_blur", default=6.3, help="FWHM spatial blur in digitizer")
@click.option(
    "--distance",
    "-d",
    default=10 * opengate.g4_units.cm,
    help="Distance source-detector",
)
def go(source_orientation, fwhm_blur, distance):

    ref = Path("references")

    # read the reference image
    ref_img = sitk.ReadImage(ref / f"{source_orientation.lower()}_10cm.mhd")
    ref_img_array = sitk.GetArrayFromImage(ref_img)
    print(f"Ref image = {ref_img_array.shape}")
    s = ref_img.GetSpacing()[1]
    # 4 slices : 2 x heads and 2 x energy windows
    # get the first slice = first head and peak
    ref_img_array = ref_img_array[0]
    print(f"Ref image = {ref_img_array.shape}")
    total = ref_img_array.sum()

    # dump img
    img = sitk.GetImageFromArray(ref_img_array)
    img.SetSpacing([s, s, 1])
    img.SetOrigin([0, 0, 0])
    sitk.WriteImage(img, ref / f"{source_orientation.lower()}_10cm_peak.mhd")

    # read the simulated image
    simu_name = f"nema001_{source_orientation}_blur_{fwhm_blur:.2f}_d_{distance:.2f}"
    f = Path("output") / simu_name
    img = sitk.ReadImage(f / f"{simu_name}_projection.mhd")
    img_array = sitk.GetArrayFromImage(img)
    print(f"Simu image = {img_array.shape}")
    # get the peak energy window
    img_array = img_array[1]
    print(f"Simu image = {img_array.shape}")
    # scaling
    scaling = total / img_array.sum()
    print(f"Scaling factor: {scaling}")
    img_array = img_array * scaling

    # dump img
    img = sitk.GetImageFromArray(img_array)
    img.SetSpacing([s, s, 1])
    img.SetOrigin([0, 0, 0])
    sitk.WriteImage(img, f / f"{simu_name}_projection_peak.mhd")

    # prepare plot
    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(15, 5))

    # get the central pixel profile
    a = 256 - 60
    b = 256 + 60
    x = np.arange(start=a, stop=b) * s
    w = 2
    c = 256
    if source_orientation == "Y":
        y = np.sum(ref_img_array[c - w : c + w, a:b], axis=0)
        ax.plot(x, y, label="ref")
        y = np.sum(img_array[c - w : c + w, a:b], axis=0)
        ax.plot(x, y, label="simu")
    if source_orientation == "X":
        y = np.sum(ref_img_array[a:b, c - w : c + w], axis=1)
        ax.plot(x, y, label="ref")
        y = np.sum(img_array[a:b, c - w : c + w], axis=1)
        ax.plot(x, y, label="simu")

    plt.legend()
    plt.show()


# --------------------------------------------------------------------------
if __name__ == "__main__":
    go()
