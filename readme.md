
# test001_no_phantom

One head SPECT, static, one single projection. 
No phantom, two spherical sources in air, mono energetic gammas, 
with acceptance angle (gamma only emitted towards the SPECT head).

About 5 sec computation time with 2 threads, PPS = 366,444


# test002_iec_phantom

Like test001 but with IEC phantom (6 spheres). 
Gamma source with 177Lu energy spectra.

About 30 sec computation time with 4 threads, PPS = 283,350


# test003_iec_phantom_rotation

Like test002 but 2 heads and with complete rotation : 60 (angles) x 2 (heads) projections. 
Multithread work but not very efficient when the activity is low. 

About 5 min computation time with 1 thread, PPS = 89,022
About 4 min computation time with 4 thread, PPS = 100,737

Use the script test003_process_image to extract all projections of a given energy window. 

# reconstruction 

FIXME : RTK reconstruction

rtksimulatedgeometry -o geom_120.xml -f 0 -n 120 -a 360 --sdd 0 --sid 400

rtkosem -g geom_120.xml -o test_recon_p0.mhd --path . --regexp test_projections_0.mhd --spacing 5 --dimension 128 --niterations 2 -v --nprojpersubset 10

rtkosem -v -g geom_120.xml -o recon_i3s10_zeng.mhd --niterations 3 --nprojpersubset 10 --path . --regexp proj_2.mhd --like ../../data/five_aligned_sources.mhd -f Zeng -b Zeng --sigmazero 0.9 --alphapsf 0.025