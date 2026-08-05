from import_export import fields, resources

from .models import LocationData


class LocationDataResource(resources.ModelResource):
    geo_name_id = fields.Field(column_name='geonameid', attribute='geo_name_id')
    city = fields.Field(column_name='cityname', attribute='city')
    state = fields.Field(column_name='state', attribute='state')
    country = fields.Field(column_name='country', attribute='country')
    latitude = fields.Field(column_name='latitude', attribute='latitude')
    longitude = fields.Field(column_name='longitude', attribute='longitude')
    timezone = fields.Field(column_name='timezone', attribute='timezone')
    sort_order = fields.Field(column_name='sortorder', attribute='sort_order')
    display_name = fields.Field(column_name='display_name', attribute='display_name')

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
