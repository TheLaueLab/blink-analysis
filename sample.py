#!/usr/bin/env python3
from itertools import chain
from functools import partial
from numpy import amax, amin, concatenate
from random import sample, seed

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
    parser.add_argument("--threshold", type=float, default=2.0,
                        help="The fold-increase over background necessary for a spot to be on.")
    parser.add_argument("--ntraces", type=int, default=5,
                        help="The number of (randomly chosen) traces to display.")
    parser.add_argument("--output", type=str, required=False,
                        help="The base name for saving data.")
    parser.add_argument("--seed", type=int, default=4,
                        help="The seed for random processed (e.g. selecting sample traces)")

    args = parser.parse_args()

    seed(args.seed)

    if args.output is not None:
        matplotlib.use('agg')
    # Must be imported after backend is set
    import matplotlib.pyplot as plt

    rois = []
    for roi_path in args.rois:
        with roi_path.open("rb") as f:
            rois.extend(loadAll(f))
    traces = list(map(partial(amax, axis=(1, 2)), rois))

    fig = plt.figure(figsize=(8, 12))
    sample_idxs = list(sample(range(len(rois)), args.ntraces))
    sample_rois  = list(map(rois.__getitem__, sample_idxs))
    sample_traces = list(map(traces.__getitem__, sample_idxs))
    vmin = min(map(amin, sample_traces))
    vmax = max(map(amax, sample_traces))
    plt_indices = range(1, len(sample_idxs) * 2, 2)
    for i, roi, trace in zip(plt_indices, sample_rois, sample_traces):
        on = trace > args.threshold

        cmap = ListedColormap(['r', 'b'])
        norm = BoundaryNorm([-float('inf'), 0.5, float('inf')], cmap.N)

        lc = LineCollection(makeSegments(trace), cmap=cmap, norm=norm)
        lc.set_array(on)

        ax = fig.add_subplot(plt_indices.stop, 1, i)
        ax.set_ylabel("max. intensity")
        ax.set_xlabel("frame")
        ax.add_collection(lc)
        ax.set_xlim(0, len(trace))
        ax.set_ylim(vmin, vmax)
        ax.axhline(y=args.threshold)

        ax = fig.add_subplot(plt_indices.stop, 1, i+1)
        rowsize = 409 # Factors 8998
        show = concatenate([concatenate(roi[i:i+rowsize], axis=-1)
                            for i in range(0, len(roi), rowsize)], axis=-2)
        ax.imshow(show, vmax=vmax, vmin=vmin,
                  cmap=get_cmap('gray'), interpolation="nearest")
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])

    if args.output is not None:
        fig.tight_layout()
        fig.savefig("{}_traces.png".format(args.output))
    else:
        plt.show()