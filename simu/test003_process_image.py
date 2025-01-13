#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import itk
import numpy as np

if __name__ == "__main__":
    # folders
    output_folder = Path("output")
    simu_name = "test003"

    # image
    nb_heads = 2
    images = []
    for i in range(nb_heads):
        img_filename = output_folder / f"{simu_name}_projection_{i}.mhd"
        # read itk image
        img = itk.imread(img_filename)
        img_array = itk.GetArrayFromImage(img)
        images.append(img_array)

    # get number of energy windows and nb of projections
    im = images[0]
    print(f'Images shape: {im.shape}')
    nb_ene_win = 7
    nb_projections = int(im.shape[0] / nb_ene_win)
    print(f'{nb_ene_win=}')
    print(f'{nb_projections=}')

    # build a 3D images with all angles and only one energy window
    w = 2  # 2 is peak 113

    # create an empty 3D image
    img_3d = np.zeros((nb_projections * nb_heads, im.shape[1], im.shape[2]))
    print(f'Images shape: {img_3d.shape}')

    # fill the 3D image with the projections
    p = 0
    for i in range(nb_heads):
        im = images[i]
        for j in range(nb_projections):
            img_3d[p] = im[j * nb_ene_win]
            p += 1

    # write final image
    output_filename = output_folder / f"{simu_name}_3d_image.mhd"
    img_3d_itk = itk.GetImageFromArray(img_3d)
    itk.imwrite(img_3d_itk, output_filename)
    print(f'Output image written to {output_filename}')