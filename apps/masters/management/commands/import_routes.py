import re
import uuid
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.masters.models import Event, RouteArea, RouteSubArea, Upashray


AREA_ORDER = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
]

AREA_NAMES = {
    "1": "City-ReliefRoad",
    "2": "Shahpur-Usmanpura",
    "3": "Naranpura-Thaltej",
    "4": "Vadaj-Subhashbridge",
    "5": "KrishnaNagar-Naroda",
    "6": "Jivrajpark-Satellite",
    "7": "Vasna-NewVasna",
    "8": "Paldi-ChandraNagar",
    "9": "Shahibag-Girdharnagar-HathisinhniVadi",
    "10": "Sabarmati-Ranip-Chandkheda-Ramol",
}

SUMMARY_GROUPS = {
    "1": [("A", "Astodia-Manekchowk", 1), ("B", "GandhiRoad-ReliefRoad", 2)],
    "2": [("A", "Shahpur-Khanpur", 1), ("B", "Usmanpura-Shantinagar-Navrangpura", 2)],
    "3": [("A", "Nehrunagar-DadaSahebPagla", 1), ("B", "Devkinandan-Mirambika-Ankur-Vijaynagar", 2),
          ("C", "ZaveriPark-Naranpura", 3), ("D", "Parasnagar-Chitrakoot-Pragatinagar-Parulnagar", 4),
          ("E", "Nirnaynagar-Chankyapuri-Ghatlodia-Sattadhar-Thaltej-Gurukul", 5)],
    "4": [("A", "Nava-Vadaj-JunaVadaj-Nandanvan-TulsiShyam-SubhashBridge", 1)],
    "5": [("A", "Krishnanagar-Naroda", 1), ("B", "Mahasukhnagar-Bapunagar-Saraspur", 2),
          ("C", "Odhav-Nikol-Jantangar-Isanpur", 3)],
    "6": [("A", "Satellite-Jivrajpark-Vejalpur", 1), ("B", "Vastrapur-SGHighway-Prernatirth", 2)],
    "7": [("A", "Godavari-Ayojannagar", 1), ("B", "Navkar-DharmRishiTirthVatika-Narayannagar", 2),
          ("C", "Rangsagar-Shantivan", 3), ("D", "Laxmivihar-JainMerchant-JethabhaiPark", 4)],
    "8": [("A", "Opera", 1), ("B", "Vasantkunj-Jainnagar-Parimal", 2),
          ("C", "VikasgruhRoad", 3), ("D", "Dashaporvad", 4),
          ("E", "JainSociety-Kunthunath", 5), ("F", "Pankaj-RajNagar", 6)],
    "9": [("A", "Shahibag-Girdharnagar-HathisinhniVadi", 1)],
    "10": [("A", "Sabarmati-Ranip-Chandkheda-Ramol", 1)],
}

OTHER_GROUPS = [
    ("Sarkhej", 1),
    ("Gota", 2),
    ("Bopal-SouthBopal-Shela", 3),
    ("Maninagar", 4),
    ("Sanand", 5),
]


def _parse_numbered_item(line):
    parts = line.strip().split(". ", 1)
    if len(parts) == 2 and parts[0].isdigit():
        num = int(parts[0])
        name = parts[1].strip()
        has_sadhu = "સાધુ" in line or "સાધ્વીજી" in line
        return num, name, has_sadhu
    return None, None, False


def _build_upashray_name(num, raw_name, area_num, sub_code):
    clean = re.sub(r"\s*\(.*?\)\s*", "", raw_name).strip()
    clean = re.sub(r"\s*–\s*", " - ", clean).strip()
    return clean or raw_name.strip()


def _import_group(area, sub_area, lines, event, created_count):
    for line in lines:
        line = line.strip()
        if not line or line == "---" or line.startswith("#"):
            continue
        num, raw_name, _ = _parse_numbered_item(line)
        if num is None:
            continue
        upashray_name = _build_upashray_name(num, raw_name, area.display_code, sub_area.display_code)
        existing = Upashray.objects.filter(event=event, name__iexact=upashray_name).first()
        if existing:
            if existing.sub_area_id is None:
                existing.sub_area = sub_area
                existing.save(update_fields=["sub_area"])
            continue
        Upashray.objects.create(
            event=event,
            name=upashray_name,
            sub_area=sub_area,
            area=f"Area {area.display_code}{sub_area.display_code}",
        )
        created_count[0] += 1


