"""Turn copied Domain 'Sold listings' pages into the project dataset.

Collection method: each results page was viewed in a browser, selected with Ctrl+A and
copied into data/raw_<suburb>_p<n>.txt. This script reads those text files and extracts one
record per sold listing. No automated access to Domain is involved - the text comes from
pages already loaded in the browser.

Usage:
    python parse_domain.py            # parse data/raw_*.txt -> data/sydney_properties.csv
    python parse_domain.py --preview  # show what would be extracted, write nothing
"""
import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).parent / "data"
OUT = DATA / "sydney_properties.csv"
SUBURBS = ["Bondi", "Chatswood", "Penrith"]

COLUMNS = ["property_id", "suburb", "address", "property_type", "bedrooms", "bathrooms",
           "car_spaces", "land_size_sqm", "internal_area_sqm", "sale_price", "sale_date",
           "sale_method", "days_on_market", "distance_to_station_km", "agent_description",
           "listing_url", "agent_agency"]

TYPE_MAP = {
    "apartment / unit / flat": "Apartment",
    "apartment": "Apartment",
    "studio": "Apartment",
    "penthouse": "Apartment",
    "new apartments / off the plan": "Apartment",
    "house": "House",
    "semi-detached": "Semi",
    "duplex": "Duplex",
    "terrace": "Semi",
    "townhouse": "Townhouse",
    "villa": "Villa",
    "acreage / semi-rural": "House",
}

RE_PRICE = re.compile(r"^\$([\d,]+)$")
RE_SOLD = re.compile(r"^Sold\s+(.*?)\s+(\d{1,2} [A-Za-z]{3} \d{4})$")
RE_BEDS = re.compile(r"^(\d+)\s*Beds?$", re.I)
RE_BATHS = re.compile(r"^(\d+)\s*Baths?$", re.I)
RE_PARK = re.compile(r"^(\d+)\s*Parking$", re.I)
RE_LAND = re.compile(r"^([\d,]+(?:\.\d+)?)\s*m²$", re.I)
RE_ADDR = re.compile(r"^(.+),\s*(" + "|".join(SUBURBS) + r")$")


def sale_method(raw: str) -> str:
    low = raw.lower()
    if "private treaty" in low:
        return "Private treaty"
    if "auction" in low:
        return "Auction"
    return ""


