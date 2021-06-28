import json
from pathlib import Path


def main() -> None:
    for stem in ["comments", "requests", "releases", "featured"]:
        input_path = Path("data") / f"{stem}.json"
        output_path = Path("data") / f"{stem}.jsonl"
        items = json.loads(input_path.read_text(encoding="utf-8"))
        output_path.write_text("\n".join(json.dumps(item) for item in items))


if __name__ == "__main__":
    main()
