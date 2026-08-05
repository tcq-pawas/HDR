#!/usr/bin/env python
"""
Import or update location data from CSV into the LocationData table.
Uses batched bulk upsert for fast imports on large files.

Usage:
    python import_location_data.py
    python import_location_data.py path/to/file.csv
"""

import csv
import os
import sys
from decimal import Decimal
from pathlib import Path

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
DEFAULT_CSV_PATH = Path('Apps') / 'Administration' / 'location_data_without_id.csv'


def _default_csv_path():
    try:
        from django.conf import settings
        return Path(settings.BASE_DIR) / DEFAULT_CSV_PATH
    except Exception:
        return Path(__file__).resolve().parent / DEFAULT_CSV_PATH


def _normalize_row(row):
    normalized = {}
    for key, value in row.items():
        if key is None:
            continue
        key = key.strip().strip('\ufeff').lower()
        key = HEADER_ALIASES.get(key, key)
        normalized[key] = (value or '').strip().strip('"')
    return normalized


def _row_to_instance(row, location_model):
    return location_model(
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


def import_location_data(csv_file_path=None):
    from django.db import transaction
    from Apps.PublicPage.models import LocationData

    if csv_file_path is None:
        csv_file_path = _default_csv_path()
    else:
        csv_file_path = Path(csv_file_path)
        if not csv_file_path.is_absolute():
            csv_file_path = Path(__file__).resolve().parent / csv_file_path

    if not csv_file_path.exists():
        return {
            'success': False,
            'message': f'CSV file not found at: {csv_file_path}',
            'total_rows': 0,
            'upserted': 0,
            'errors': 0,
        }

    instances = []
    error_count = 0
    total_rows = 0
    error_details = []

    with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        headers = reader.fieldnames

        for row_num, row in enumerate(reader, start=2):
            total_rows += 1
            try:
                normalized = _normalize_row(row)
                if not normalized.get('geo_name_id'):
                    raise ValueError('missing geo_name_id')
                instances.append(_row_to_instance(normalized, LocationData))
            except Exception as exc:
                error_count += 1
                if len(error_details) < 10:
                    error_details.append({'row': row_num, 'error': str(exc)})

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

    return {
        'success': error_count == 0,
        'message': 'Location data imported successfully.' if error_count == 0 else 'Import completed with errors.',
        'file': str(csv_file_path),
        'headers': headers,
        'total_rows': total_rows,
        'upserted': len(instances),
        'errors': error_count,
        'error_details': error_details,
    }


if __name__ == '__main__':
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
    django.setup()

    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    result = import_location_data(csv_file)
    print(result)
    sys.exit(0 if result['success'] else 1)
