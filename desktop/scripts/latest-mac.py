"""One latest-mac.yml for the two Macs' builds, each made on its own system (.github/workflows/desktop.yml), so each
wrote its own: the files of both under the one version, Apple silicon's first. electron-updater picks the file for
the Mac it runs on (on Apple silicon the one whose name says arm64, on an Intel Mac the other).

    python3 scripts/latest-mac.py <arm64's latest-mac.yml> <x64's latest-mac.yml> > latest-mac.yml"""
import sys


def parts(text):
    """The lines before the file list (with `files:`), the list, the lines after it."""
    lines = text.rstrip("\n").split("\n")
    i = lines.index("files:")
    j = i + 1
    while j < len(lines) and lines[j].startswith(" "):
        j += 1
    return lines[:i + 1], lines[i + 1:j], lines[j:]


def merge(arm64, x64):
    va, vb = (next(line for line in t.split("\n") if line.startswith("version:")) for t in (arm64, x64))
    if va != vb:
        raise ValueError(f"two versions: {va}, {vb}")
    head, files, tail = parts(arm64)
    other = parts(x64)[1]
    if not any("arm64" in line for line in files) or any("arm64" in line for line in other):
        raise ValueError("the first file is Apple silicon's, the second an Intel Mac's")
    return "\n".join(head + files + other + tail) + "\n"


if __name__ == "__main__":
    a, b = (open(f, encoding="utf-8").read() for f in sys.argv[1:3])
    sys.stdout.write(merge(a, b))
