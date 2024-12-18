## C-band-phase-bias

This repository serves as a companion to Devlin and Lohman (2024) "Evaluation of Vegetation Bias in InSAR Time Series for Agricultural Areas within the San Joaquin Valley, CA", EarthArXiv preprint, https://doi.org/10.31223/X50T5K. It contains code developed by the authors for this project and is meant to serve as a starting point for those wishing to reproduce and/or adapt the workflow. 

### Install

The following will clone the repository and create the necessary conda environment.

```bash
git clone https://github.com/kdevlin525/C-band-phase-bias && cd C-band-phase-bias
conda env create --file environment.yml
conda activate phase-bias
```

### Contents

Below are a list of the contents of this repository and a brief descripton of each file.

`ungeocode_to_radar.ipynb`
This notebook resamples georeferenced files (such as GeoTIFFs) to the desired radar coordinates. It assumes radar files are in ISCE2 file format.

`segment_fields.ipynb`
This notebook creates several arrays used for land cover classification and masking: one of stable pixels, one for several crop types, and one with each individual field labelled with an ID.

`field_loop.ipynb`
This is the main notebook of the project. It calculates phase bias and several other metrics for every field for sequential interferograms, then saves several dataframes.

`make_synth_ifgs.py`
This script makes synthetic interferograms that only contain the phase bias calculated in `field_loop.ipynb` and Gaussian noise. These files are used as inputs for a Mintpy inversion.

`unwrap_ifgs.py`
This script reads in SLCs and downlooks, filters, and unwraps to create sequential interferograms.

`masked_unw_ifgs.ipynb`
This notebook creates masked unwrapped interferograms.

DOI: 10.5281/zenodo.14519568