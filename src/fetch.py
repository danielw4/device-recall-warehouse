"""Download the three openFDA bulk archives used by this project."""

import json
import urllib.request
from pathlib import Path


MANIFEST_URL = "https://api.fda.gov/download.json"
DATASETS = {
    "recall": "device-recall.json.zip",
    "510k": "device-510k.json.zip",
    "classification": "device-classification.json.zip",
}


def main() -> None:
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(MANIFEST_URL) as response:
        manifest = json.load(response)

    device = manifest["results"]["device"]
    for dataset, filename in DATASETS.items():
        destination = raw_dir / filename
        if destination.exists():
            print(f"skip {destination}")
            continue
        partitions = device[dataset]["partitions"]
        if len(partitions) != 1:
            raise RuntimeError(f"expected one {dataset} partition, found {len(partitions)}")
        url = partitions[0]["file"]
        partial = destination.with_suffix(destination.suffix + ".part")
        print(f"download {url} -> {destination}")
        urllib.request.urlretrieve(url, partial)
        partial.replace(destination)


if __name__ == "__main__":
    main()
