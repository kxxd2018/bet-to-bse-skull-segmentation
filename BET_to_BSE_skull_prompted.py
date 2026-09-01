import os
import re
from pathlib import Path

os.environ["NIPYPE_NO_ET"] = "1"

from nipype import config
from nipype.interfaces import brainsuite, fsl
import nipype.pipeline.engine as pe

config.enable_debug_mode()


def windows_or_linux_path(value: str) -> str:
    """Accept a Linux/WSL path or a Windows drive path and return a WSL path."""
    value = value.strip().strip('"').strip("'")

    if not value:
        raise ValueError("A path is required.")

    # Converts examples such as D:\Research\scan.nii.gz or D:/Research/scan.nii.gz
    # into /mnt/d/Research/scan.nii.gz.
    match = re.match(r"([A-Za-z]):[\\/](.*)", value)

    if match:
        drive, remainder = match.groups()
        return f"/mnt/{drive.lower()}/" + remainder.replace("\\", "/")

    # Keep Linux/WSL paths usable and normalize accidental backslashes.
    return value.replace("\\", "/")


def ask_existing_file(prompt: str) -> str:
    while True:
        try:
            file_path = Path(windows_or_linux_path(input(prompt)))
        except ValueError as exc:
            print(f"{exc} Try again.")
            continue

        if file_path.is_file():
            return str(file_path.resolve())

        print(f"File not found: {file_path}")
        print("Paste a full Linux/WSL path or Windows path, for example:")
        print("  /mnt/d/Research/subject/scan.nii.gz")
        print(r"  D:\Research\subject\scan.nii.gz")
        print()


def ask_output_directory(prompt: str) -> str:
    while True:
        try:
            output_dir = Path(windows_or_linux_path(input(prompt)))
        except ValueError as exc:
            print(f"{exc} Try again.")
            continue

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            if not output_dir.is_dir():
                raise OSError("The path is not a directory.")
            return str(output_dir.resolve())
        except OSError as exc:
            print(f"Cannot create or use output directory {output_dir}: {exc}")
            print()


def ask_integer(prompt: str, default: int) -> int:
    while True:
        answer = input(
            f"{prompt} Press Enter to accept the default [{default}]: "
        ).strip()

        if answer == "":
            return default

        try:
            value = int(answer)
        except ValueError:
            print("Enter a whole number or press Enter to accept the default.")
            print()
            continue

        if 0 <= value <= 255:
            return value

        print("Enter a number from 0 to 255.")
        print()


def ask_prefix(default: str) -> str:
    # If the original input filename is already a valid surface prefix,
    # use it automatically and do not ask the user.
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", default):
        return default

    # Only ask the user when the original filename contains invalid characters.
    print(
        f'The original input filename prefix "{default}" contains characters '
        "that cannot be used in a BrainSuite surface filename."
    )
    print(
        "Use only letters, numbers, dots, underscores, or hyphens. "
        "Do not include spaces, slashes, backslashes, or a folder path."
    )
    print()

    while True:
        prefix = input("Enter a surface file prefix: ").strip()

        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", prefix):
            return prefix

        print(
            "Invalid prefix. Use letters, numbers, dots, underscores, "
            "or hyphens; do not include a path."
        )
        print()


print("\nMRI Skull Segmentation")
print("- FSL BET mask to BrainSuite Skullfinder workflow")
print("- Operable within Window's WSL (Linux)")
print("- Both FSL and Brainsuite must be installed within Window's WSL environment")
print("You can paste either Linux/WSL paths (/mnt/d/...) or Windows paths (D:\\...).")
print()

# -------------------------------------------------------------------
# Ask for files and settings
# -------------------------------------------------------------------

t1_file = ask_existing_file("Input T1 MRI file (.nii or .nii.gz): ")
print()

bse_reference = ask_existing_file(
    "Existing reference BSE mask for BET mask transformation: "
)
print()

final_dir = ask_output_directory("Final output folder: ")
print()

skull_threshold = ask_integer(
    "Lower threshold (Skull threshold), 1-255",
    53,
)

scalp_threshold = ask_integer(
    "Upper threshold (Scalp threshold), 1-255",
    116,
)

if skull_threshold > scalp_threshold:
    raise ValueError(
        "Lower (Skull) threshold must be less than or equal to "
        "Upper (Scalp) threshold."
    )

# -------------------------------------------------------------------
# Find the BrainSuite bin directory.
# Use /lib/BrainSuite23a/bin automatically if it is valid.
# If it fails, allow a Linux/WSL or Windows-style path as input.
# -------------------------------------------------------------------

DEFAULT_BRAINSUITE_BIN = Path("/opt/BrainSuite23a/bin")
DEFAULT_SKULLFINDER = DEFAULT_BRAINSUITE_BIN / "skullfinder.exe"

if os.name == "nt":
    BRAINSUITE_EXECUTABLE = "skullfinder.exe"
else:
    BRAINSUITE_EXECUTABLE = "skullfinder"

