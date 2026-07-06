from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import json
import random
from pathlib import Path
from typing import Any

import pandas as pd
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset

try:
    import pydicom
except ImportError as exc:
    raise SystemExit("Missing dependency: pydicom. Install with `pip install pydicom`.") from exc

try:
    from PIL import Image
except ImportError:
    Image = None  # Optional: only needed for --export-frames-dir


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = PROJECT_ROOT / "code/src/data_analysis/output_lidc_csv/patient_texture_details.csv"
DEFAULT_MODEL_OUT = PROJECT_ROOT / "code/src/training/texture_only.pt"
TEXTURE_CATEGORY_TO_INDEX = {
    "ground-glass": 0,
    "part-solid": 1,
    "solid": 2,
}
TEXTURE_CLASS_NAMES = ["ground-glass", "part-solid", "solid"]
N_TEXTURE_CLASSES = 3


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


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
            }
        except (KeyError, TypeError, ValueError):
            continue
    return out


def parse_float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def choose_uid(uids: list[str], policy: str) -> str:
    if not uids:
        raise ValueError("No SOP UIDs found.")
    if policy == "first":
        return uids[0]
    if policy == "last":
        return uids[-1]
    return uids[len(uids) // 2]


def resolve_path(path_value: str) -> Path:
    path_obj = Path(path_value)
    if path_obj.exists():
        return path_obj
    return (PROJECT_ROOT / path_obj).resolve()


def parse_int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_z_from_dataset(ds: Any) -> float | None:
    if hasattr(ds, "ImagePositionPatient") and len(ds.ImagePositionPatient) >= 3:
        return parse_float_or_none(ds.ImagePositionPatient[2])
    return parse_float_or_none(getattr(ds, "SliceLocation", None))


def get_instance_from_dataset(ds: Any) -> int | None:
    return parse_int_or_none(getattr(ds, "InstanceNumber", None))


@dataclass
class SliceInfo:
    sop_uid: str
    z_position: float | None
    instance_number: int | None
    path: Path


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


def hu_normalize(image: torch.Tensor, hu_min: float = -1000.0, hu_max: float = 400.0) -> torch.Tensor:
    image = torch.clamp(image, min=hu_min, max=hu_max)
    image = (image - hu_min) / (hu_max - hu_min)
    return image


def crop_with_margin(image: torch.Tensor, bbox: dict[str, int] | None, margin: int) -> torch.Tensor:
    if bbox is None:
        return image
    h, w = int(image.shape[0]), int(image.shape[1])
    xmin = max(0, int(bbox["xmin"]) - margin)
    ymin = max(0, int(bbox["ymin"]) - margin)
    xmax = min(w - 1, int(bbox["xmax"]) + margin)
    ymax = min(h - 1, int(bbox["ymax"]) + margin)
    if xmax <= xmin or ymax <= ymin:
        return image
    return image[ymin : ymax + 1, xmin : xmax + 1]


def resize_2d(image: torch.Tensor, size: int) -> torch.Tensor:
    image = image.unsqueeze(0).unsqueeze(0)
    image = F.interpolate(image, size=(size, size), mode="bilinear", align_corners=False)
    return image.squeeze(0)


def maybe_export_png(image_chw: torch.Tensor, out_path: Path) -> None:
    if Image is None:
        raise RuntimeError("Pillow is required for --export-frames-dir. Install with `pip install pillow`.")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    array = torch.clamp(image_chw, 0.0, 1.0).squeeze(0).mul(255.0).byte().cpu().numpy()
    Image.fromarray(array, mode="L").save(out_path)


class LIDCTextureFrameDataset(Dataset):
    def __init__(
        self,
        csv_path: Path,
        uid_choice: str = "middle",
        image_size: int = 128,
        roi_margin: int = 8,
        export_frames_dir: Path | None = None,
        max_samples: int | None = None,
    ) -> None:
        self.csv_path = csv_path
        self.uid_choice = uid_choice
        self.image_size = image_size
        self.roi_margin = roi_margin
        self.export_frames_dir = export_frames_dir
        self.samples: list[dict[str, Any]] = []
        self.series_cache: dict[Path, dict[str, Path]] = {}
        self._build_index(max_samples=max_samples)

    def _build_index(self, max_samples: int | None) -> None:
        df = pd.read_csv(self.csv_path)
        for _, row in df.iterrows():
            texture_category = str(row.get("texture_category_majority", "")).strip().lower()
            texture_index = TEXTURE_CATEGORY_TO_INDEX.get(texture_category)
            if texture_index is None:
                continue

            uids = parse_uid_list(row.get("ct_slice_sop_uids"))
            if not uids:
                continue
            target_uid = choose_uid(uids, self.uid_choice)

            xml_path = resolve_path(str(row["xml_path"]))
            series_dir = xml_path.parent
            uid_to_path = self._get_uid_to_path(series_dir)
            frame_path = uid_to_path.get(target_uid)
            if frame_path is None:
                for uid in uids:
                    frame_path = uid_to_path.get(uid)
                    if frame_path is not None:
                        target_uid = uid
                        break
            if frame_path is None:
                continue

            bbox_map = parse_roi_bbox_map(row.get("roi_bbox_by_sop_json"))
            bbox = bbox_map.get(target_uid)
            if bbox is None and bbox_map:
                bbox = next(iter(bbox_map.values()))

            self.samples.append(
                {
                    "patient_id": str(row.get("patient_id")),
                    "nodule_id": str(row.get("nodule_id")),
                    "target_uid": target_uid,
                    "frame_path": frame_path,
                    "bbox": bbox,
                    "texture_label_idx": texture_index,
                }
            )
            if max_samples is not None and len(self.samples) >= max_samples:
                break

    def _get_uid_to_path(self, series_dir: Path) -> dict[str, Path]:
        cached = self.series_cache.get(series_dir)
        if cached is not None:
            return cached
        slices = load_series_index(series_dir)
        uid_to_path = {s.sop_uid: s.path for s in slices}
        self.series_cache[series_dir] = uid_to_path
        return uid_to_path

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        sample = self.samples[idx]
        ds = pydicom.dcmread(str(sample["frame_path"]), force=True)
        image = torch.from_numpy(ds.pixel_array.astype("float32"))

        slope = parse_float_or_none(getattr(ds, "RescaleSlope", None))
        intercept = parse_float_or_none(getattr(ds, "RescaleIntercept", None))
        if slope is not None:
            image = image * float(slope)
        if intercept is not None:
            image = image + float(intercept)

        image = hu_normalize(image)
        image = crop_with_margin(image, sample["bbox"], self.roi_margin)
        image = resize_2d(image, self.image_size)

        if self.export_frames_dir is not None:
            export_name = (
                f"{sample['patient_id']}_{sample['nodule_id']}_{sample['target_uid']}.png".replace("/", "_")
            )
            maybe_export_png(image, self.export_frames_dir / export_name)

        texture = F.one_hot(
            torch.tensor(sample["texture_label_idx"], dtype=torch.long),
            num_classes=N_TEXTURE_CLASSES,
        ).float()
        return image, texture


class ConvBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class TextureOnlyNet(nn.Module):
    def __init__(self, n_texture_classes: int = N_TEXTURE_CLASSES) -> None:
        super().__init__()
        channels = [1, 32, 64, 128]
        self.blocks = nn.ModuleList(
            [ConvBlock(channels[i], channels[i + 1]) for i in range(len(channels) - 1)]
        )
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.gap = nn.AdaptiveAvgPool2d((1, 1))
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(64, n_texture_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for block in self.blocks:
            x = block(x)
            x = self.pool(x)
        x = self.gap(x)
        return self.head(x)


def build_split_indices(
    n_samples: int, val_ratio: float, test_ratio: float, seed: int
) -> tuple[list[int], list[int], list[int]]:
    idx = list(range(n_samples))
    rnd = random.Random(seed)
    rnd.shuffle(idx)
    n_val = max(1, int(n_samples * val_ratio))
    n_test = max(1, int(n_samples * test_ratio))

    while n_val + n_test >= n_samples and (n_val > 1 or n_test > 1):
        if n_val >= n_test and n_val > 1:
            n_val -= 1
        elif n_test > 1:
            n_test -= 1
        else:
            break

    if n_val + n_test >= n_samples:
        raise ValueError(
            "Split ratios leave no training samples. Lower --val-ratio/--test-ratio or increase dataset size."
        )

    val_idx = idx[:n_val]
    test_idx = idx[n_val : n_val + n_test]
    train_idx = idx[n_val + n_test :]
    return train_idx, val_idx, test_idx


def one_hot_cross_entropy(logits: torch.Tensor, onehot_targets: torch.Tensor) -> torch.Tensor:
    return -(onehot_targets * F.log_softmax(logits, dim=1)).sum(dim=1).mean()


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_classification_metrics(
    preds: torch.Tensor,
    labels: torch.Tensor,
    class_names: list[str],
) -> dict[str, Any]:
    num_classes = len(class_names)
    confusion = torch.zeros((num_classes, num_classes), dtype=torch.int64)
    for true_label, pred_label in zip(labels.view(-1), preds.view(-1)):
        confusion[int(true_label), int(pred_label)] += 1

    per_class: dict[str, dict[str, float | int]] = {}
    precision_sum = 0.0
    recall_sum = 0.0
    f1_sum = 0.0

    for class_index, class_name in enumerate(class_names):
        true_positives = int(confusion[class_index, class_index].item())
        false_positives = int(confusion[:, class_index].sum().item() - true_positives)
        false_negatives = int(confusion[class_index, :].sum().item() - true_positives)
        support = int(confusion[class_index, :].sum().item())

        precision = safe_divide(true_positives, true_positives + false_positives)
        recall = safe_divide(true_positives, true_positives + false_negatives)
        f1 = safe_divide(2.0 * precision * recall, precision + recall)

        precision_sum += precision
        recall_sum += recall
        f1_sum += f1
        per_class[class_name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    total_samples = int(confusion.sum().item())
    correct_samples = int(torch.diag(confusion).sum().item())
    return {
        "accuracy": safe_divide(correct_samples, total_samples),
        "precision": safe_divide(precision_sum, num_classes),
        "recall": safe_divide(recall_sum, num_classes),
        "f1": safe_divide(f1_sum, num_classes),
        "support": total_samples,
        "per_class": per_class,
    }


def format_metrics(prefix: str, metrics: dict[str, Any]) -> str:
    return (
        f"{prefix}_acc={metrics['accuracy']:.4f} "
        f"{prefix}_precision={metrics['precision']:.4f} "
        f"{prefix}_recall={metrics['recall']:.4f} "
        f"{prefix}_f1={metrics['f1']:.4f}"
    )


def print_per_class_metrics(split_name: str, task_name: str, metrics: dict[str, Any]) -> None:
    per_class = metrics.get("per_class", {})
    for class_name, class_metrics in per_class.items():
        print(
            f"{split_name}_{task_name}_{class_name}: "
            f"precision={class_metrics['precision']:.4f} "
            f"recall={class_metrics['recall']:.4f} "
            f"f1={class_metrics['f1']:.4f} "
            f"support={class_metrics['support']}"
        )


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> dict[str, Any]:
    model.eval()
    total_loss = 0.0
    n_batches = 0
    preds: list[torch.Tensor] = []
    labels: list[torch.Tensor] = []
    with torch.no_grad():
        for images, tex_onehot in loader:
            images = images.to(device)
            tex_onehot = tex_onehot.to(device)

            logits = model(images)
            loss = one_hot_cross_entropy(logits, tex_onehot)

            total_loss += float(loss.item())
            preds.append(torch.argmax(logits, dim=1).cpu())
            labels.append(torch.argmax(tex_onehot, dim=1).cpu())
            n_batches += 1

    if n_batches == 0:
        metrics = compute_classification_metrics(
            preds=torch.empty(0, dtype=torch.long),
            labels=torch.empty(0, dtype=torch.long),
            class_names=TEXTURE_CLASS_NAMES,
        )
        return {"loss": 0.0, "texture": metrics}

    metrics = compute_classification_metrics(
        preds=torch.cat(preds),
        labels=torch.cat(labels),
        class_names=TEXTURE_CLASS_NAMES,
    )
    return {"loss": total_loss / n_batches, "texture": metrics}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Train a single-task CT model on LIDC nodule frames for texture classification. "
            "Input: 2D CT frame. Output: texture category (3-class one-hot)."
        )
    )
    parser.add_argument("--csv-path", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--uid-choice", choices=["first", "middle", "last"], default="middle")
    parser.add_argument("--image-size", type=int, default=128)
    parser.add_argument("--roi-margin", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--early-stopping-patience", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument(
        "--export-frames-dir",
        type=Path,
        default=None,
        help="Optional: export each selected nodule frame as PNG.",
    )
    parser.add_argument("--model-out", type=Path, default=DEFAULT_MODEL_OUT)
    args = parser.parse_args()

    if not (0.0 < args.val_ratio < 1.0):
        raise ValueError("--val-ratio must be between 0 and 1.")
    if not (0.0 < args.test_ratio < 1.0):
        raise ValueError("--test-ratio must be between 0 and 1.")
    if args.val_ratio + args.test_ratio >= 1.0:
        raise ValueError("--val-ratio + --test-ratio must be < 1.0.")
    if args.early_stopping_patience < 1:
        raise ValueError("--early-stopping-patience must be at least 1.")

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = LIDCTextureFrameDataset(
        csv_path=args.csv_path,
        uid_choice=args.uid_choice,
        image_size=args.image_size,
        roi_margin=args.roi_margin,
        export_frames_dir=args.export_frames_dir,
        max_samples=args.max_samples,
    )
    if len(dataset) < 3:
        raise RuntimeError(
            "Not enough valid samples after filtering and DICOM matching. Need at least 3."
        )

    train_idx, val_idx, test_idx = build_split_indices(
        len(dataset), args.val_ratio, args.test_ratio, args.seed
    )
    train_ds = torch.utils.data.Subset(dataset, train_idx)
    val_ds = torch.utils.data.Subset(dataset, val_idx)
    test_ds = torch.utils.data.Subset(dataset, test_idx)

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )

    model = TextureOnlyNet().to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )

    best_val_loss = float("inf")
    best_state: dict[str, Any] | None = None
    epochs_without_improvement = 0

    print(f"device: {device}")
    print(f"samples_total: {len(dataset)}")
    print(f"samples_train: {len(train_ds)}")
    print(f"samples_val: {len(val_ds)}")
    print(f"samples_test: {len(test_ds)}")

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        n_batches = 0
        preds: list[torch.Tensor] = []
        labels: list[torch.Tensor] = []

        for images, tex_onehot in train_loader:
            images = images.to(device)
            tex_onehot = tex_onehot.to(device)

            optimizer.zero_grad()
            logits = model(images)
            loss = one_hot_cross_entropy(logits, tex_onehot)
            loss.backward()
            optimizer.step()

            running_loss += float(loss.item())
            preds.append(torch.argmax(logits, dim=1).detach().cpu())
            labels.append(torch.argmax(tex_onehot, dim=1).detach().cpu())
            n_batches += 1

        train_metrics = {
            "loss": running_loss / max(1, n_batches),
            "texture": compute_classification_metrics(
                preds=torch.cat(preds) if preds else torch.empty(0, dtype=torch.long),
                labels=torch.cat(labels) if labels else torch.empty(0, dtype=torch.long),
                class_names=TEXTURE_CLASS_NAMES,
            ),
        }
        val_metrics = evaluate(model=model, loader=val_loader, device=device)

        print(
            f"epoch {epoch:02d} | "
            f"train_loss={train_metrics['loss']:.4f} "
            f"{format_metrics('train_tex', train_metrics['texture'])} | "
            f"val_loss={val_metrics['loss']:.4f} "
            f"{format_metrics('val_tex', val_metrics['texture'])}"
        )

        if val_metrics["loss"] < best_val_loss:
            best_val_loss = val_metrics["loss"]
            epochs_without_improvement = 0
            best_state = {
                "model_state_dict": copy.deepcopy(model.state_dict()),
                "args": vars(args),
                "val_metrics": val_metrics,
            }
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= args.early_stopping_patience:
                print(
                    "early_stopping: "
                    f"epoch={epoch:02d} "
                    f"patience={args.early_stopping_patience} "
                    f"best_val_loss={best_val_loss:.4f}"
                )
                break

    if best_state is None:
        raise RuntimeError("Training completed but no checkpoint was captured.")

    model.load_state_dict(best_state["model_state_dict"])
    test_metrics = evaluate(model=model, loader=test_loader, device=device)
    best_state["test_metrics"] = test_metrics

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(best_state, args.model_out)
    print(f"saved_best_model: {args.model_out}")
    print(f"best_val_loss: {best_val_loss:.4f}")
    print(
        "test_metrics: "
        f"loss={test_metrics['loss']:.4f} "
        f"{format_metrics('texture', test_metrics['texture'])}"
    )
    print_per_class_metrics("test", "texture", test_metrics["texture"])


if __name__ == "__main__":
    main()
