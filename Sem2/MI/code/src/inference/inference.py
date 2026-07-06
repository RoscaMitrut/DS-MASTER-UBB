from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

import torch
from torch.nn import functional as F

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Missing dependency: pillow. Install with `pip install pillow`.") from exc


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "code" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from training.train_malignancy_only import (  # noqa: E402
    LIDCMalignancyFrameDataset,
    MALIGNANCY_CLASS_NAMES,
    MalignancyOnlyNet,
    build_split_indices as build_malignancy_split_indices,
)
from training.train_multitask_texture_malignancy import (  # noqa: E402
    LIDCNoduleFrameDataset,
    MultiTaskCrossTalkNet,
    build_split_indices as build_multitask_split_indices,
)
from training.train_texture_only import (  # noqa: E402
    LIDCTextureFrameDataset,
    TEXTURE_CLASS_NAMES,
    TextureOnlyNet,
    build_split_indices as build_texture_split_indices,
    resize_2d,
)


DEFAULT_CSV = PROJECT_ROOT / "code/src/data_analysis/output_lidc_csv/patient_texture_details.csv"
DEFAULT_OUT_DIR = PROJECT_ROOT / "code/src/inference/outputs"
DEFAULT_MULTITASK_MODEL = PROJECT_ROOT / "code/src/training/multitask_texture_malignancy_cross_talk.pt"
DEFAULT_TEXTURE_MODEL = PROJECT_ROOT / "code/src/training/texture_only.pt"
DEFAULT_MALIGNANCY_MODEL = PROJECT_ROOT / "code/src/training/malignancy_only.pt"


def load_checkpoint(model_path: Path, device: torch.device) -> dict[str, Any]:
    try:
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    except TypeError:
        checkpoint = torch.load(model_path, map_location=device)
    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise ValueError(f"Checkpoint does not contain a model_state_dict: {model_path}")
    return checkpoint


