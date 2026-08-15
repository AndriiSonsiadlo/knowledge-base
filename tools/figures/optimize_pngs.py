"""Shrink the generated figures for the web.

matplotlib writes 24-bit RGB PNGs, but these figures are flat-colour plots with
a small palette — quantising to 256 adaptive colours typically cuts file size by
60-80 % with no visible difference at the size they're displayed.

The check below is conservative: a file is only replaced when the quantised
version is *both* smaller and close to the original pixel-for-pixel, so a
gradient-heavy heatmap that genuinely needs more colours is left alone.

    python optimize_pngs.py            # optimise static/img/ml
    python optimize_pngs.py --check    # report only, change nothing
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2] / "static" / "img" / "ml"

# Mean absolute per-channel error, 0-255. Above this the quantised version is
# rejected as visibly degraded.
MAX_MEAN_ERROR = 2.0


def optimise(path: pathlib.Path, dry_run: bool = False):
    before = path.stat().st_size
    original = Image.open(path).convert("RGB")

    quant = original.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    restored = quant.convert("RGB")

    err = float(np.abs(np.asarray(original, dtype=np.int16)
                       - np.asarray(restored, dtype=np.int16)).mean())

    tmp = path.with_suffix(".opt.png")
    quant.save(tmp, optimize=True)
    after = tmp.stat().st_size

    if err > MAX_MEAN_ERROR or after >= before:
        tmp.unlink()
        return before, before, err, False

    if dry_run:
        tmp.unlink()
    else:
        tmp.replace(path)
    return before, after, err, True


def main():
    dry = "--check" in sys.argv
    files = sorted(ROOT.rglob("*.png"))
    total_before = total_after = 0
    skipped = []
    for p in files:
        before, after, err, changed = optimise(p, dry_run=dry)
        total_before += before
        total_after += after
        if not changed:
            skipped.append((p.relative_to(ROOT), err))

    print(f"{len(files)} files: {total_before/1e6:.1f} MB → {total_after/1e6:.1f} MB "
          f"({100 * (1 - total_after / total_before):.0f} % smaller)"
          + ("  [check only, nothing written]" if dry else ""))
    if skipped:
        print(f"left untouched ({len(skipped)}, too much colour detail):")
        for name, err in skipped:
            print(f"  {name}  (mean error {err:.2f})")


if __name__ == "__main__":
    main()
