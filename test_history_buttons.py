import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'passport_app.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

if user:
    client = Client()
    client.force_login(user)
    response = client.get('/history/')
    
    html = response.content.decode()
    
    print(f"Status: {response.status_code}")
    print(f"Response length: {len(html)}")
    print(f"delete-btn count: {html.count('delete-btn')}")
    print(f"Download count: {html.count('Download')}")
    print(f"restore-btn count: {html.count('restore-btn')}")
    print(f"Generations in context: {len(response.context['generations'])}")
    
    # Check if delete button HTML is present
    if 'class="btn btn-danger delete-btn"' in html:
        print("✓ Delete button HTML found!")
    else:
        print("✗ Delete button HTML NOT found")
        
    # Look for the button section
    if 'btn-group' in html:
        print(f"✓ btn-group found {html.count('btn-group')} times")
    else:
        print("✗ btn-group NOT found")
else:
    print("No user found in database")
