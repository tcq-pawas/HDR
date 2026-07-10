#!/usr/bin/env python
"""
Script to import or update location data from CSV file
Reads location_data_without_id.csv and updates/creates LocationData records

Usage:
    python import_location_data.py                    # Uses default CSV file
    python import_location_data.py path/to/file.csv  # Uses custom CSV file

Features:
    - Creates new LocationData records if GeoNameID doesn't exist
    - Updates existing records if GeoNameID matches
    - Uses update_or_create for efficient database operations
    - Provides detailed progress output with emojis
    - Shows summary of created/updated/error counts
"""

import os
import sys
import csv
import django

# Setup Django environment BEFORE any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HeyDayRealty.settings')
django.setup()

from Apps.PublicPage.models import LocationData


def import_location_data(csv_file_path='location_data_without_id.csv'):
    """
    Import or update location data from CSV file
    Uses GeoNameID as unique identifier for update_or_create
    """
    
    # If file path is not absolute, look in project root
    if not os.path.isabs(csv_file_path):
        csv_file_path = os.path.join(os.path.dirname(__file__), csv_file_path)
    
    if not os.path.exists(csv_file_path):
        print(f'❌ CSV file not found at: {csv_file_path}')
        return False
    
    print(f'📂 Importing location data from: {csv_file_path}')
    print('=' * 60)
    
    created_count = 0
    updated_count = 0
    error_count = 0
    total_rows = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Print the headers to debug
            print(f'📋 CSV Headers: {reader.fieldnames}')
            
            for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                total_rows += 1
                try:
                    # Check if GeoNameID exists in the row
                    if 'GeoNameID' not in row:
                        print(f'❌ Row {row_num} missing GeoNameID. Available keys: {list(row.keys())}')
                        error_count += 1
                        continue
                    
                    geo_name_id = int(row['GeoNameID'])
                    
                    # Check if record exists and update or create
                    location_data, created = LocationData.objects.update_or_create(
                        geo_name_id=geo_name_id,
                        defaults={
                            'city': row['City'],
                            'state': row['State'],
                            'country': row['Country'],
                            'latitude': float(row['Latitude']),
                            'longitude': float(row['Longitude']),
                            'timezone': row['Timezone'],
                            'sort_order': int(row['SortOrder']),
                            'display_name': row['DisplayName'].strip('"')
                        }
                    )
                    
                    if created:
                        created_count += 1
                        print(f'✅ Created: {location_data.city}, {location_data.state} (ID: {geo_name_id})')
                    else:
                        updated_count += 1
                        print(f'🔄 Updated: {location_data.city}, {location_data.state} (ID: {geo_name_id})')
                
                except Exception as e:
                    error_count += 1
                    print(f'❌ Error processing row {row_num}: {str(e)}')
                    print(f'   Row data: {row}')
    
    except Exception as e:
        print(f'❌ Failed to read CSV file: {str(e)}')
        return False
    
    # Summary
    print('\n' + '=' * 60)
    print('📊 IMPORT SUMMARY')
    print('=' * 60)
    print(f'  Total rows processed: {total_rows}')
    print(f'  Created: {created_count}')
    print(f'  Updated: {updated_count}')
    print(f'  Errors: {error_count}')
    print('=' * 60)
    
    if error_count > 0:
        print(f'⚠️  Import completed with {error_count} error(s)')
    else:
        print('🎉 Import completed successfully!')
    
    return error_count == 0


if __name__ == '__main__':
    print('🚀 Starting Location Data Import...')
    print('=' * 60)
    
    # Allow custom file path as command line argument
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'location_data_without_id.csv'
    
    success = import_location_data(csv_file)
    
    print('\n' + '=' * 60)
    print('IMPORT COMPLETE')
    print('=' * 60)
    
    if success:
        print('✅ Location data import completed successfully!')
        print('\nYou can now use LocationData in your application.')
    else:
        print('❌ Location data import encountered errors.')
        print('Please review the error messages above.')
    
    sys.exit(0 if success else 1)