def save_preprocessed_image(image_chw: torch.Tensor, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image = torch.clamp(image_chw, 0.0, 1.0).squeeze(0).mul(255.0).byte().cpu().numpy()
    Image.fromarray(image, mode="L").save(out_path)


def load_cropped_image(image_path: Path, image_size: int) -> torch.Tensor:
    image = Image.open(image_path).convert("L")
    tensor = torch.as_tensor(list(image.getdata()), dtype=torch.float32).reshape(image.height, image.width)
    tensor = tensor / 255.0
    return resize_2d(tensor, image_size)


def checkpoint_path_arg(checkpoint_args: dict[str, Any], name: str, fallback: Path) -> Path:
    value = checkpoint_args.get(name)
    if value is None:
        return fallback
    return Path(value)


def checkpoint_int_arg(checkpoint_args: dict[str, Any], name: str, fallback: int) -> int:
    value = checkpoint_args.get(name)
    if value is None:
        return fallback
    return int(value)


def checkpoint_float_arg(checkpoint_args: dict[str, Any], name: str, fallback: float) -> float:
    value = checkpoint_args.get(name)
    if value is None:
        return fallback
    return float(value)


def checkpoint_optional_int_arg(
    checkpoint_args: dict[str, Any],
    name: str,
    fallback: int | None,
) -> int | None:
    value = checkpoint_args.get(name)
    if value is None:
        return fallback
    return int(value)


def choose_dataset_sample_index(
    dataset_len: int,
    args: argparse.Namespace,
    checkpoint_args: dict[str, Any],
    build_split_indices: Any,
) -> tuple[int, str]:
    if args.sample_index is not None:
        if args.sample_index >= dataset_len:
            raise IndexError(
                f"--sample-index {args.sample_index} is out of range for dataset with {dataset_len} samples."
            )
        return args.sample_index, "explicit"

    checkpoint_max_samples = checkpoint_args.get("max_samples")
    trained_on_full_dataset = "max_samples" in checkpoint_args and checkpoint_max_samples is None
    if trained_on_full_dataset:
        val_ratio = checkpoint_float_arg(checkpoint_args, "val_ratio", 0.2)
        test_ratio = checkpoint_float_arg(checkpoint_args, "test_ratio", 0.2)
        split_seed = checkpoint_int_arg(checkpoint_args, "seed", 42)
        _, _, test_idx = build_split_indices(dataset_len, val_ratio, test_ratio, split_seed)
        if not test_idx:
            raise RuntimeError("Checkpoint split produced an empty test set.")
        selection_seed = (
            args.random_seed
            if args.random_seed is not None
            else random.SystemRandom().randint(0, 2**32 - 1)
        )
        return random.Random(selection_seed).choice(test_idx), "random_test"

    return 0, "default"


def texture_label(index: int | None) -> str | None:
    if index is None:
        return None
    return TEXTURE_CLASS_NAMES[index]


def malignancy_label(index: int | None) -> str | None:
    if index is None:
        return None
    return MALIGNANCY_CLASS_NAMES[index]


def make_sample_name(sample: dict[str, Any] | None, image_path: Path | None, task: str) -> str:
    if sample is not None:
        patient_id = str(sample.get("patient_id", "patient")).replace("/", "_")
        nodule_id = str(sample.get("nodule_id", "nodule")).replace("/", "_")
        uid = str(sample.get("target_uid", "slice")).replace("/", "_")
        return f"{task}_{patient_id}_{nodule_id}_{uid}"
    if image_path is not None:
        return f"{task}_{image_path.stem}"
    return task


def write_result(result: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


def print_label_block(result: dict[str, Any]) -> None:
    print(f"task: {result['task']}")
    print(f"input_image_saved: {result['preprocessed_image_path']}")
    print(f"labels_saved: {result['labels_path']}")
    print("ground_truth:")
    for key, value in result["ground_truth"].items():
        print(f"  {key}: {value}")
    print("predicted:")
    for key, value in result["predicted"].items():
        print(f"  {key}: {value}")


def infer_multitask(args: argparse.Namespace, device: torch.device) -> dict[str, Any]:
    checkpoint = load_checkpoint(args.model_path, device)
    checkpoint_args = checkpoint.get("args", {})
    cross_talk = args.cross_talk or checkpoint_args.get("cross_talk", "cross_stitch")
    image_size = args.image_size or int(checkpoint_args.get("image_size", 128))

    model = MultiTaskCrossTalkNet(cross_talk=cross_talk).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    image, sample, ground_truth = load_input_for_task(
        task="multitask",
        args=args,
        checkpoint_args=checkpoint_args,
        image_size=image_size,
    )
    with torch.no_grad():
        texture_logits, malignancy_logits = model(image.unsqueeze(0).to(device))
        texture_probs = F.softmax(texture_logits, dim=1).squeeze(0).cpu()
        malignancy_probs = F.softmax(malignancy_logits, dim=1).squeeze(0).cpu()

    texture_pred = int(torch.argmax(texture_probs).item())
    malignancy_pred = int(torch.argmax(malignancy_probs).item())
    return build_result(
        task="multitask",
        args=args,
        image=image,
        sample=sample,
        ground_truth=ground_truth,
        predicted={
            "texture_index": texture_pred,
            "texture_label": texture_label(texture_pred),
            "texture_probabilities": {
                name: float(texture_probs[idx].item()) for idx, name in enumerate(TEXTURE_CLASS_NAMES)
            },
            "malignancy_index": malignancy_pred,
            "malignancy_label": malignancy_label(malignancy_pred),
            "malignancy_probabilities": {
                name: float(malignancy_probs[idx].item()) for idx, name in enumerate(MALIGNANCY_CLASS_NAMES)
            },
        },
    )


def infer_texture(args: argparse.Namespace, device: torch.device) -> dict[str, Any]:
    checkpoint = load_checkpoint(args.model_path, device)
    checkpoint_args = checkpoint.get("args", {})
    image_size = args.image_size or int(checkpoint_args.get("image_size", 128))

    model = TextureOnlyNet().to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    image, sample, ground_truth = load_input_for_task(
        task="texture",
        args=args,
        checkpoint_args=checkpoint_args,
        image_size=image_size,
    )
    with torch.no_grad():
        logits = model(image.unsqueeze(0).to(device))
        probs = F.softmax(logits, dim=1).squeeze(0).cpu()

    pred = int(torch.argmax(probs).item())
    return build_result(
        task="texture",
        args=args,
        image=image,
        sample=sample,
        ground_truth=ground_truth,
        predicted={
            "texture_index": pred,
            "texture_label": texture_label(pred),
            "texture_probabilities": {
                name: float(probs[idx].item()) for idx, name in enumerate(TEXTURE_CLASS_NAMES)
            },
        },
    )


def infer_malignancy(args: argparse.Namespace, device: torch.device) -> dict[str, Any]:
    checkpoint = load_checkpoint(args.model_path, device)
    checkpoint_args = checkpoint.get("args", {})
    image_size = args.image_size or int(checkpoint_args.get("image_size", 128))

    model = MalignancyOnlyNet().to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    image, sample, ground_truth = load_input_for_task(
        task="malignancy",
        args=args,
        checkpoint_args=checkpoint_args,
        image_size=image_size,
    )
    with torch.no_grad():
        logits = model(image.unsqueeze(0).to(device))
        probs = F.softmax(logits, dim=1).squeeze(0).cpu()

    pred = int(torch.argmax(probs).item())
    return build_result(
        task="malignancy",
        args=args,
        image=image,
        sample=sample,
        ground_truth=ground_truth,
        predicted={
            "malignancy_index": pred,
            "malignancy_label": malignancy_label(pred),
            "malignancy_probabilities": {
                name: float(probs[idx].item()) for idx, name in enumerate(MALIGNANCY_CLASS_NAMES)
            },
        },
    )


def load_input_for_task(
    task: str,
    args: argparse.Namespace,
    checkpoint_args: dict[str, Any],
    image_size: int,
) -> tuple[torch.Tensor, dict[str, Any] | None, dict[str, Any]]:
    if args.image_path is not None:
        image = load_cropped_image(args.image_path, image_size)
        ground_truth: dict[str, Any] = {
            "note": "not provided for image input; pass --texture-label and/or --malignancy-label if known",
        }
        if task in ("multitask", "texture"):
            ground_truth["texture_label"] = args.texture_label
        if task in ("multitask", "malignancy"):
            ground_truth["malignancy_index"] = args.malignancy_label
            ground_truth["malignancy_label"] = malignancy_label(args.malignancy_label)
        return image, None, ground_truth

    if task == "texture":
        dataset = LIDCTextureFrameDataset(
            csv_path=checkpoint_path_arg(checkpoint_args, "csv_path", args.csv_path),
            uid_choice=checkpoint_args.get("uid_choice", args.uid_choice),
            image_size=image_size,
            roi_margin=checkpoint_int_arg(checkpoint_args, "roi_margin", args.roi_margin),
            max_samples=checkpoint_optional_int_arg(checkpoint_args, "max_samples", args.max_samples),
        )
        sample_index, sample_source = choose_dataset_sample_index(
            len(dataset), args, checkpoint_args, build_texture_split_indices
        )
        image, texture_onehot = dataset[sample_index]
        texture_index = int(torch.argmax(texture_onehot).item())
        ground_truth = {
            "sample_index": sample_index,
            "sample_source": sample_source,
            "texture_index": texture_index,
            "texture_label": texture_label(texture_index),
        }
        return image, dataset.samples[sample_index], ground_truth

    if task == "malignancy":
        dataset = LIDCMalignancyFrameDataset(
            csv_path=checkpoint_path_arg(checkpoint_args, "csv_path", args.csv_path),
            uid_choice=checkpoint_args.get("uid_choice", args.uid_choice),
            image_size=image_size,
            roi_margin=checkpoint_int_arg(checkpoint_args, "roi_margin", args.roi_margin),
            max_samples=checkpoint_optional_int_arg(checkpoint_args, "max_samples", args.max_samples),
        )
        sample_index, sample_source = choose_dataset_sample_index(
            len(dataset), args, checkpoint_args, build_malignancy_split_indices
        )
        image, malignancy = dataset[sample_index]
        malignancy_index = int(malignancy.item())
        ground_truth = {
            "sample_index": sample_index,
            "sample_source": sample_source,
            "malignancy_index": malignancy_index,
            "malignancy_label": malignancy_label(malignancy_index),
        }
        return image, dataset.samples[sample_index], ground_truth

    dataset = LIDCNoduleFrameDataset(
        csv_path=checkpoint_path_arg(checkpoint_args, "csv_path", args.csv_path),
        uid_choice=checkpoint_args.get("uid_choice", args.uid_choice),
        image_size=image_size,
        roi_margin=checkpoint_int_arg(checkpoint_args, "roi_margin", args.roi_margin),
        max_samples=checkpoint_optional_int_arg(checkpoint_args, "max_samples", args.max_samples),
    )
    sample_index, sample_source = choose_dataset_sample_index(
        len(dataset), args, checkpoint_args, build_multitask_split_indices
    )
    image, texture_onehot, malignancy = dataset[sample_index]
    texture_index = int(torch.argmax(texture_onehot).item())
    malignancy_index = int(malignancy.item())
    ground_truth = {
        "sample_index": sample_index,
        "sample_source": sample_source,
        "texture_index": texture_index,
        "texture_label": texture_label(texture_index),
        "malignancy_index": malignancy_index,
        "malignancy_label": malignancy_label(malignancy_index),
    }
    return image, dataset.samples[sample_index], ground_truth


def build_result(
    task: str,
    args: argparse.Namespace,
    image: torch.Tensor,
    sample: dict[str, Any] | None,
    ground_truth: dict[str, Any],
    predicted: dict[str, Any],
) -> dict[str, Any]:
    sample_name = make_sample_name(sample, args.image_path, task)
    image_path = args.out_dir / f"{sample_name}_preprocessed.png"
    labels_path = args.out_dir / f"{sample_name}_labels.json"
    save_preprocessed_image(image, image_path)

    result = {
        "task": task,
        "model_path": str(args.model_path),
        "source_image_path": str(args.image_path) if args.image_path is not None else str(sample["frame_path"]),
        "preprocessed_image_path": str(image_path),
        "labels_path": str(labels_path),
        "sample": serialize_sample(sample),
        "ground_truth": ground_truth,
        "predicted": predicted,
    }
    write_result(result, labels_path)
    return result


def serialize_sample(sample: dict[str, Any] | None) -> dict[str, Any] | None:
    if sample is None:
        return None
    return {key: str(value) if isinstance(value, Path) else value for key, value in sample.items()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run inference with the saved multitask, texture-only, or malignancy-only model. "
            "By default, full-dataset checkpoints sample a random held-out test item from --csv-path and apply "
            "the same DICOM crop/normalize/resize pipeline as training, so ground-truth labels are available. "
            "Use --sample-index to force a dataset item, or --image-path for an already cropped grayscale image."
        )
    )
    parser.add_argument("--task", choices=["multitask", "texture", "malignancy"], default="multitask")
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--csv-path", type=Path, default=DEFAULT_CSV)
    parser.add_argument(
        "--sample-index",
        type=int,
        default=None,
        help=(
            "Dataset index to run. If omitted for a checkpoint trained with --max-samples None, "
            "a random sample is selected from the checkpoint's held-out test split."
        ),
    )
    parser.add_argument("--random-seed", type=int, default=None)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--uid-choice", choices=["first", "middle", "last"], default="middle")
    parser.add_argument("--roi-margin", type=int, default=8)
    parser.add_argument("--image-size", type=int, default=None)
    parser.add_argument("--cross-talk", choices=["cross_stitch", "co_attention"], default=None)
    parser.add_argument(
        "--image-path",
        type=Path,
        default=None,
        help="Already cropped grayscale image. Ground truth can be supplied with --texture-label/--malignancy-label.",
    )
    parser.add_argument(
        "--use-csv-sample",
        action="store_true",
        help="Load --sample-index from --csv-path using the training preprocessing pipeline. This is the default.",
    )
    parser.add_argument("--texture-label", choices=TEXTURE_CLASS_NAMES, default=None)
    parser.add_argument("--malignancy-label", type=int, choices=[0, 1], default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    if args.use_csv_sample:
        args.image_path = None
    if args.model_path is None:
        defaults = {
            "multitask": DEFAULT_MULTITASK_MODEL,
            "texture": DEFAULT_TEXTURE_MODEL,
            "malignancy": DEFAULT_MALIGNANCY_MODEL,
        }
        args.model_path = defaults[args.task]
    if args.sample_index is not None and args.sample_index < 0:
        raise ValueError("--sample-index must be >= 0.")
    return args


def main() -> None:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if args.task == "texture":
        result = infer_texture(args, device)
    elif args.task == "malignancy":
        result = infer_malignancy(args, device)
    else:
        result = infer_multitask(args, device)
    print_label_block(result)


if __name__ == "__main__":
    main()