def parse_file(path: Path) -> tuple[list[dict], int]:
    """Return (records, withheld_count) for one copied page."""
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()]

    # A listing runs from one "Sold <method> <date>" line to just before the next one.
    anchors = [i for i, ln in enumerate(lines) if RE_SOLD.match(ln)]
    records, withheld = [], 0

    for n, start in enumerate(anchors):
        end = anchors[n + 1] if n + 1 < len(anchors) else len(lines)
        block = lines[start:end]

        m = RE_SOLD.match(block[0])
        method_raw, date_raw = m.group(1), m.group(2)

        addr = suburb = None
        for ln in block:
            a = RE_ADDR.match(ln)
            if a:
                addr, suburb = a.group(1).strip(), a.group(2)
                break
        if not addr:
            continue

        price = None
        for ln in block:
            p = RE_PRICE.match(ln)
            if p:
                price = int(p.group(1).replace(",", ""))
                break
        if price is None:
            withheld += 1
            continue

        # Attributes sit in the short run of lines between the address and the property
        # type. Bounding the scan keeps the last listing on a page from reading the
        # page footer, which also contains bare dashes and bed counts.
        addr_i = next(i for i, ln in enumerate(block) if RE_ADDR.match(ln))
        window = block[addr_i + 1: addr_i + 10]

        # The counts always appear in the order beds, baths, parking, and Domain prints a
        # bare dash for any of them that is nil - a studio shows a dash for bedrooms, an
        # apartment without a space shows one for parking. So the dashes are resolved by
        # position rather than assumed to be parking. Nil is read as zero rather than
        # unknown; see the data quality discussion in Part 1.
        land = ptype = None
        seq = []
        for ln in window:
            if (b := RE_BEDS.match(ln)):
                seq.append(("beds", int(b.group(1))))
            elif (b := RE_BATHS.match(ln)):
                seq.append(("baths", int(b.group(1))))
            elif (b := RE_PARK.match(ln)):
                seq.append(("park", int(b.group(1))))
            elif (b := RE_LAND.match(ln)):
                land = float(b.group(1).replace(",", ""))
            elif ln in {"−", "-", "–"}:
                seq.append((None, 0))
            elif ln.lower() in TYPE_MAP:
                ptype = TYPE_MAP[ln.lower()]
                break

        slots = {}
        order = ["beds", "baths", "park"]
        for label, value in seq:
            if label is None:
                label = next((k for k in order if k not in slots), None)
                if label is None:
                    continue
            slots[label] = value
        beds, baths, park = slots.get("beds"), slots.get("baths"), slots.get("park")

        if baths is None or ptype is None:
            continue

        records.append({
            "suburb": suburb,
            "address": addr,
            "property_type": ptype,
            "bedrooms": beds if beds is not None else 0,
            "bathrooms": baths,
            "car_spaces": park if park is not None else "",
            "land_size_sqm": land if land is not None else "",
            "internal_area_sqm": "",
            "sale_price": price,
            "sale_date": datetime.strptime(date_raw, "%d %b %Y").strftime("%Y-%m-%d"),
            "sale_method": sale_method(method_raw),
            "days_on_market": "",
            "distance_to_station_km": "",
            "agent_description": "",
            "listing_url": "",
            # The agency banner precedes the "Sold ..." anchor, so it sits just
            # above this block rather than inside it.
            "agent_agency": (lines[start - 2] if start >= 2
                             and lines[start - 1].startswith("Agent - ") else ""),
        })

    return records, withheld


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="show results without writing")
    args = ap.parse_args()

    raw_files = sorted(DATA.glob("raw_*.txt"))
    if not raw_files:
        print(f"No raw_*.txt files in {DATA}", file=sys.stderr)
        return 1

    all_rows, total_withheld = [], 0
    print(f"{'file':28} {'usable':>7} {'withheld':>9} {'yield':>7}")
    print("-" * 55)
    for f in raw_files:
        rows, withheld = parse_file(f)
        total_withheld += withheld
        seen = len(rows) + withheld
        print(f"{f.name:28} {len(rows):7d} {withheld:9d} {len(rows)/seen*100 if seen else 0:6.0f}%")
        all_rows.extend(rows)

    before = len(all_rows)
    deduped, seen_addr = [], set()
    for r in all_rows:
        key = (r["suburb"], r["address"].lower())
        if key not in seen_addr:
            seen_addr.add(key)
            deduped.append(r)

    print("-" * 55)
    print(f"{'TOTAL':28} {before:7d} {total_withheld:9d}")
    if before != len(deduped):
        print(f"removed {before - len(deduped)} duplicate address(es) across pages")

    for i, r in enumerate(deduped, 1):
        r["property_id"] = i

    print("\nPer suburb:")
    for s in SUBURBS:
        n = sum(r["suburb"] == s for r in deduped)
        print(f"  {s:12} {n:4d}   {'OK' if n >= 30 else f'need {30 - n} more'}")
    print(f"\n  TOTAL        {len(deduped):4d}   "
          f"{'OK' if len(deduped) >= 100 else f'need {100 - len(deduped)} more'}")

    if deduped:
        prices = sorted(r["sale_price"] for r in deduped)
        print(f"\nPrice range ${prices[0]:,} to ${prices[-1]:,}, "
              f"median ${prices[len(prices) // 2]:,}")
        dates = sorted(r["sale_date"] for r in deduped)
        print(f"Sales from {dates[0]} to {dates[-1]}")
        land = sum(1 for r in deduped if r["land_size_sqm"] != "")
        print(f"Land size present for {land} of {len(deduped)} properties")

    if args.preview:
        print("\n--preview: nothing written")
        return 0

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(deduped)
    print(f"\nwrote {OUT} ({len(deduped)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
