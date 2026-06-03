"""Convert Notion-exported feedback HTML tables to data/override_examples.json."""

from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class CellTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        return "".join(self.parts).strip()


def extract_cell_text(html_fragment: str) -> str:
    parser = CellTextExtractor()
    parser.feed(html_fragment)
    return parser.get_text()


def parse_confidence(raw: str) -> int | None:
    value = raw.strip()
    if not value:
        return None
    match = re.match(r"^(\d+)\s*%?$", value)
    if match:
        return int(match.group(1))
    raise ValueError(f"Unexpected confidence value: {raw!r}")


def parse_html_file(path: Path, source: str) -> tuple[list[dict], int]:
    html = path.read_text(encoding="utf-8")
    tbody_match = re.search(r"<tbody>(.*?)</tbody>", html, re.DOTALL)
    if not tbody_match:
        raise ValueError(f"No tbody found in {path}")

    rows_html = re.findall(r"<tr[^>]*>(.*?)</tr>", tbody_match.group(1), re.DOTALL)
    items: list[dict] = []
    for row_html in rows_html:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL)
        if len(cells) != 6:
            raise ValueError(f"Expected 6 cells, got {len(cells)} in {path}")

        id_raw, title_html, rec_html, final_html, conf_html, note_html = cells
        items.append(
            {
                "id": int(extract_cell_text(id_raw)),
                "title": extract_cell_text(title_html),
                "recommended_visual": extract_cell_text(rec_html),
                "final_visual": extract_cell_text(final_html),
                "confidence": parse_confidence(extract_cell_text(conf_html)),
                "note": extract_cell_text(note_html),
                "source": source,
            }
        )
    return items, len(rows_html)


def confidence_distribution(items: list[dict]) -> dict[str, int]:
    return {
        "ge_90": sum(1 for x in items if x["confidence"] is not None and x["confidence"] >= 90),
        "70_89": sum(
            1 for x in items if x["confidence"] is not None and 70 <= x["confidence"] <= 89
        ),
        "lt_70": sum(1 for x in items if x["confidence"] is not None and x["confidence"] < 70),
        "none": sum(1 for x in items if x["confidence"] is None),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--html",
        action="append",
        nargs=2,
        metavar=("PATH", "SOURCE"),
        required=True,
        help="HTML export path and source tag (repeatable)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/override_examples.json"),
    )
    args = parser.parse_args()

    all_items: list[dict] = []
    row_counts: dict[str, int] = {}
    for path_str, source in args.html:
        path = Path(path_str)
        items, count = parse_html_file(path, source)
        row_counts[path.name] = count
        all_items.extend(items)

    required = {
        "id",
        "title",
        "recommended_visual",
        "final_visual",
        "confidence",
        "note",
        "source",
    }
    for index, item in enumerate(all_items):
        missing = required - set(item)
        if missing:
            raise ValueError(f"Item {index} missing fields: {missing}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(all_items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    json.loads(args.output.read_text(encoding="utf-8"))

    dist = confidence_distribution(all_items)
    print("Row counts per HTML:", row_counts)
    print("Total items:", len(all_items))
    print(f"confidence >= 90 : {dist['ge_90']}건")
    print(f"confidence 70~89 : {dist['70_89']}건")
    print(f"confidence < 70 : {dist['lt_70']}건")
    print(f"confidence 없음 : {dist['none']}건")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