if DEFAULT_BRAINSUITE_BIN.is_dir() and DEFAULT_SKULLFINDER.is_file():
    BRAINSUITE_BIN = DEFAULT_BRAINSUITE_BIN.resolve()

    print(f"Using default BrainSuite bin directory: {BRAINSUITE_BIN}")
    print()

else:
    print(
        "The default BrainSuite bin directory could not be used:\n"
        f"  {DEFAULT_BRAINSUITE_BIN}"
    )
    print(
        "Enter the BrainSuite bin folder. You may paste either a "
        "Linux/WSL path or a Windows path."
    )
    print("Examples:")
    print("  /opt/BrainSuite23a/bin")
    print(r"  D:\Apps\BrainSuite23a\bin")
    print()

    while True:
        try:
            entered_path = input("BrainSuite bin folder: ")
            linux_path = windows_or_linux_path(entered_path)
            BRAINSUITE_BIN = Path(linux_path)

        except ValueError as exc:
            print(f"{exc} Try again.")
            print()
            continue

        skullfinder_executable = BRAINSUITE_BIN / "skullfinder"

        if BRAINSUITE_BIN.is_dir() and skullfinder_executable.is_file():
            BRAINSUITE_BIN = BRAINSUITE_BIN.resolve()

            print(
                f"Using entered BrainSuite bin directory: "
                f"{BRAINSUITE_BIN}"
            )
            print()
            break

        print(f"Invalid BrainSuite bin folder: {BRAINSUITE_BIN}")
        print(
            "The selected folder must contain the executable named "
            "`skullfinder`."
        )
        print()

# Add the validated Linux/WSL BrainSuite bin directory to PATH.
os.environ["PATH"] = (
    f"{BRAINSUITE_BIN}{os.pathsep}{os.environ.get('PATH', '')}"
)

print(f"BrainSuite bin directory: {BRAINSUITE_BIN}")
print(f"Skullfinder executable: {BRAINSUITE_BIN / 'skullfinder'}")
print()

# -------------------------------------------------------------------
# Derive output prefix from the T1 filename
# -------------------------------------------------------------------

input_stem = Path(t1_file).name

if input_stem.endswith(".nii.gz"):
    input_stem = input_stem[:-7]
elif input_stem.endswith(".nii"):
    input_stem = input_stem[:-4]

surface_prefix = ask_prefix(input_stem)

workflow_dir = os.path.join(final_dir, "nipype_work")
surface_output_prefix = os.path.join(final_dir, surface_prefix)

# -------------------------------------------------------------------
# Find FLIRT identity matrix
# -------------------------------------------------------------------

fsl_dir = os.environ.get("FSLDIR", "")

if fsl_dir:
    default_identity_matrix = (
        Path(fsl_dir) / "etc" / "flirtsch" / "ident.mat"
    )
else:
    default_identity_matrix = (
        Path.home() / "fsl" / "etc" / "flirtsch" / "ident.mat"
    )

if default_identity_matrix.is_file():
    identity_matrix = str(default_identity_matrix.resolve())
    print(f"Using FSL identity matrix: {identity_matrix}")
    print()
else:
    print("FSL identity matrix was not found automatically.")
    print()

    identity_matrix = ask_existing_file(
        "Enter the path to an identity matrix (.mat) file: "
    )
    print()

# -------------------------------------------------------------------
# Nipype workflow
# -------------------------------------------------------------------

wf = pe.Workflow(
    name="bet_to_bse_skull",
    base_dir=workflow_dir,
)

# BET creates a binary brain mask.
bet = pe.Node(
    fsl.BET(
        in_file=t1_file,
        mask=True,
        frac=0.5,
        robust=True,
    ),
    name="bet",
)

# FLIRT resamples the BET mask to the BSE reference geometry.
applyxfm = pe.Node(
    fsl.FLIRT(
        apply_xfm=True,
        interp="nearestneighbour",
        in_matrix_file=identity_matrix,
        reference=bse_reference,
    ),
    name="applyxfm",
)

# Skullfinder generates the label image and BrainSuite surfaces.
skullfinder = pe.Node(
    brainsuite.Skullfinder(
        inputMRIFile=t1_file,
        lowerThreshold=skull_threshold,
        upperThreshold=scalp_threshold,
        surfaceFilePrefix=surface_output_prefix,
    ),
    name="skullfinder",
)

wf.connect(bet, "mask_file", applyxfm, "in_file")
wf.connect(applyxfm, "out_file", skullfinder, "inputMaskFile")

if __name__ == "__main__":

    wf.run()
    print("Settings")
    print(f"  T1 MRI:          {t1_file}")
    print(f"  BSE reference:   {bse_reference}")
    print(f"  Final folder:    {final_dir}")
    print(f"  Skull threshold: {skull_threshold}  (Skullfinder -l)")
    print(f"  Scalp threshold: {scalp_threshold}  (Skullfinder -u)")
    print(f"  Surface prefix:  {surface_output_prefix}")
    print(f"  Work directory:  {workflow_dir}")
    print()
    print("Workflow finished.")
