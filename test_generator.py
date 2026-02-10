"""
Test script for generate_pdf and generate_jpeg functions
Usage: python test_generator.py <image_path>
"""

import sys
import os
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'passport_app.settings')
django.setup()

from generator.utils import generate_pdf, generate_jpeg, remove_background
import shutil


def test_pdf_generation(image_path, output_dir="test_output"):
    """Test PDF generation with various configurations"""
    print("\n" + "="*60)
    print("TESTING PDF GENERATION")
    print("="*60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Test configurations
    test_configs = [
        {
            "name": "A4 Portrait - 2 copies with full cut lines",
            "paper_size": "A4",
            "orientation": "portrait",
            "margin_cm": 1.0,
            "col_gap_cm": 0.5,
            "row_gap_cm": 0.5,
            "cut_lines": True,
            "cut_line_style": "crosshair",
            "copies": 2,
        },
        {
            "name": "A4 Landscape - 3 copies without cut lines",
            "paper_size": "A4",
            "orientation": "landscape",
            "margin_cm": 1.5,
            "col_gap_cm": 0.3,
            "row_gap_cm": 0.3,
            "cut_lines": False,
            "cut_line_style": "full",
            "copies": 3,
        },
        {
            "name": "Letter Portrait - 1 copy with crosshair cut lines",
            "paper_size": "Letter",
            "orientation": "portrait",
            "margin_cm": 1.0,
            "col_gap_cm": 0.5,
            "row_gap_cm": 0.5,
            "cut_lines": True,
            "cut_line_style": "crosshair",
            "copies": 1,
        },
    ]
    
    results = []
    for config in test_configs:
        print(f"\nTest: {config['name']}")
        print("-" * 60)
        
        try:
            copies_map = {image_path: config['copies']}
            
            pdf_path = generate_pdf(
                photos=[image_path],
                copies_map=copies_map,
                paper_size=config['paper_size'],
                orientation=config['orientation'],
                margin_cm=config['margin_cm'],
                col_gap_cm=config['col_gap_cm'],
                row_gap_cm=config['row_gap_cm'],
                cut_lines=config['cut_lines'],
                output_dir=output_dir,
                cut_line_style=config.get('cut_line_style', 'full'),
            )
            
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path) / 1024  # KB
                print(f"✓ SUCCESS: Generated {os.path.basename(pdf_path)}")
                print(f"  Size: {file_size:.2f} KB")
                print(f"  Path: {pdf_path}")
                results.append((config['name'], True, pdf_path))
            else:
                print(f"✗ FAILED: File not created")
                results.append((config['name'], False, None))
                
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            results.append((config['name'], False, None))
    
    return results


