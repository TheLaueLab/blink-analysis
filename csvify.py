#!/usr/bin/env python3
from itertools import chain
from functools import partial
from numpy import mean, clip, zeros
from pickle import load
import csv

stat_names = ["frame_photons", "blink_photons", "total_photons",
              "blink_times", "total_times", "total_blinks"]
coords = ("y", "x")

def loadAll(f):
    while True:
        try:
            yield load(f)
        except EOFError:
            return

if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path

    parser = ArgumentParser(description="Convert stat .pickle files to CSV")
    parser.add_argument("peakfile", type=Path, help="The location of peaks to process")
    parser.add_argument("statfile", type=Path, help="The pickled stats to process")
    parser.add_argument("outfile", type=Path, help="The file to write stats to")

    args = parser.parse_args()
    with args.statfile.open("rb") as f:
        stats = load(f)
    with args.peakfile.open("rb") as f:
        peaks = load(f)

    with args.outfile.open("w") as f:
        writer = csv.writer(f)
        headers = chain(coords[::-1], stats.keys())
        writer.writerow(chain(coords[::-1], stats.keys()))
        for peak, peak_stats in zip(peaks[:, ::-1], zip(*stats.values())):
            writer.writerow(chain(peak, peak_stats))