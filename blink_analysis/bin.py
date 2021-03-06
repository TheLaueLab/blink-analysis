#!/usr/bin/env python3
def iterBin(data, width, pool=None):
    from functools import partial
    from itertools import tee, islice, count
    from numpy import stack, sum as asum

    slices = tee(data, width)
    slices = map(lambda data, start: islice(data, start, None, width), slices, count())
    slices = map(stack, zip(*slices))

    func = partial(asum, axis=0, dtype='uint32')
    return map(func, slices) if pool is None else pool.imap(func, slices)

def tiffChain(series):
    from tifffile.tifffile import TiffPageSeries
    from itertools import chain

    # TODO: Deal with large, single files as generated by this program
    # Not an immediate issue as output is uncompressed and therefore memmap'd
    # Remember to update in project.py too
    return chain.from_iterable(map(TiffPageSeries.asarray, series))

def main(args=None):
    from sys import argv
    from argparse import ArgumentParser
    from tifffile import TiffFile, TiffWriter
    from contextlib import ExitStack
    from itertools import chain
    from functools import partial
    from pathlib import Path

    import yaml

    parser = ArgumentParser(description="Bin adjacent frames of a TIF video.")
    parser.add_argument("tifs", nargs='+', type=partial(TiffFile, multifile=False))
    parser.add_argument("-n", type=int, required=True)
    parser.add_argument("outfile", type=partial(TiffWriter, bigtiff=True))
    parser.add_argument("--metadata", nargs=2, type=Path,
                        help="Input and output metadata files (exposure updated)")
    args = parser.parse_args(argv[1:] if args is None else args)

    with args.metadata[0].open("r") as infile:
        metadata = yaml.load(infile)
    metadata["binning"] = args.n

    with args.metadata[1].open("w") as outfile:
        yaml.dump(metadata, outfile, default_flow_style=False)

    with ExitStack() as stack, args.outfile as outfile:
        for tif in args.tifs: stack.enter_context(tif)
        frames = tiffChain(chain.from_iterable(tif.series for tif in args.tifs))
        for frame in iterBin(frames, args.n):
            outfile.save(frame)

if __name__ == "__main__":
    main()
