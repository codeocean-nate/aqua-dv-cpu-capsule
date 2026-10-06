#!/usr/bin/env python3
"""Deployment verification: CPU check.

Prints a short identity banner and machine facts, reads EVERY regular file under the data
folder (size + SHA-256, so attached data assets are proven readable, not just listed) and
writes results a verifier can read back:

  <results>/result.txt         "DV-CHECK OK <utc>" plus the counts
  <results>/data_manifest.tsv  path <TAB> bytes <TAB> sha256 for every file under <data>
  <results>/summary.json       machine facts, counts and the identity values

Standard library only, no network access. The only environment values it prints are the
four Code Ocean identity variables (CO_CAPSULE_ID, CO_COMPUTATION_ID, CO_CPUS, CO_MEMORY).

Options:
  --require-data N   exit 2 unless at least N files are found under the data folder
                     (use it in a pipeline step, or when an asset must be attached)
Folders default to /data and /results; DV_DATA_DIR and DV_RESULTS_DIR override them.
"""
import argparse
import hashlib
import json
import os
import platform
import sys
import time

IDENTITY = {"CO_CAPSULE_ID": "capsule", "CO_COMPUTATION_ID": "computation",
            "CO_CPUS": "cpus", "CO_MEMORY": "memory"}
CHUNK = 1024 * 1024


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def files_under(root):
    """Regular files under root, without following directory links (data assets can
    contain links that point back to their own folder)."""
    found = []
    if not os.path.isdir(root):
        return found
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            if os.path.isfile(path):
                found.append(path)
    return found


def sha256(path):
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as f:
        while True:
            block = f.read(CHUNK)
            if not block:
                break
            size += len(block)
            h.update(block)
    return size, h.hexdigest()


def memory_bytes():
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--require-data", type=int, default=0, metavar="N")
    args = ap.parse_args()

    data = os.environ.get("DV_DATA_DIR", "/data")
    results = os.environ.get("DV_RESULTS_DIR", "/results")
    identity = {k: os.environ.get(k, "unset") for k in IDENTITY}
    print("DV-BANNER " + " ".join(f"{IDENTITY[k]}={v}" for k, v in identity.items()), flush=True)

    facts = {
        "utc": utc(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "memory_bytes": memory_bytes(),
    }
    print("DV-MACHINE " + " ".join(f"{k}={v}" for k, v in facts.items() if k != "utc"), flush=True)

    rows, unreadable, total = [], 0, 0
    for path in files_under(data):
        try:
            size, digest = sha256(path)
        except OSError as e:
            unreadable += 1
            print(f"DV-UNREADABLE {path}: {e.__class__.__name__}", flush=True)
            continue
        total += size
        rows.append((path, size, digest))
        print(f"DV-FILE {digest}  {size}  {path}", flush=True)
    print(f"DV-DATA files={len(rows)} bytes={total} unreadable={unreadable} folder={data}", flush=True)

    os.makedirs(results, exist_ok=True)
    with open(os.path.join(results, "data_manifest.tsv"), "w") as f:
        f.write("path\tbytes\tsha256\n")
        for path, size, digest in rows:
            f.write(f"{path}\t{size}\t{digest}\n")
    summary = {"identity": identity, "machine": facts, "data_folder": data,
               "data_files": len(rows), "data_bytes": total, "unreadable": unreadable}
    with open(os.path.join(results, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")

    ok = unreadable == 0 and len(rows) >= args.require_data
    status = "OK" if ok else "FAIL"
    with open(os.path.join(results, "result.txt"), "w") as f:
        f.write(f"DV-CHECK {status} {utc()} data_files={len(rows)} data_bytes={total} unreadable={unreadable}\n")
    print(f"DV-CHECK {status} data_files={len(rows)} required={args.require_data} unreadable={unreadable}", flush=True)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
