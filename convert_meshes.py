#!/usr/bin/env python3
"""
Convert all .obj Wavefront meshes in Asset/meshes/ into Qt Quick 3D binary .mesh files
using the Qt balsam tool.
"""

import os
import sys
import glob
import shutil
import tempfile
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MESHES_DIR = os.path.join(SCRIPT_DIR, "meshes")

def find_balsam():
    candidates = [
        "balsam-qt6",
        "/usr/bin/balsam-qt6",
        "/usr/lib64/qt6/bin/balsam",
        "balsam",
        "/usr/bin/balsam",
    ]
    for c in candidates:
        path = shutil.which(c)
        if path:
            return path
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None

def main():
    balsam_bin = find_balsam()
    if not balsam_bin:
        print("Error: Could not find balsam tool (balsam-qt6 or balsam).", file=sys.stderr)
        sys.exit(1)

    print(f"Using Balsam binary: {balsam_bin}")
    print(f"Source meshes directory: {MESHES_DIR}")

    obj_files = sorted(glob.glob(os.path.join(MESHES_DIR, "*.obj")))
    if not obj_files:
        print(f"No .obj files found in {MESHES_DIR}!")
        sys.exit(0)

    print(f"Found {len(obj_files)} .obj files to convert.")

    temp_root = tempfile.mkdtemp(prefix="balsam_conv_")
    success_count = 0
    failed = []

    try:
        for idx, obj_path in enumerate(obj_files, 1):
            base_name = os.path.splitext(os.path.basename(obj_path))[0]
            target_mesh_path = os.path.join(MESHES_DIR, f"{base_name}.mesh")

            out_sub = os.path.join(temp_root, base_name)
            os.makedirs(out_sub, exist_ok=True)

            cmd = [balsam_bin, "-platform", "offscreen", obj_path, "-o", out_sub]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode != 0:
                print(f"[{idx}/{len(obj_files)}] Failed: {base_name} (Code {result.returncode})")
                failed.append((base_name, result.stderr.decode("utf-8", errors="ignore")))
                continue

            generated_meshes = glob.glob(os.path.join(out_sub, "meshes", "*.mesh"))
            if not generated_meshes:
                print(f"[{idx}/{len(obj_files)}] Warning: No .mesh generated for {base_name}")
                failed.append((base_name, "No .mesh file generated"))
                continue

            # Copy the primary mesh to target_mesh_path
            shutil.copy2(generated_meshes[0], target_mesh_path)
            success_count += 1
            if idx % 20 == 0 or idx == len(obj_files):
                print(f"[{idx}/{len(obj_files)}] Converted: {base_name} -> {os.path.basename(target_mesh_path)}")

    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    print(f"\nConversion complete: {success_count}/{len(obj_files)} successfully converted.")
    if failed:
        print(f"Failed conversions ({len(failed)}):")
        for name, err in failed:
            print(f"  - {name}: {err[:100]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
