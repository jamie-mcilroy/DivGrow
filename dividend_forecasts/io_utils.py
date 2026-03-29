import csv
import json
import os


def ensure_parent_dir(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_json(path):
    with open(path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


def load_csv_rows(path, encoding="utf-8-sig"):
    with open(path, "r", newline="", encoding=encoding) as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv_rows(path, header, rows):
    ensure_parent_dir(path)
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)
        writer.writerows(rows)


def get_year_columns(fieldnames):
    return sorted(int(fieldname) for fieldname in fieldnames if fieldname.isdigit())

