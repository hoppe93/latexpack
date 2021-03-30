#!/usr/bin/env python3

import argparse
import pathlib
import shutil
import sys
import time

import parse


def pack(root, output, copybbl):
    """
    Pack the LaTeX document with root document 'root' into the
    directory 'output'.
    """
    root     = pathlib.Path(root).absolute().resolve()
    rootdir  = pathlib.Path(root).parent.absolute().resolve()
    output   = pathlib.Path(output).absolute().resolve()

    bbl      = rootdir / (root.stem + '.bbl')

    if not root.is_file():
        raise Exception("The specified root file '{}' is not a file.".format(str(root)))

    if not output.is_dir():
        output.mkdir(parents=True)

    parse.process_file(str(root), output=output, fig=1, subfig=0)

    # Copy bibliography
    if copybbl:
        if bbl.is_file():
            shutil.copy(str(bbl), output / bbl.name)
            print("Copied bibliography file '{}'.".format(bbl.name))


def main():
    parser = argparse.ArgumentParser(description="A tool for generating a clean, uncommented LaTeX document.")

    # Default packaging directory
    defaultpack = './pack{}'.format(time.strftime('%y%m%d'))

    parser.add_argument('root', help='Path to root document', nargs=1)
    parser.add_argument('--exclude-bbl', help="Exclude the compiled bibliography file", type=bool)
    parser.add_argument('--output', default=defaultpack, help="Directory under which the packed output should be stored")

    args = parser.parse_args()

    start = time.time()

    pack(root=args.root[0], output=args.output, copybbl=not args.exclude_bbl)

    stop = time.time()

    print('\nDONE in {:.3f}s'.format(stop-start))

    return 0


if __name__ == '__main__':
    sys.exit(main())


