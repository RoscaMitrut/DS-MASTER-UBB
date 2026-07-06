from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import pydicom
except ImportError as exc:
    raise SystemExit(
        "Missing dependency. Install required packages first: pip install pydicom matplotlib"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = PROJECT_ROOT / "code/src/data_analysis/output_lidc_csv/patient_texture_details.csv"


@dataclass
class SliceInfo:
    sop_uid: str
    z_position: float | None
    instance_number: int | None
    path: Path


def parse_uid_list(uid_cell: Any) -> list[str]:
    if uid_cell is None or (isinstance(uid_cell, float) and pd.isna(uid_cell)):
        return []
    return [uid.strip() for uid in str(uid_cell).split(";") if uid.strip()]


def parse_roi_bbox_map(cell: Any) -> dict[str, dict[str, int]]:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return {}
    try:
        parsed = json.loads(str(cell))
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    out: dict[str, dict[str, int]] = {}
    for sop_uid, bbox in parsed.items():
        if not isinstance(sop_uid, str) or not isinstance(bbox, dict):
            continue
        try:
            out[sop_uid] = {
                "xmin": int(bbox["xmin"]),
                "ymin": int(bbox["ymin"]),
                "xmax": int(bbox["xmax"]),
                "ymax": int(bbox["ymax"]),
                "num_points": int(bbox.get("num_points", 0)),
            }
        except (KeyError, TypeError, ValueError):
            continue
    return out


def parse_float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def resolve_path(path_value: str) -> Path:
    path_obj = Path(path_value)
    if path_obj.exists():
        return path_obj
    return (PROJECT_ROOT / path_obj).resolve()


def get_z_from_dataset(ds: Any) -> float | None:
    if hasattr(ds, "ImagePositionPatient") and len(ds.ImagePositionPatient) >= 3:
        return parse_float_or_none(ds.ImagePositionPatient[2])
    return parse_float_or_none(getattr(ds, "SliceLocation", None))


def get_instance_from_dataset(ds: Any) -> int | None:
    return parse_int_or_none(getattr(ds, "InstanceNumber", None))


def load_series_index(series_dir: Path) -> list[SliceInfo]:
    dicom_files = sorted(series_dir.glob("*.dcm"))
    if not dicom_files:
        dicom_files = [p for p in sorted(series_dir.iterdir()) if p.is_file()]

    slices: list[SliceInfo] = []
    for dicom_path in dicom_files:
        try:
            ds = pydicom.dcmread(str(dicom_path), stop_before_pixels=True, force=True)
        except Exception:
            continue

        sop_uid = str(getattr(ds, "SOPInstanceUID", "")).strip()
        if not sop_uid:
            continue

        slices.append(
            SliceInfo(
                sop_uid=sop_uid,
                z_position=get_z_from_dataset(ds),
                instance_number=get_instance_from_dataset(ds),
                path=dicom_path,
            )
        )

    if any(s.z_position is not None for s in slices):
        slices.sort(
            key=lambda s: (
                s.z_position if s.z_position is not None else float("inf"),
                s.instance_number if s.instance_number is not None else 10**9,
                s.path.name,
            )
        )
    else:
        slices.sort(
            key=lambda s: (
                s.instance_number if s.instance_number is not None else 10**9,
                s.path.name,
            )
        )

    return slices


def choose_uid(uids: list[str], policy: str) -> str:
    if not uids:
        raise ValueError("No SOP UIDs found in ct_slice_sop_uids.")

    if policy == "first":
        return uids[0]
    if policy == "last":
        return uids[-1]
    return uids[len(uids) // 2]


def find_row(
    df: pd.DataFrame, patient_id: str | None, nodule_id: str | None, row_index: int | None
) -> pd.Series:
    if row_index is not None:
        if row_index < 0 or row_index >= len(df):
            raise IndexError(f"row-index {row_index} is out of range [0, {len(df) - 1}]")
        return df.iloc[row_index]

    if patient_id is None and nodule_id is None:
        if df.empty:
            raise ValueError("CSV is empty; no rows available.")
        print("No selector provided, defaulting to row-index 0.")
        return df.iloc[0]

    if patient_id is None or nodule_id is None:
        raise ValueError("Provide either --row-index or both --patient-id and --nodule-id.")

    matched = df[
        (df["patient_id"].astype(str) == str(patient_id))
        & (df["nodule_id"].astype(str) == str(nodule_id))
    ]
    if matched.empty:
        raise ValueError(f"No row found for patient_id={patient_id}, nodule_id={nodule_id}")
    if len(matched) > 1:
        raise ValueError(
            "Multiple rows matched. Use --row-index to select the exact row."
        )
    return matched.iloc[0]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read patient_texture_details.csv, print malignancy for one nodule, "
            "and display one CT frame selected from its SOP UID list. "
            "If no selector is given, row-index 0 is used."
        )
    )
    parser.add_argument("--csv-path", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--patient-id", type=str, default="LIDC-IDRI-0072")
    parser.add_argument("--nodule-id", type=str, default="101448")
    parser.add_argument("--row-index", type=int, default=None)
    parser.add_argument(
        "--uid-choice",
        choices=["first", "middle", "last"],
        default="middle",
        help="Which SOP UID from ct_slice_sop_uids to visualize.",
    )
    parser.add_argument(
        "--save-path",
        type=Path,
        default=None,
        help="Optional output path (PNG) for the displayed frame.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open an interactive matplotlib window.",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csv_path)
    row = find_row(df, args.patient_id, args.nodule_id, args.row_index)

    uids = parse_uid_list(row.get("ct_slice_sop_uids"))
    target_uid = choose_uid(uids, args.uid_choice)

    xml_path = resolve_path(str(row["xml_path"]))
    series_dir = xml_path.parent
    slices = load_series_index(series_dir)
    if not slices:
        raise RuntimeError(f"No readable DICOM slices found in: {series_dir}")

    uid_to_idx = {s.sop_uid: i for i, s in enumerate(slices)}

    frame_idx = uid_to_idx.get(target_uid)
    if frame_idx is None:
        for uid in uids:
            frame_idx = uid_to_idx.get(uid)
            if frame_idx is not None:
                target_uid = uid
                break
    if frame_idx is None:
        raise RuntimeError(
            f"None of the SOP UIDs from CSV were found in series: {series_dir}"
        )

    selected = slices[frame_idx]
    ds = pydicom.dcmread(str(selected.path), force=True)
    image = ds.pixel_array.astype("float32")

    slope = parse_float_or_none(getattr(ds, "RescaleSlope", None))
    intercept = parse_float_or_none(getattr(ds, "RescaleIntercept", None))
    if slope is not None:
        image = image * slope
    if intercept is not None:
        image = image + intercept

    malignancy_majority = row.get("malignancy_majority")
    malignancy_binary = row.get("malignancy_binary_majority")
    roi_bbox_map = parse_roi_bbox_map(row.get("roi_bbox_by_sop_json"))
    roi_bbox = roi_bbox_map.get(selected.sop_uid)

    print(f"patient_id: {row.get('patient_id')}")
    print(f"nodule_id: {row.get('nodule_id')}")
    print(f"malignancy_majority: {malignancy_majority}")
    print(f"malignancy_binary_majority: {malignancy_binary} (0=benign, 1=malignant)")
    print(f"selected_sop_uid: {selected.sop_uid}")
    print(f"frame_index_0based: {frame_idx}")
    print(f"instance_number: {selected.instance_number}")
    print(f"z_position: {selected.z_position}")
    print(f"dicom_path: {selected.path}")
    if roi_bbox is not None:
        print(
            "roi_bbox_xyxy: "
            f"{roi_bbox['xmin']},{roi_bbox['ymin']},{roi_bbox['xmax']},{roi_bbox['ymax']} "
            f"(points={roi_bbox['num_points']})"
        )
    else:
        print("roi_bbox_xyxy: not available for selected SOP UID")

    title = (
        f"{row.get('patient_id')} | nodule {row.get('nodule_id')} | "
        f"mal_bin={malignancy_binary} | frame={frame_idx}"
    )
    plt.figure(figsize=(7, 7))
    plt.imshow(image, cmap="gray")
    if roi_bbox is not None:
        width = roi_bbox["xmax"] - roi_bbox["xmin"] + 1
        height = roi_bbox["ymax"] - roi_bbox["ymin"] + 1
        plt.gca().add_patch(
            Rectangle(
                (roi_bbox["xmin"], roi_bbox["ymin"]),
                width,
                height,
                fill=False,
                edgecolor="red",
                linewidth=1.5,
            )
        )
    plt.title(title)
    plt.axis("off")

    if args.save_path is not None:
        args.save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(args.save_path, dpi=150, bbox_inches="tight")
        print(f"saved_frame_png: {args.save_path}")

    if args.no_show:
        plt.close()
    else:
        plt.show()


if __name__ == "__main__":
    main()
