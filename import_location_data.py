#!/usr/bin/env python
"""
Script to import or update location data from CSV file.
Uses batched bulk upsert for fast imports on large files.

Usage:
    python import_location_data.py                    # Uses default CSV file
    python import_location_data.py path/to/file.csv  # Uses custom CSV file
"""

import csv
import os
import sys
from decimal import Decimal

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
django.setup()

from django.db import transaction

from Apps.PublicPage.models import LocationData

BATCH_SIZE = 500
UPDATE_FIELDS = [
    'city',
    'state',
    'country',
    'latitude',
    'longitude',
    'timezone',
    'sort_order',
    'display_name',
]
HEADER_ALIASES = {
    'geonameid': 'geo_name_id',
    'cityname': 'city',
    'sortorder': 'sort_order',
}


def _normalize_row(row):
    normalized = {}
    for key, value in row.items():
        if key is None:
            continue
        key = key.strip().strip('\ufeff').lower()
        key = HEADER_ALIASES.get(key, key)
        normalized[key] = (value or '').strip().strip('"')
    return normalized


def _row_to_instance(row):
    return LocationData(
        geo_name_id=int(row['geo_name_id']),
        city=row['city'],
        state=row['state'],
        country=row['country'],
        latitude=Decimal(str(row['latitude'])),
        longitude=Decimal(str(row['longitude'])),
        timezone=row['timezone'],
        sort_order=int(row.get('sort_order') or 1),
        display_name=row['display_name'],
    )


def import_location_data(csv_file_path='location_data_without_id.csv'):
    if not os.path.isabs(csv_file_path):
        csv_file_path = os.path.join(os.path.dirname(__file__), csv_file_path)

    if not os.path.exists(csv_file_path):
        print(f'CSV file not found at: {csv_file_path}')
        return False

    print(f'Importing location data from: {csv_file_path}')
    instances = []
    error_count = 0
    total_rows = 0

    with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        print(f'CSV headers: {reader.fieldnames}')

        for row_num, row in enumerate(reader, start=2):
            total_rows += 1
            try:
                normalized = _normalize_row(row)
                if not normalized.get('geo_name_id'):
                    raise ValueError('missing geo_name_id')
                instances.append(_row_to_instance(normalized))
            except Exception as exc:
                error_count += 1
                print(f'Error on row {row_num}: {exc}')

    if instances:
        with transaction.atomic():
            for start in range(0, len(instances), BATCH_SIZE):
                batch = instances[start:start + BATCH_SIZE]
                LocationData.objects.bulk_create(
                    batch,
                    update_conflicts=True,
                    update_fields=UPDATE_FIELDS,
                    unique_fields=['geo_name_id'],
                )
                print(f'Imported rows {start + 1}-{start + len(batch)}')

    print('\nIMPORT SUMMARY')
    print(f'  Total rows processed: {total_rows}')
    print(f'  Upserted: {len(instances)}')
    print(f'  Errors: {error_count}')
    return error_count == 0


if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'location_data_without_id.csv'
    success = import_location_data(csv_file)
    sys.exit(0 if success else 1)
