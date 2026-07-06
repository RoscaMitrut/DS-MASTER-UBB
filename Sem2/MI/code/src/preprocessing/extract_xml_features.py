from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import math

import pandas as pd


def local_name(tag: str) -> str:
    """Return XML local tag name without namespace."""
    return tag.rsplit("}", 1)[-1]


def find_first_child(parent: ET.Element, name: str) -> ET.Element | None:
    for child in parent:
        if local_name(child.tag) == name:
            return child
    return None


def parse_int(text: str | None) -> int | None:
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def parse_float(text: str | None) -> float | None:
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def texture_to_category(texture_value: int | None) -> str | None:
    """
    Map LIDC texture score to category:
    1-2 -> ground-glass (non-solid)
    3   -> part-solid
    4-5 -> solid
    """
    if texture_value is None:
        return None
    if texture_value in (1, 2):
        return "ground-glass"
    if texture_value == 3:
        return "part-solid"
    if texture_value in (4, 5):
        return "solid"
    return None


def malignancy_to_binary(malignancy_value: int | None) -> int | None:
    """
    Map LIDC malignancy score to binary class:
    1-2 -> benign (0)
    3-5 -> malignant (1)
    """
    if malignancy_value is None:
        return None
    if malignancy_value in (1, 2):
        return 0
    if malignancy_value in (3, 4, 5):
        return 1
    return None


def majority_vote(values: list[int]) -> int | None:
    if not values:
        return None
    counts = Counter(values)
    max_count = max(counts.values())
    winners = sorted(v for v, c in counts.items() if c == max_count)
    # Deterministic tie-breaker: choose the lower ordinal score.
    return winners[0]


def bbox_from_points(points: list[tuple[int, int]]) -> dict[str, int] | None:
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return {
        "xmin": min(xs),
        "ymin": min(ys),
        "xmax": max(xs),
        "ymax": max(ys),
        "num_points": len(points),
    }


def normalize_path_for_match(path_text: str) -> str:
    return path_text.replace("\\", "/").strip().lower()


def parse_semicolon_list(text: object) -> list[str]:
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return []
    return [item.strip() for item in str(text).split(";") if item.strip()]


