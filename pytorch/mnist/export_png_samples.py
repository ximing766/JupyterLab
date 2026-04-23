import argparse
import os
from collections import defaultdict

from torchvision import datasets


def export_mnist_pngs(data_root: str, out_dir: str, train: bool, per_class: int) -> str:
    os.makedirs(out_dir, exist_ok=True)
    dataset = datasets.MNIST(root=data_root, train=train, download=False)

    picked = defaultdict(int)
    written = 0
    labels_path = os.path.join(out_dir, "labels.txt")

    with open(labels_path, "w", encoding="utf-8") as f:
        for idx in range(len(dataset)):
            img, label = dataset[idx]
            if picked[label] >= per_class:
                if len(picked) == 10 and all(v >= per_class for v in picked.values()):
                    break
                continue

            filename = f"{label}_{idx:05d}.png"
            img_path = os.path.join(out_dir, filename)
            img.save(img_path)
            f.write(f"{filename}\t{label}\n")

            picked[label] += 1
            written += 1

    return labels_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"),
        help="MNIST root directory (contains MNIST/raw). Default: ./data next to this script.",
    )
    parser.add_argument(
        "--out-dir",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples"),
        help="Output directory for exported PNGs.",
    )
    parser.add_argument(
        "--split",
        choices=["train", "test"],
        default="test",
        help="Which split to export from.",
    )
    parser.add_argument(
        "--per-class",
        type=int,
        default=10,
        help="How many images to export for each digit class (0-9).",
    )
    args = parser.parse_args()

    labels_path = export_mnist_pngs(
        data_root=args.data_root,
        out_dir=args.out_dir,
        train=(args.split == "train"),
        per_class=args.per_class,
    )
    print(f"Exported PNG samples to: {args.out_dir}")
    print(f"Labels saved to: {labels_path}")


if __name__ == "__main__":
    main()