class Command(BaseCommand):
    help = "Import upashray routes data from routes_data.txt"

    def add_arguments(self, parser):
        parser.add_argument("--event", type=int, help="Event PK to assign upashray to")
        parser.add_argument("--file", type=str, default="routes_data.txt", help="Path to routes data file")

    def handle(self, *args, **options):
        filepath = Path(options["file"])
        if not filepath.exists():
            self.stderr.write(f"File not found: {filepath}")
            return

        event_pk = options["event"]
        event = None
        if event_pk:
            event = Event.objects.filter(pk=event_pk).first()
            if not event:
                self.stderr.write(f"Event with PK {event_pk} not found")
                return
        if not event:
            event = Event.objects.filter(is_current=True, is_active=True).first()
            if not event:
                self.stderr.write("No current event found. Provide --event PK.")
                return

        self.stdout.write(f"Using event: {event}")

        content = filepath.read_text(encoding="utf-8")

        self._ensure_route_areas()
        self._import_main_areas(content, event)
        self._import_other_areas(content, event)

        total = Upashray.objects.filter(event=event).count()
        self.stdout.write(self.style.SUCCESS(f"Done. Total upashray for this event: {total}"))

    def _ensure_route_areas(self):
        for code in AREA_ORDER:
            RouteArea.objects.get_or_create(
                display_code=code,
                defaults={"name": AREA_NAMES[code], "display_order": int(code)},
            )
        RouteArea.objects.get_or_create(
            display_code="11",
            defaults={"name": "Other Areas", "display_order": 11},
        )

    def _ensure_sub_area(self, area, sub_code, sub_name, order):
        sub, _ = RouteSubArea.objects.get_or_create(
            route_area=area,
            display_code=sub_code,
            defaults={"name": sub_name, "display_order": order},
        )
        return sub

    def _import_main_areas(self, content, event):
        created = [0]
        lines = content.splitlines()
        area_code = None
        sub_code = None
        sub_lines = []
        sub_name = None

        def _do_flush():
            nonlocal area_code, sub_code, sub_lines, sub_name
            if not sub_lines:
                return
            a = RouteArea.objects.filter(display_code=area_code).first()
            if not a:
                return
            sc = sub_code or "A"
            sn = sub_name or a.name
            so = int(sc) if sc.isdigit() else (ord(sc) - 64)
            sub = self._ensure_sub_area(a, sc, sn, so)
            _import_group(a, sub, sub_lines, event, created)
            sub_lines = []

        def _set_area(code, sc, name):
            nonlocal area_code, sub_code, sub_lines, sub_name
            _do_flush()
            area_code = code
            sub_code = sc
            sub_name = name
            sub_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            m = re.match(r"^##\s*Area\s*-\s*(\d+)\s*\(([A-Z])\)\s*:", line)
            if m:
                _set_area(m.group(1), m.group(2), line.split(":", 1)[1].strip() if ":" in line else "")
                i += 1
                continue

            m = re.match(r"^##\s*Area\s*-\s*(\d+)\s*:", line)
            if m:
                _set_area(m.group(1), "", line.split(":", 1)[1].strip() if ":" in line else "")
                i += 1
                continue

            if re.match(r"^-{3,}$", line):
                _do_flush()
                i += 1
                continue

            if re.match(r"^###\s+", line):
                _do_flush()
                i += 1
                continue

            if re.match(r"^##\s*(સરખેજ|ગોતા|બોપલ|મણીનગર|સાણંદ)", line):
                _do_flush()
                area_code = None
                i += 1
                continue

            if re.match(r"^#\s*$|^#\s*=", line):
                i += 1
                continue

            if re.match(r"^##\s*Additional", line):
                i += 1
                continue

            if re.match(r"^\d+\.\s+", line) and area_code:
                sub_lines.append(line)

            i += 1

        _do_flush()
        self.stdout.write(f"Created {created[0]} new upashray from main areas")

    def _import_other_areas(self, content, event):
        created = [0]
        other_area = RouteArea.objects.filter(display_code="11").first()
        if not other_area:
            return

        other_blocks = {
            "Sarkhej": [],
            "Gota": [],
            "Bopal": [],
            "Maninagar": [],
            "Sanand": [],
        }

        lines = content.splitlines()
        current_section = None
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("## સરખેજ"):
                current_section = "Sarkhej"
                i += 1
                continue
            elif line.startswith("## ગોતા"):
                current_section = "Gota"
                i += 1
                continue
            elif line.startswith("## બોપલ"):
                current_section = "Bopal"
                i += 1
                continue
            elif line.startswith("## મણીનગર"):
                current_section = "Maninagar"
                i += 1
                continue
            elif line.startswith("## સાણંદ"):
                current_section = "Sanand"
                i += 1
                continue

            if current_section and re.match(r"^\d+\.\s+", line):
                other_blocks.setdefault(current_section, []).append(line)

            if re.match(r"^-{3,}$", line) and current_section:
                current_section = None

            i += 1

        for section_name, block_lines in other_blocks.items():
            if not block_lines:
                continue
            sub, _ = RouteSubArea.objects.get_or_create(
                route_area=other_area,
                display_code="",
                defaults={"name": section_name, "display_order": 1},
            )
            for line in block_lines:
                num, raw_name, _ = _parse_numbered_item(line)
                if num is None:
                    continue
                upashray_name = _build_upashray_name(num, raw_name, "11", "OT")
                existing = Upashray.objects.filter(event=event, name__iexact=upashray_name).first()
                if existing:
                    if existing.sub_area_id is None:
                        existing.sub_area = sub
                        existing.save(update_fields=["sub_area"])
                    continue
                Upashray.objects.create(
                    event=event,
                    name=upashray_name,
                    sub_area=sub,
                    area=f"Other - {section_name}",
                )
                created[0] += 1

        self.stdout.write(f"Created {created[0]} new upashray from other areas")
