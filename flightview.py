import argparse
import numpy as np
import pandas as pd
from scipy import interpolate
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
# from pymongo import MongoClient
import flightphase
import os
import sys
import conda

conda_file_dir = conda.__file__
conda_dir = conda_file_dir.split('lib')[0]
proj_lib = os.path.join(os.path.join(conda_dir, 'share'), 'proj')
os.environ["PROJ_LIB"] = proj_lib

from mpl_toolkits.basemap import Basemap



def fill_nan(A):
    # interpolate to fill nan values
    inds = np.arange(A.shape[0])
    good = np.where(np.isfinite(A))
    f = interpolate.interp1d(inds[good], A[good], fill_value="extrapolate")
    B = np.where(np.isfinite(A), A, f(inds))
    return B


# get script arguments
parser = argparse.ArgumentParser()

parser.add_argument("--folder", default="data/saved_csvs", dest="folder")
parser.add_argument(
    "--coll", dest="coll", required=True, help="Flights data collection name"
)
args = parser.parse_args()

folder = args.folder
COLL = args.coll

# Configuration for the database
# mongo_client = MongoClient("localhost", 27017)
# mcoll = mongo_client[DB][COLL]

plt.figure(figsize=(10, 4))

colormap = {
    "GND": "black",
    "CL": "green",
    "CR": "blue",
    "DE": "orange",
    "LVL": "purple",
    "NA": "red",
}
legend_lines = []
for lab, col in colormap.items():
    legend_lines.append(Line2D([0], [0], color=col, label=lab))

for i, file_path in enumerate(os.listdir(folder)):
    df = pd.read_csv(f"{folder}/{file_path}")
    df.drop_duplicates(subset=["ts"], inplace=True)

    times = np.array(df["ts"])
    times = times - times[0]
    lats = np.array(df["lat"])
    lons = np.array(df["lon"])

    if "alt" in df.columns:
        alts = np.array(df["alt"])
        spds = np.array(df["spd"])
        rocs = np.array(df["roc"])
    elif "H" in df.columns:
        Hs = np.array(df["H"])
        vgxs = np.array(df["vgx"])
        vgys = np.array(df["vgy"])
        vhs = np.array(df["vh"])
        alts = Hs / 0.3048
        spds = np.sqrt(vgxs ** 2 + vgys ** 2) / 0.5144
        rocs = vhs / 0.00508

    try:
        labels = flightphase.fuzzylabels(times, alts, spds, rocs)
    except:
        print(f"Could not compute fuzzy labels for file {file_path}.")
        continue

    colors = [colormap[l] for l in labels]

    # setup mercator map projection.
    # plt.suptitle("press any key to continue to next example...")

    plt.subplot(121)
    m = Basemap(
        llcrnrlon=min(lons) - 2,
        llcrnrlat=min(lats) - 2,
        urcrnrlon=max(lons) + 2,
        urcrnrlat=max(lats) + 2,
        resolution="l",
        projection="merc",
    )
    m.fillcontinents()
    # plot SIL as a fix point
    latSIL = 51.989884
    lonSIL = 4.375374
    m.plot(lonSIL, latSIL, latlon=True, marker="o", c="red", zorder=9)
    m.scatter(lons, lats, latlon=True, marker=".", c=colors, lw=0, zorder=10)

    plt.subplot(122)
    plt.scatter(times, alts, marker=".", c=colors, lw=0)
    plt.ylabel("altitude (ft)")
    plt.legend(handles=legend_lines, prop={'size': 8})

    # plt.tight_layout()
    plt.savefig(f"data/saved_figures/fig_{i}.png")
    # plt.draw()
    # plt.waitforbuttonpress(-1)
    plt.clf()

