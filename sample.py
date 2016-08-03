#!/usr/bin/env python3
from itertools import chain
from functools import partial
from numpy import amax, amin, mean, concatenate, pad
from random import sample, seed
from fret_analysis import calculateThreshold

def loadAll(f):
    from pickle import load

    while True:
        try:
            yield load(f)
        except EOFError:
            break

def makeSegments(y, x=None):
    from numpy import arange, concatenate, array

    if x is None:
        x = arange(len(y))
    points = array([x, y]).T.reshape(-1, 1, 2)
    return concatenate([points[:-1], points[1:]], axis=1)

if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path

    import matplotlib
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.collections import LineCollection
    from matplotlib.cm import get_cmap

    parser = ArgumentParser(description="Analyze single-particle traces.")
    parser.add_argument("rois", nargs='+', type=Path,
                        help="The pickled ROIs to process")
    parser.add_argument("--ntraces", type=int, default=5,
                        help="The number of (randomly chosen) traces to display.")
    parser.add_argument("--output", type=str, required=False,
                        help="The base name for saving data.")
    parser.add_argument("--seed", type=int, default=4,
                        help="The seed for random processed (e.g. selecting sample traces)")
    parser.add_argument("--bin", type=int, default=1,
                        help="Number of frames to bin.")

    args = parser.parse_args()

    seed(args.seed)

    if args.output is not None:
        matplotlib.use('agg')
    # Must be imported after backend is set
    import matplotlib.pyplot as plt

    rois = []
    for roi_path in args.rois:
        with roi_path.open("rb") as f:
            for roi in loadAll(f):
                end = len(roi) // args.bin * args.bin
                roi = sum(map(lambda start: roi[start:end:args.bin], range(args.bin)))
                rois.append(roi)
    traces = list(map(partial(mean, axis=(1, 2)), rois))

    fig = plt.figure(figsize=(8, 12))
    sample_idxs = list(sample(range(len(rois)), args.ntraces))
    sample_rois  = list(map(rois.__getitem__, sample_idxs))
    sample_traces = list(map(traces.__getitem__, sample_idxs))
    roi_vmin = min(map(amin, sample_rois))
    roi_vmax = max(map(amax, sample_rois))
    trace_vmin = min(map(amin, sample_traces))
    trace_vmax = max(map(amax, sample_traces))
    plt_indices = range(1, len(sample_idxs) * 2, 2)
    for i, roi, trace in zip(plt_indices, sample_rois, sample_traces):
        threshold = calculateThreshold(trace)
        on = trace > threshold

        cmap = ListedColormap(['r', 'b'])
        norm = BoundaryNorm([-float('inf'), 0.5, float('inf')], cmap.N)

        lc = LineCollection(makeSegments(trace), cmap=cmap, norm=norm)
        lc.set_array(on)

        ax = fig.add_subplot(plt_indices.stop, 1, i)
        ax.set_ylabel("max. intensity")
        ax.set_xlabel("frame")
        ax.add_collection(lc)
        ax.set_xlim(-0.01 * len(trace), len(trace) * 1.01)
        ax.set_ylim(trace_vmin, trace_vmax)
        ax.axhline(y=threshold)

        ax = fig.add_subplot(plt_indices.stop, 1, i+1)
        rowsize = 400
        framesize = roi[0].shape
        rows = [concatenate(roi[i:i+rowsize], axis=1)
                for i in range(0, len(roi), rowsize)]
        show = concatenate([pad(row, [(0, 0), (0, framesize[1] * rowsize - row.shape[1])],
                                mode='constant', constant_values=0) for row in rows])
        ax.imshow(show, vmax=roi_vmax, vmin=roi_vmin,
                  cmap=get_cmap('gray'), interpolation="nearest")
        ax.set_ylim(show.shape[0] + 2, -7)
        ax.set_xlim(-4, show.shape[1] + 4)
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])

    if args.output is not None:
        fig.tight_layout()
        fig.savefig("{}_traces.png".format(args.output))
    else:
        fig.tight_layout()
        plt.show()
