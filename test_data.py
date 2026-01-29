import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'passport_app.settings')
django.setup()

from generator.config import PHOTO_SIZES, PASSPORT_CONFIG

print('PHOTO_SIZES loaded:')
print(f'Number of presets: {len(PHOTO_SIZES)}')
print(f'Keys: {list(PHOTO_SIZES.keys())}')
print()
print('First size:', PHOTO_SIZES.get('passport_35x45'))
print()

# Test JSON serialization
try:
    photo_json = json.dumps(PHOTO_SIZES)
    config_json = json.dumps(PASSPORT_CONFIG)
    print('✓ Both objects are JSON serializable')
except Exception as e:
    print(f'✗ JSON serialization error: {e}')
