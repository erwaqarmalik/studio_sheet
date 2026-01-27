"""
Quick setup script for Passport Photo Generator
Helps with initial configuration and validation
"""
import os
import sys
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)

def check_python_version():
    """Check if Python version is compatible."""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print("✅ Python version compatible")
    return True

def check_env_file():
    """Check if .env file exists."""
    print_header("Checking Environment Configuration")
    
    if not os.path.exists('.env'):
        print("⚠️  .env file not found")
        print("\nCreating .env from .env.example...")
        
        if os.path.exists('.env.example'):
            # Copy example file
            with open('.env.example', 'r') as src:
                content = src.read()
            
            # Generate SECRET_KEY
            try:
                from django.core.management.utils import get_random_secret_key
                secret_key = get_random_secret_key()
                content = content.replace('your-secret-key-here-change-in-production', secret_key)
                content = content.replace('DEBUG=False', 'DEBUG=True')  # Dev default
            except ImportError:
                print("⚠️  Django not installed yet, using template")
            
            with open('.env', 'w') as dest:
                dest.write(content)
            
            print("✅ Created .env file with generated SECRET_KEY")
            print("   Note: DEBUG is set to True for development")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✅ .env file exists")
    
    return True

def check_dependencies():
    """Check if required packages are installed."""
    print_header("Checking Dependencies")
    
    required = {
        'django': 'Django',
        'PIL': 'Pillow',
        'reportlab': 'ReportLab',
        'decouple': 'python-decouple'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} missing")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("\nRun: pip install -r requirements.txt")
        return False
    
    return True

def check_directories():
    """Check if required directories exist."""
    print_header("Checking Directories")
    
    dirs = ['logs', 'media', 'media/uploads', 'media/outputs']
    
    for directory in dirs:
        path = Path(directory)
        if not path.exists():
            print(f"⚠️  Creating {directory}/")
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {directory}/")
        else:
            print(f"✅ {directory}/ exists")
    
    return True

def check_migrations():
    """Check if migrations are needed."""
    print_header("Checking Database")
    
    if not os.path.exists('db.sqlite3'):
        print("⚠️  Database not found")
        print("\nRun: python manage.py migrate")
        return False
    
    print("✅ Database file exists")
    print("   (Run 'python manage.py migrate' to ensure it's up to date)")
    return True

def run_tests():
    """Optionally run tests."""
    print_header("Running Tests")
    
    response = input("\nWould you like to run tests? (y/N): ").strip().lower()
    
    if response == 'y':
        print("\nRunning tests...")
        os.system('python manage.py test')
        return True
    else:
        print("Skipped tests. Run manually with: python manage.py test")
        return True

def print_next_steps():
    """Print next steps for the user."""
    print_header("Setup Complete!")
    
    print("\n🎉 Your passport photo generator is ready!")
    print("\nNext steps:")
    print("1. Review .env file and adjust settings if needed")
    print("2. Run migrations: python manage.py migrate")
    print("3. Start dev server: python manage.py runserver")
    print("4. Visit: http://localhost:8000")
    print("\nFor production deployment:")
    print("- See README_NEW.md for detailed instructions")
    print("- See DEPLOYMENT_NOTES.md for production configs")
    print("- Set up file cleanup: python manage.py cleanup_old_files")
    print("\nDocumentation:")
    print("- README_NEW.md - Full documentation")
    print("- CHANGELOG.md - Recent improvements")
    print("- IMPLEMENTATION_SUMMARY.md - Quick reference")

def main():
    """Run all checks."""
    print("\n🚀 Passport Photo Generator - Quick Setup")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment Config", check_env_file),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Database", check_migrations),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error during {name} check: {e}")
            results.append((name, False))
    
    # Summary
    print_header("Setup Summary")
    
    all_passed = True
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
        if not result:
            all_passed = False
    
    if all_passed:
        # Optionally run tests
        run_tests()
        print_next_steps()
    else:
        print("\n⚠️  Some checks failed. Please resolve the issues above.")
        print("   Then run this script again or proceed manually.")

if __name__ == '__main__':
    main()