def test_jpeg_generation(image_path, output_dir="test_output"):
    """Test JPEG generation with various configurations"""
    print("\n" + "="*60)
    print("TESTING JPEG GENERATION")
    print("="*60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Test configurations
    test_configs = [
        {
            "name": "A4 Portrait - 4 copies with full cut lines",
            "paper_size": "A4",
            "orientation": "portrait",
            "margin_cm": 1.0,
            "col_gap_cm": 0.5,
            "row_gap_cm": 0.5,
            "cut_lines": True,
            "cut_line_style": "full",
            "copies": 4,
        },
        {
            "name": "A4 Landscape - 6 copies without cut lines",
            "paper_size": "A4",
            "orientation": "landscape",
            "margin_cm": 1.5,
            "col_gap_cm": 0.3,
            "row_gap_cm": 0.3,
            "cut_lines": False,
            "cut_line_style": "full",
            "copies": 6,
        },
        {
            "name": "A3 Portrait - 8 copies with crosshair cut lines",
            "paper_size": "A3",
            "orientation": "portrait",
            "margin_cm": 1.0,
            "col_gap_cm": 0.5,
            "row_gap_cm": 0.5,
            "cut_lines": True,
            "cut_line_style": "crosshair",
            "copies": 8,
        },
    ]
    
    results = []
    for config in test_configs:
        print(f"\nTest: {config['name']}")
        print("-" * 60)
        
        try:
            copies_map = {image_path: config['copies']}
            
            jpeg_paths = generate_jpeg(
                photos=[image_path],
                copies_map=copies_map,
                paper_size=config['paper_size'],
                orientation=config['orientation'],
                margin_cm=config['margin_cm'],
                col_gap_cm=config['col_gap_cm'],
                row_gap_cm=config['row_gap_cm'],
                cut_lines=config['cut_lines'],
                output_dir=output_dir,
                cut_line_style=config.get('cut_line_style', 'full'),
            )
            
            if jpeg_paths:
                total_size = sum(os.path.getsize(p) / 1024 for p in jpeg_paths)
                print(f"✓ SUCCESS: Generated {len(jpeg_paths)} page(s)")
                print(f"  Total size: {total_size:.2f} KB")
                for i, path in enumerate(jpeg_paths, 1):
                    size = os.path.getsize(path) / 1024
                    print(f"  Page {i}: {os.path.basename(path)} ({size:.2f} KB)")
                results.append((config['name'], True, jpeg_paths))
            else:
                print(f"✗ FAILED: No files created")
                results.append((config['name'], False, None))
                
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            results.append((config['name'], False, None))
    
    return results


def test_background_removal(image_path, output_dir="test_output"):
    """Test background removal with different background colors"""
    print("\n" + "="*60)
    print("TESTING BACKGROUND REMOVAL")
    print("="*60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Test configurations
    test_configs = [
        {
            "name": "White background (#FFFFFF)",
            "bg_color": "#FFFFFF",
        },
        {
            "name": "Light blue background (#E0F0FF)",
            "bg_color": "#E0F0FF",
        },
        {
            "name": "Light gray background (#F0F0F0)",
            "bg_color": "#F0F0F0",
        },
        {
            "name": "Cream background (#FFF8DC)",
            "bg_color": "#FFF8DC",
        },
    ]
    
    results = []
    for i, config in enumerate(test_configs, 1):
        print(f"\nTest {i}: {config['name']}")
        print("-" * 60)
        
        try:
            # Create a copy of the image for testing
            test_image_name = f"bg_removed_{config['bg_color'].replace('#', '')}.jpg"
            test_image_path = os.path.join(output_dir, test_image_name)
            shutil.copy2(image_path, test_image_path)
            
            original_size = os.path.getsize(test_image_path) / 1024
            print(f"  Original size: {original_size:.2f} KB")
            print(f"  Removing background with {config['bg_color']}...")
            
            # Perform background removal
            success = remove_background(test_image_path, config['bg_color'])
            
            if success and os.path.exists(test_image_path):
                processed_size = os.path.getsize(test_image_path) / 1024
                print(f"✓ SUCCESS: Background removed")
                print(f"  Processed size: {processed_size:.2f} KB")
                print(f"  Output: {test_image_path}")
                results.append((config['name'], True, test_image_path))
            else:
                print(f"✗ FAILED: Background removal unsuccessful")
                results.append((config['name'], False, None))
                
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((config['name'], False, None))
    
    # Test with invalid color
    print(f"\nTest {len(test_configs) + 1}: Invalid color format (should fail gracefully)")
    print("-" * 60)
    try:
        test_image_path = os.path.join(output_dir, "bg_removed_invalid.jpg")
        shutil.copy2(image_path, test_image_path)
        success = remove_background(test_image_path, "invalid_color")
        if not success:
            print(f"✓ SUCCESS: Handled invalid color gracefully")
            results.append(("Invalid color handling", True, None))
        else:
            print(f"✗ FAILED: Should have rejected invalid color")
            results.append(("Invalid color handling", False, None))
    except Exception as e:
        print(f"✓ SUCCESS: Exception caught for invalid color - {str(e)}")
        results.append(("Invalid color handling", True, None))
    
    return results



def print_summary(pdf_results, jpeg_results, bg_results=None):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    print("\nPDF Generation:")
    pdf_passed = sum(1 for _, success, _ in pdf_results if success)
    print(f"  Passed: {pdf_passed}/{len(pdf_results)}")
    for name, success, _ in pdf_results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
    
    print("\nJPEG Generation:")
    jpeg_passed = sum(1 for _, success, _ in jpeg_results if success)
    print(f"  Passed: {jpeg_passed}/{len(jpeg_results)}")
    for name, success, _ in jpeg_results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
    
    total_passed = pdf_passed + jpeg_passed
    total_tests = len(pdf_results) + len(jpeg_results)
    
    if bg_results:
        print("\nBackground Removal:")
        bg_passed = sum(1 for _, success, _ in bg_results if success)
        print(f"  Passed: {bg_passed}/{len(bg_results)}")
        for name, success, _ in bg_results:
            status = "✓" if success else "✗"
            print(f"  {status} {name}")
        total_passed += bg_passed
        total_tests += len(bg_results)
    
    print(f"\nOverall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_generator.py <image_path> [--skip-bg]")
        print("\nExample:")
        print("  python test_generator.py media/uploads/test_photo.jpg")
        print("  python test_generator.py media/uploads/test_photo.jpg --skip-bg")
        print("\nOptions:")
        print("  --skip-bg    Skip background removal tests (faster)")
        sys.exit(1)
    
    image_path = sys.argv[1]
    skip_bg = "--skip-bg" in sys.argv
    
    # Validate image path
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    print("="*60)
    print("PHOTO GENERATOR TEST SUITE")
    print("="*60)
    print(f"Input image: {image_path}")
    print(f"Image size: {os.path.getsize(image_path) / 1024:.2f} KB")
    
    # Run tests
    pdf_results = test_pdf_generation(image_path)
    jpeg_results = test_jpeg_generation(image_path)
    
    bg_results = None
    if not skip_bg:
        print("\n⚠️  Background removal test may take 30-60 seconds on first run (model download)")
        print("    Use --skip-bg flag to skip these tests\n")
        bg_results = test_background_removal(image_path)
    else:
        print("\n⏭️  Skipping background removal tests (--skip-bg flag used)")
    
    # Print summary
    print_summary(pdf_results, jpeg_results, bg_results)
    
    print("\n" + "="*60)
    print(f"Test output saved to: {os.path.abspath('test_output')}")
    print("="*60)


if __name__ == "__main__":
    main()
