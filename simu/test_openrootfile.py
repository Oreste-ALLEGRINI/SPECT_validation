import uproot as root
import matplotlib.pyplot as plt

myFile = root.open("/media/DATA/NEMA_SPECT/Gate_module/spect_validation_oreste/simu/energy_resolution/nema001_Y_blur_6.30_d_100.00/test019_hits.root")

# Accéder au TTree (remplacez "nom_du_ttree" par le nom du TTree dans le fichier)
tree = myFile["PhaseSpace;1"]

# Lire des branches spécifiques
data = tree.arrays(["KineticEnergy"], library="np")

# Exemple : tracer un histogramme
plt.hist(data["KineticEnergy"], bins=50, histtype="step", label="Données")
plt.xlabel("Energy (MeV)")
plt.ylabel("Counts")
plt.legend()
plt.show()