def inspect_nodule_frames_from_details(
    details_csv: Path, xml_path: str, nodule_id: str | None = None
) -> None:
    df = pd.read_csv(details_csv)

    required_columns = {
        "xml_path",
        "nodule_id",
        "malignancy_majority",
        "malignancy_binary_majority",
        "ct_slice_z_positions",
        "ct_slice_sop_uids",
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {details_csv}: {sorted(missing)}")

    xml_norm = normalize_path_for_match(xml_path)
    matched = df[df["xml_path"].astype(str).map(normalize_path_for_match) == xml_norm]
    if nodule_id is not None:
        matched = matched[matched["nodule_id"].astype(str) == str(nodule_id)]

    if matched.empty:
        print("No matching nodules found for the provided file/nodule filters.")
        return

    for _, row in matched.iterrows():
        current_nodule_id = row["nodule_id"]
        mal_majority = row["malignancy_majority"]
        mal_binary = row["malignancy_binary_majority"]
        mal_label = (
            "malignant" if str(mal_binary) in {"1", "1.0"} else "benign" if str(mal_binary) in {"0", "0.0"} else "unknown"
        )

        print(f"\nNodule: {current_nodule_id}")
        print(f"XML file: {row['xml_path']}")
        print(f"Malignancy majority score: {mal_majority}")
        print(f"Malignancy mapped: {mal_binary} ({mal_label})")

        z_positions = parse_semicolon_list(row.get("ct_slice_z_positions"))
        sop_uids = parse_semicolon_list(row.get("ct_slice_sop_uids"))
        max_len = max(len(z_positions), len(sop_uids))

        if max_len == 0:
            print("No CT frame information available.")
            continue

        print("Frames (index_0based | z_position | imageSOP_UID):")
        for idx in range(max_len):
            z_val = z_positions[idx] if idx < len(z_positions) else ""
            sop_val = sop_uids[idx] if idx < len(sop_uids) else ""
            print(f"{idx} | {z_val} | {sop_val}")


def extract_nodule_rows_from_xml(xml_path: Path, patient_id: str) -> list[dict]:
    rows: list[dict] = []
    try:
        root = ET.parse(xml_path).getroot()
    except Exception:
        return rows

    nodule_votes: dict[str, dict[str, list]] = defaultdict(
        lambda: {
            "texture_values": [],
            "malignancy_values": [],
            "reading_session_indices": [],
            "z_positions": [],
            "sop_uids": [],
            "roi_points_by_sop": defaultdict(list),
        }
    )

    reading_session_index = 0
    for elem in root.iter():
        if local_name(elem.tag) != "readingSession":
            continue

        reading_session_index += 1
        for nodule_elem in elem:
            if local_name(nodule_elem.tag) != "unblindedReadNodule":
                continue

            nodule_id_elem = find_first_child(nodule_elem, "noduleID")
            characteristics_elem = find_first_child(nodule_elem, "characteristics")
            texture_elem = (
                find_first_child(characteristics_elem, "texture")
                if characteristics_elem is not None
                else None
            )
            malignancy_elem = (
                find_first_child(characteristics_elem, "malignancy")
                if characteristics_elem is not None
                else None
            )

            texture_value = parse_int(texture_elem.text if texture_elem is not None else None)
            malignancy_value = parse_int(
                malignancy_elem.text if malignancy_elem is not None else None
            )

            nodule_id = (
                nodule_id_elem.text.strip()
                if nodule_id_elem is not None and nodule_id_elem.text
                else None
            )
            if nodule_id is None:
                continue

            nodule_data = nodule_votes[nodule_id]
            nodule_data["reading_session_indices"].append(reading_session_index)
            if texture_value is not None:
                nodule_data["texture_values"].append(texture_value)
            if malignancy_value is not None:
                nodule_data["malignancy_values"].append(malignancy_value)

            for roi_elem in nodule_elem:
                if local_name(roi_elem.tag) != "roi":
                    continue
                z_elem = find_first_child(roi_elem, "imageZposition")
                sop_elem = find_first_child(roi_elem, "imageSOP_UID")
                z_value = parse_float(z_elem.text if z_elem is not None else None)
                if z_value is not None:
                    nodule_data["z_positions"].append(z_value)
                sop_uid = (
                    sop_elem.text.strip()
                    if sop_elem is not None and sop_elem.text and sop_elem.text.strip()
                    else None
                )
                if sop_uid is None:
                    continue

                nodule_data["sop_uids"].append(sop_uid)

                for edge_elem in roi_elem:
                    if local_name(edge_elem.tag) != "edgeMap":
                        continue
                    x_elem = find_first_child(edge_elem, "xCoord")
                    y_elem = find_first_child(edge_elem, "yCoord")
                    x_val = parse_int(x_elem.text if x_elem is not None else None)
                    y_val = parse_int(y_elem.text if y_elem is not None else None)
                    if x_val is None or y_val is None:
                        continue
                    nodule_data["roi_points_by_sop"][sop_uid].append((x_val, y_val))

    for nodule_id, nodule_data in nodule_votes.items():
        texture_majority = majority_vote(nodule_data["texture_values"])
        malignancy_majority = majority_vote(nodule_data["malignancy_values"])
        texture_category = texture_to_category(texture_majority)
        malignancy_binary = malignancy_to_binary(malignancy_majority)

        # Keep nodules that have at least one requested label.
        if texture_majority is None and malignancy_majority is None:
            continue

        unique_z = sorted(set(nodule_data["z_positions"]))
        unique_sop = sorted(set(nodule_data["sop_uids"]))
        roi_bbox_by_sop: dict[str, dict[str, int]] = {}
        for sop_uid, points in nodule_data["roi_points_by_sop"].items():
            bbox = bbox_from_points(points)
            if bbox is not None:
                roi_bbox_by_sop[sop_uid] = bbox

        rows.append(
            {
                "patient_id": patient_id,
                "xml_path": str(xml_path),
                "nodule_id": nodule_id,
                "num_texture_opinions": len(nodule_data["texture_values"]),
                "num_malignancy_opinions": len(nodule_data["malignancy_values"]),
                "texture_majority": texture_majority,
                "texture_category_majority": texture_category,
                "malignancy_majority": malignancy_majority,
                "malignancy_binary_majority": malignancy_binary,
                "ct_slice_z_min": min(unique_z) if unique_z else None,
                "ct_slice_z_max": max(unique_z) if unique_z else None,
                "ct_slice_z_positions": ";".join(str(z) for z in unique_z),
                "ct_slice_sop_uids": ";".join(unique_sop),
                "roi_bbox_by_sop_json": json.dumps(roi_bbox_by_sop, separators=(",", ":")),
            }
        )

    return rows


def build_patient_summary(
    patient_ids: list[str], nodule_df: pd.DataFrame
) -> pd.DataFrame:
    summary_rows: list[dict] = []

    for patient_id in patient_ids:
        patient_df = nodule_df[nodule_df["patient_id"] == patient_id]

        texture_counts = patient_df["texture_category_majority"].value_counts()
        dominant_texture = texture_counts.idxmax() if not texture_counts.empty else None

        malignancy_counts = patient_df["malignancy_binary_majority"].value_counts()
        dominant_malignancy = (
            malignancy_counts.idxmax() if not malignancy_counts.empty else None
        )

        summary_rows.append(
            {
                "patient_id": patient_id,
                "num_nodules": int(len(patient_df)),
                "ground_glass_count": int(texture_counts.get("ground-glass", 0)),
                "part_solid_count": int(texture_counts.get("part-solid", 0)),
                "solid_count": int(texture_counts.get("solid", 0)),
                "benign_nodule_count": int(malignancy_counts.get(0, 0)),
                "malignant_nodule_count": int(malignancy_counts.get(1, 0)),
                "dominant_texture_category": dominant_texture,
                "dominant_malignancy_binary": dominant_malignancy,
            }
        )

    return pd.DataFrame(summary_rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract LIDC per-nodule majority texture and majority malignancy from CT XML "
            "for patient IDs in processed_lung_nodules.csv."
        )
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("code\src\data_analysis\output_lidc_csv\processed_lung_nodules.csv"),
        help="CSV containing a patient_id column.",
    )
    parser.add_argument(
        "--lidc-root",
        type=Path,
        default=Path("code/data/LIDC-IDRI"),
        help="Root folder containing LIDC-IDRI-xxxx patient directories.",
    )
    parser.add_argument(
        "--out-details",
        type=Path,
        default=Path("code/src/data_analysis/output_lidc_csv/patient_texture_details.csv"),
        help="Output CSV with one row per nodule (majority opinion across readers).",
    )
    parser.add_argument(
        "--out-summary",
        type=Path,
        default=Path("code/src/data_analysis/output_lidc_csv/patient_texture_summary.csv"),
        help="Output CSV with one row per patient.",
    )
    parser.add_argument(
        "--inspect-csv",
        type=Path,
        help="Existing patient_texture_details.csv to inspect.",
    )
    parser.add_argument(
        "--inspect-xml-path",
        type=str,
        help="Specific xml_path value to inspect in the details CSV.",
    )
    parser.add_argument(
        "--inspect-nodule-id",
        type=str,
        help="Optional nodule_id filter for inspect mode.",
    )
    args = parser.parse_args()

    if args.inspect_csv and args.inspect_xml_path:
        inspect_nodule_frames_from_details(
            details_csv=args.inspect_csv,
            xml_path=args.inspect_xml_path,
            nodule_id=args.inspect_nodule_id,
        )
        return

    input_df = pd.read_csv(args.input_csv)
    if "patient_id" not in input_df.columns:
        raise ValueError(f"'patient_id' column not found in {args.input_csv}")

    patient_ids = (
        input_df["patient_id"]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .tolist()
    )

    detail_rows: list[dict] = []
    for patient_id in patient_ids:
        patient_dir = args.lidc_root / patient_id
        if not patient_dir.exists():
            continue

        for xml_path in patient_dir.rglob("*.xml"):
            detail_rows.extend(extract_nodule_rows_from_xml(xml_path, patient_id))

    details_df = pd.DataFrame(
        detail_rows,
        columns=[
            "patient_id",
            "xml_path",
            "nodule_id",
            "num_texture_opinions",
            "num_malignancy_opinions",
            "texture_majority",
            "texture_category_majority",
            "malignancy_majority",
            "malignancy_binary_majority",
            "ct_slice_z_min",
            "ct_slice_z_max",
            "ct_slice_z_positions",
            "ct_slice_sop_uids",
            "roi_bbox_by_sop_json",
        ],
    )

    summary_df = build_patient_summary(patient_ids, details_df)

    args.out_details.parent.mkdir(parents=True, exist_ok=True)
    args.out_summary.parent.mkdir(parents=True, exist_ok=True)
    details_df.to_csv(args.out_details, index=False)
    summary_df.to_csv(args.out_summary, index=False)

    print(f"Patients in input: {len(patient_ids)}")
    print(f"Nodules extracted: {len(details_df)}")
    print(f"Wrote details: {args.out_details}")
    print(f"Wrote summary: {args.out_summary}")


if __name__ == "__main__":
    main()
