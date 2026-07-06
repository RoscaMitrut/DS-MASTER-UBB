# train_multitask_texture_malignancy.py

This script trains a **multi-task CT model** that takes a 2D nodule frame as input and predicts:
- `texture_category_majority` (3-class category, one-hot encoded target)
- `malignancy_binary_majority` (binary label: `0` benign, `1` malignant)

The model uses **soft sharing / cross-talk** between tasks and can switch between:
- `cross_stitch`: learnable linear mixing between task streams
- `co_attention`: channel-wise mutual gating between task streams

## 1) Required preprocessing

Before training, you must generate:
- `code/src/data_analysis/output_lidc_csv/patient_texture_details.csv`

This CSV is produced by preprocessing scripts (see `code/src/preprocessing`), especially:
- `extract_xml_features.py` (extracts labels + SOP UIDs + ROI info from XML)

The training script reads DICOM slices directly from paths referenced by `xml_path` in this CSV.

## 2) Input

Default input CSV:
- `code/src/data_analysis/output_lidc_csv/patient_texture_details.csv`

Important columns used:
- `xml_path`
- `ct_slice_sop_uids`
- `roi_bbox_by_sop_json`
- `texture_category_majority`
- `malignancy_binary_majority`
- `patient_id`, `nodule_id` (for bookkeeping / optional frame export names)

For each row (nodule), the script:
1. selects one SOP UID (`--uid-choice first|middle|last`, default `middle`)
2. locates the matching DICOM slice in the same series folder as `xml_path`
3. loads pixel array and applies DICOM rescale (`RescaleSlope`, `RescaleIntercept`)
4. normalizes HU to `[0,1]` using clip range `[-1000, 400]`
5. crops around ROI bbox (if available) with margin `--roi-margin`
6. resizes to `--image-size` (default `128x128`)

Optional:
- save selected frames as PNG using `--export-frames-dir`.

## 3) Train / validation / test split

The dataset is shuffled (seeded) and split into:
- train
- validation
- test

Controlled by:
- `--val-ratio` (default `0.2`)
- `--test-ratio` (default `0.2`)

Constraint:
- `val-ratio + test-ratio < 1.0`

## 4) Training method

Model: `MultiTaskCrossTalkNet`
- Two CNN branches (texture branch + malignancy branch)
- After each block, a cross-talk unit exchanges information between branches
- The mechanism is selected with `--cross-talk`
  - `cross_stitch`: learnable 2x2 feature mixing
  - `co_attention`: channel-wise co-attention using global descriptors from the other task branch
- Two classification heads output logits for:
  - texture: 3 classes (`ground-glass`, `part-solid`, `solid`)
  - malignancy: 2 classes (`0`, `1`)

Texture encoding:
- `texture_category_majority` is converted with one-hot encoding:
  - `ground-glass -> [1,0,0]`
  - `part-solid -> [0,1,0]`
  - `solid -> [0,0,1]`

Loss:
- `one-hot cross-entropy(texture)` + `CrossEntropy(malignancy_binary)`
- weighted by:
  - `--texture-loss-weight` (default `1.0`)
  - `--malignancy-loss-weight` (default `1.0`)

Optimizer:
- `AdamW` (`--learning-rate`, `--weight-decay`)

Model selection:
- best checkpoint is chosen by **lowest validation loss**

Final evaluation:
- after training, best checkpoint is evaluated on the held-out **test** split.

## 5) Output

Saved checkpoint (default):
- `code/src/training/multitask_texture_malignancy_cross_talk.pt`

Checkpoint contains:
- `model_state_dict`
- run args
- best validation metrics
- final test metrics

Metrics now include, for both tasks (`texture`, `malignancy`):
- `accuracy`
- overall `precision`, `recall`, `f1` (macro-averaged across classes)
- `per_class` metrics with:
  - `precision`
  - `recall`
  - `f1`
  - `support`

Console logs include:
- sample counts (`total/train/val/test`)
- per-epoch train/val loss + accuracy/precision/recall/F1 summaries
- final test loss + summary metrics
- final test per-class precision/recall/F1/support

## 6) Example runs

Full run with defaults:
```bash
python code/src/training/train_multitask_texture_malignancy.py
```

Run with co-attention cross-talk:
```bash
python code/src/training/train_multitask_texture_malignancy.py --cross-talk co_attention
```

Small smoke run (limited samples):
```bash
python code/src/training/train_multitask_texture_malignancy.py --max-samples 14 --epochs 3
```

Run and export selected nodule frames:
```bash
python code/src/training/train_multitask_texture_malignancy.py --export-frames-dir code/src/training/extracted_frames
```
