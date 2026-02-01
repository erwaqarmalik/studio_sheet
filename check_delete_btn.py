import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'passport_app.settings'

import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

if user:
    print(f"Testing with user: {user.username}")
    c = Client()
    c.force_login(user)
    r = c.get('/history/')
    
    html = r.content.decode()
    
    # Check for delete button
    if 'delete-btn' in html:
        print("✓ delete-btn FOUND in HTML")
        # Find and print a snippet
        idx = html.find('delete-btn')
        print("\nSnippet around delete-btn:")
        print(html[max(0, idx-200):idx+300])
    else:
        print("✗ delete-btn NOT FOUND in HTML")
        print(f"\nHTML length: {len(html)}")
        
    # Check for the generations loop
    if 'for gen in generations' in html or 'Recent Generations' in html:
        print("✓ Generations loop found")
    else:
        print("✗ Generations loop not found")
        
    # Count how many buttons expected
    download_count = html.count('Download')
    print(f"\nDownload buttons found: {download_count}")
else:
    print("No user found!")
