from decimal import Decimal, InvalidOperation

from django.db import transaction
from import_export import fields, resources
from import_export.results import Error, Result, RowResult

from .models import LocationData

HEADER_ALIASES = {
    'geonameid': 'geo_name_id',
    'cityname': 'city',
    'sortorder': 'sort_order',
}
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
IMPORT_BATCH_SIZE = 500


class LocationDataResource(resources.ModelResource):
    geo_name_id = fields.Field(attribute='geo_name_id', column_name='geo_name_id')
    city = fields.Field(attribute='city', column_name='city')
    state = fields.Field(attribute='state', column_name='state')
    country = fields.Field(attribute='country', column_name='country')
    latitude = fields.Field(attribute='latitude', column_name='latitude')
    longitude = fields.Field(attribute='longitude', column_name='longitude')
    timezone = fields.Field(attribute='timezone', column_name='timezone')
    sort_order = fields.Field(attribute='sort_order', column_name='sort_order')
    display_name = fields.Field(attribute='display_name', column_name='display_name')

    class Meta:
        model = LocationData
        import_id_fields = ('geo_name_id',)
        fields = (
            'geo_name_id',
            'city',
            'state',
            'country',
            'latitude',
            'longitude',
            'timezone',
            'sort_order',
            'display_name',
        )
        export_order = fields
        skip_unchanged = True
        batch_size = IMPORT_BATCH_SIZE

    def before_import(self, dataset, **kwargs):
        dataset.headers = [
            HEADER_ALIASES.get(header.strip().strip('\ufeff').lower(), header.strip().strip('\ufeff').lower())
            for header in dataset.headers
        ]
        return super().before_import(dataset, **kwargs)

    def before_import_row(self, row, **kwargs):
        row = {
            (key.strip().strip('\ufeff') if key else key): value
            for key, value in row.items()
        }
        for legacy_name, field_name in HEADER_ALIASES.items():
            if legacy_name in row and field_name not in row:
                row[field_name] = row[legacy_name]
        return super().before_import_row(row, **kwargs)

    def _row_to_instance(self, row):
        return LocationData(
            geo_name_id=int(row['geo_name_id']),
            city=(row.get('city') or '').strip(),
            state=(row.get('state') or '').strip(),
            country=(row.get('country') or '').strip(),
            latitude=Decimal(str(row['latitude'])),
            longitude=Decimal(str(row['longitude'])),
            timezone=(row.get('timezone') or '').strip(),
            sort_order=int(row.get('sort_order') or 1),
            display_name=(row.get('display_name') or '').strip().strip('"'),
        )

    def import_data(self, dataset, dry_run=False, raise_errors=False, **kwargs):
        """Bulk upsert rows in batches to avoid request timeouts on large files."""
        self.before_import(dataset, **kwargs)
        self._check_import_id_fields(dataset.headers)

        result = Result()
        result.total_rows = len(dataset)
        instances = []
        row_index_map = []

        for row_number, data_row in enumerate(dataset, 1):
            row = dict(zip(dataset.headers, data_row))
            row_result = RowResult()
            try:
                self.before_import_row(row, row_number=row_number, **kwargs)
                instance = self._row_to_instance(row)
                instances.append(instance)
                row_index_map.append(row_number)
                row_result.import_type = RowResult.IMPORT_TYPE_UPDATE
            except (KeyError, ValueError, InvalidOperation, TypeError) as exc:
                row_result.import_type = RowResult.IMPORT_TYPE_ERROR
                row_result.errors.append(Error(exc, row=row, number=row_number))
                result.append_error_row(row_number, row, row_result.errors)
                if raise_errors:
                    raise exc
            result.increment_row_result_total(row_result)
            if not row_result.errors:
                result.append_row_result(row_result)

        if dry_run or not instances:
            return result

        db_connection = self.get_db_connection_name()
        with transaction.atomic(using=db_connection):
            for start in range(0, len(instances), IMPORT_BATCH_SIZE):
                batch = instances[start:start + IMPORT_BATCH_SIZE]
                LocationData.objects.using(db_connection).bulk_create(
                    batch,
                    update_conflicts=True,
                    update_fields=UPDATE_FIELDS,
                    unique_fields=['geo_name_id'],
                )

        return result
