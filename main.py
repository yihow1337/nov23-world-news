#!/usr/bin/env python3
"""make.fun entry: news-image-20261123.

Writes the day's news image to $MAKEFUN_OUTPUT_DIR/entry.png (default
/output/entry.png). Standard library only; the picture ships in the
repository and tools/render.py is what drew it.
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "entry.png"
CHUNK = 1 << 18


def main():
    src = os.path.join(HERE, NAME)
    if not os.path.isfile(src):
        raise SystemExit("missing image: %s" % src)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, NAME)
    tmp = dst + ".part"
    # Write to a temporary file first, then rename, so a half-written file
    # never shows up as the entry.
    with open(src, "rb") as fin, open(tmp, "wb") as fout:
        while True:
            block = fin.read(CHUNK)
            if not block:
                break
            fout.write(block)
    os.replace(tmp, dst)


if __name__ == "__main__":
    main()
