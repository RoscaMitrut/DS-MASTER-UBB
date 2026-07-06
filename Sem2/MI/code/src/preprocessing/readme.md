# extract_xml_features.py

This script reads LIDC XML files for each `patient_id` from:
- `code/src/data_analysis/output_lidc_csv/processed_lung_nodules.csv`

It extracts nodule information from CT annotations:
- texture
- malignancy
- CT slice ids (`imageSOP_UID`)
- CT z positions
- 2D ROI boxes (from ROI contour points)

If a nodule has multiple reader opinions, it keeps the majority opinion.

Texture mapping:
- `1, 2 -> ground-glass`
- `3 -> part-solid`
- `4, 5 -> solid`

Malignancy mapping:
- `1, 2 -> benign (0)`
- `3, 4, 5 -> malignant (1)`

Outputs:
- `code/src/data_analysis/output_lidc_csv/patient_texture_details.csv`
- one row per nodule
- includes majority labels and ROI bbox data (`roi_bbox_by_sop_json`)
- `code/src/data_analysis/output_lidc_csv/patient_texture_summary.csv`
- one row per patient
- counts of texture and benign/malignant nodules

Run:
```bash
python code/src/preprocessing/extract_xml_features.py
```

Inspect mode (print frames and malignancy from an existing details CSV):
```bash
python code/src/preprocessing/extract_xml_features.py --inspect-csv code/src/data_analysis/output_lidc_csv/patient_texture_details.csv --inspect-xml-path "code/data/LIDC-IDRI/.../xxx.xml"
```

# visualize_nodule_frame.py

This script reads one nodule from:
- `code/src/data_analysis/output_lidc_csv/patient_texture_details.csv`

Then it:
- finds the DICOM slice using `imageSOP_UID`
- loads the CT frame
- prints nodule info (patient id, nodule id, malignancy, frame index, z position)
- draws the ROI 2D box on the image (red rectangle), if available

Select nodule by:
- `--patient-id` and `--nodule-id`
- or `--row-index`

Default selection in script:
- `patient_id = LIDC-IDRI-0072`
- `nodule_id = 101448`

Run:
```bash
python code/src/preprocessing/visualize_nodule_frame.py
```

Example:
```bash
python code/src/preprocessing/visualize_nodule_frame.py --patient-id LIDC-IDRI-0068 --nodule-id 114086
```

Optional:
- `--uid-choice first|middle|last` to choose which nodule slice to show
- `--save-path file.png` to save image
- `--no-show` to run without opening window
