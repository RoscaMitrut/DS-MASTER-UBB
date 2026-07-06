# Lung Nodule Multi-Task Learning with Cross-Talk

Teaser: https://youtu.be/YVKSJVsAflI

## Project Description

Lung nodules detected through low-dose CT screening have highly variable clinical significance: some remain indolent for years, while others rapidly progress to malignancy. Clinicians typically rely on multiple heterogeneous attributes, including radiomic features, volumetric growth patterns, and patient clinical data, to stratify risk and decide between monitoring and intervention.

This project explores a multi-task learning (MTL) approach for lung nodule analysis. MTL is useful in this setting because related clinical outcomes can be learned jointly, allowing the model to share relevant information across tasks and improve generalization. We focus in particular on cross-talk mechanisms between task-specific branches, such as cross-stitch units, sluice-style information sharing, or co-attention, so that the tasks can directly influence one another through shared representations.

The proposed model jointly predicts:

- **T1:** Nodule malignancy risk (`benign` vs. `malignant`)
- **T2:** Radiological subtype classification (`solid`, `part-solid`, `ground-glass`)

Beyond predictive performance, the project also emphasizes interpretability. The model outputs are accompanied by SHAP explanations, task-specific feature importance analysis, and an examination of how the two tasks interact inside the shared architecture.

## Team

- **Raicu Maria**
- **Rosca Eduard**

## Content

This repository contains the materials and implementation for a study of cross-talk-based multi-task learning in lung cancer screening support. The main components of the project are:

- Data processing and preparation for lung nodule records derived from low-dose CT screening data
- Feature-based modeling using radiomic, volumetric, and clinical variables
- Multi-task learning architectures designed to jointly solve malignancy prediction and radiological subtype classification
- Cross-task interaction mechanisms, including approaches such as cross-stitch connections and co-attention links
- Model evaluation against single-task baselines
- Interpretability analysis through SHAP values and task-wise feature importance
- Investigation of how shared learning between tasks affects final predictions

## Conclusion

As a conclusion, our proposed models can jointly predict nodule texture and malignancy using cross-stitch and co-attention links, but on the dataset we used, due to class imbalance neither variant could outperform the single-task baseline model. The limiting factor was the quality and balance of the data rather than the architecture itself.
