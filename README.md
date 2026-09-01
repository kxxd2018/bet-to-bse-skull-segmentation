# BET-to-BSE Skull Segmentation Pipeline

A Nipype-orchestrated MRI pipeline that combines FSL's Brain Extraction Tool (BET) with BrainSuite's Skullfinder to perform whole-skull segmentation from T1-weighted MRI scans. Built as part of ongoing research into MRI-based skull segmentation, with an eye toward future forensic and archaeological applications.

## What it does

1. Runs **FSL BET** on a T1-weighted MRI to generate a binary brain mask.
2. Uses **FSL FLIRT** to resample the BET brain mask into the geometry of an existing BrainSuite BSE reference mask (nearest-neighbour interpolation, identity transform).
3. Feeds the registered mask and the original T1 into **BrainSuite Skullfinder** to generate inner/outer skull and scalp surface meshes, using configurable skull/scalp intensity thresholds.
4. Runs cross-platform in a WSL/Linux environment, and accepts either Linux/WSL (`/mnt/d/...`) or Windows-style (`D:\...`) paths interactively at the command line.

## Why a hybrid BET + Skullfinder approach

Using BrainSuite's own BSE for brain extraction can under- or over-estimate the brain boundary in some regions, which then propagates into the skull/scalp surfaces Skullfinder generates. This pipeline substitutes **FSL BET's** brain mask (with its own tunable fractional-intensity and vertical-gradient parameters) as the geometric input driving Skullfinder's segmentation, in an effort to reduce known failure modes such as incomplete temporal-bone or orbital coverage.

## Requirements

- Ubuntu or WSL (Windows Subsystem for Linux)
- Python 3.8+
- [FSL](https://fsl.fmrib.ox.ac.uk/) (tested with FSL 6.x)
- [BrainSuite](https://brainsuite.org/) (tested with BrainSuite23a)

### Installing FSL (Ubuntu/WSL)

```bash
curl -Ls https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/getfsl.sh | sh -s
```

Close and reopen your terminal once it finishes. For custom/advanced installs, download and run `fslinstaller.py` instead — see the [official FSL Linux installation guide](https://fsl.fmrib.ox.ac.uk/fsl/docs/install/linux.html).

### Installing BrainSuite (Ubuntu/WSL)

1. Register and download `BrainSuite23a.linux.tgz` from the [BrainSuite downloads page](http://forums.brainsuite.org/download/) (registration required).
2. Extract it, e.g. to `/opt`:
   ```bash
   sudo tar xvfz BrainSuite23a.linux.tgz -C /opt/
   ```
3. Add `/opt/BrainSuite23a/bin` to your `PATH`.
4. BrainSuite's GUI and some tools additionally require MATLAB Compiler Runtime (MCR) 2023a — install this first. See this [BrainSuite/Brainstorm install walkthrough](https://neuroimage.usc.edu/brainstorm/Tutorials/BstBrainSuite) for details.

### Python dependencies

```bash
pip install -r requirements.txt
```

## Obtaining a BSE reference mask

This pipeline needs an existing BrainSuite BSE mask as the registration target for the BET mask. Generate one from your T1 image using BrainSuite's command-line `bse` tool:

```bash
bse -i your_t1.nii.gz -o bse_output.nii.gz --mask bse_mask.nii.gz
```

(You can also run this interactively through BrainSuite's GUI — the "Brain Surface Extractor" step of Cortical Surface Extraction.) Pass the resulting `bse_mask.nii.gz` as the "reference BSE mask" input when running this pipeline. Full flag reference: [BrainSuite `bse` command-line docs](https://brainsuite.org/processing/surfaceextraction/cse-command-line/).

## Test data

This pipeline was developed and tested against the tutorial dataset provided by BrainSuite's [Nipype Cortical Surface Extraction tutorial](https://brainsuite.org/nipype-cse/):

```bash
curl http://users.bmap.ucla.edu/~jwong/BrainSuiteNipype_Tutorial.zip -o "BrainSuiteNipype_Tutorial.zip"
unzip -o -qq BrainSuiteNipype_Tutorial.zip -d ~/Documents
```

That tutorial's scan (subject `2523412`) originates from the [Beijing Enhanced dataset](https://fcon_1000.projects.nitrc.org/indi/retro/BeijingEnhanced.html), released by Beijing Normal University's State Key Laboratory of Cognitive Neuroscience and Learning through the International Neuroimaging Data-sharing Initiative (INDI), distributed under a CC BY-NC license.

## Usage

```bash
python src/BET_to_BSE_skull_prompted.py
```

The script interactively prompts for:
- Input T1 MRI file (`.nii`/`.nii.gz`)
- An existing BSE reference mask
- An output folder
- Skull/scalp intensity thresholds (defaults: 53 / 116)
- The BrainSuite `bin` folder (auto-detected if in the default location, otherwise entered manually)

## Known limitations (from testing so far)

- Temporal-bone regions can remain incomplete even after BET/Skullfinder threshold tuning.
- Orbital roof / anterior skull-base coverage is sometimes missing.
- Segmentation quality is scanner-dependent (differences observed between Philips and Siemens acquisitions).

## Roadmap

- Benchmark BET `-f` (fractional intensity threshold) and `-g` (vertical gradient) presets per scanner vendor
- Evaluate bias-field correction (N3/N4) and SPM segmentation as complementary preprocessing steps
- Extract skull-thickness metrics from inner/outer skull meshes
- Long-term goal: extend toward infant, forensic, and archaeological skull-segmentation applications

## Screenshots

_Add before/after BSE and BET mask screenshots here._

## License

MIT — see [LICENSE](LICENSE).
