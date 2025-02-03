import uproot as root
import matplotlib.pyplot as plt
import pandas as pd
import csv

path = "/media/DATA/NEMA_SPECT/Gate_module/spect_validation_oreste/simu/energy_resolution/nema001_Hits_blur_4.60_d_100.00Al0.13/"
myFile = root.open(path+"nema001_Y_blur_4.60_d_100.00_energy.root")

# Accéder au TTree (remplacez "nom_du_ttree" par le nom du TTree dans le fichier)
tree = myFile["digitizer_blur;1"]

# Lire des branches spécifiques
data = tree.arrays(["TotalEnergyDeposit"], library="pd")

# Sauvegarder les données dans un fichier CSV
data.to_csv(path+"output_energy.csv", index=False)

# Exemple : tracer un histogramme
counts, bin_edges, _ = plt.hist(data["TotalEnergyDeposit"], bins=160, histtype="step", label="Données")
plt.xlabel("Energy (MeV)")
plt.ylabel("Counts")
plt.legend()
plt.show()

with open(path+"histogram_data.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Bin_Start", "Bin_End", "Count"])  # En-têtes du fichier CSV
    for start, end, count in zip(bin_edges[:-1], bin_edges[1:], counts):
        writer.writerow([start, end, count])