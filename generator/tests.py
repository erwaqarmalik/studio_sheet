"""
Unit tests for passport photo generator.
"""
import os
import tempfile
from pathlib import Path
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from PIL import Image
import io

from generator.models import PhotoGeneration
from generator.validators import (
    validate_image_file,
    validate_numeric_field,
    validate_copies_list,
)
from generator.utils import (
    calculate_grid,
    crop_to_passport_aspect_ratio,
    cm_to_px,
    resolve_paper_size,
    PAPER_SIZES,
)
from generator.config import PASSPORT_CONFIG


class ValidatorTests(TestCase):
    """Tests for file validators."""
    
    def create_test_image(self, width=800, height=600, format='JPEG'):
        """Helper to create a test image file."""
        img = Image.new('RGB', (width, height), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        return img_io
    
    def test_validate_image_file_success(self):
        """Test validation of valid image files."""
        img_data = self.create_test_image()
        uploaded_file = SimpleUploadedFile(
            "test.jpg",
            img_data.getvalue(),  # Use getvalue() instead of read()
            content_type="image/jpeg"
        )
        
        # Should not raise exception
        self.assertTrue(validate_image_file(uploaded_file))
    
    def test_validate_image_file_invalid_extension(self):
        """Test rejection of invalid file extensions."""
        img_data = self.create_test_image()
        uploaded_file = SimpleUploadedFile(
            "test.txt",
            img_data.getvalue(),
            content_type="text/plain"
        )
        
        with self.assertRaises(ValidationError) as context:
            validate_image_file(uploaded_file)
        
        self.assertIn('.txt', str(context.exception))
    
    def test_validate_image_file_too_large(self):
        """Test rejection of oversized files."""
        # Create a large fake file
        large_data = b'x' * (11 * 1024 * 1024)  # 11MB
        uploaded_file = SimpleUploadedFile(
            "test.jpg",
            large_data,
            content_type="image/jpeg"
        )
        
        with self.assertRaises(ValidationError) as context:
            validate_image_file(uploaded_file)
        
        self.assertIn('too large', str(context.exception).lower())
    
    def test_validate_image_file_too_small(self):
        """Test rejection of too small images."""
        img_data = self.create_test_image(width=50, height=50)
        uploaded_file = SimpleUploadedFile(
            "test.jpg",
            img_data.getvalue(),
            content_type="image/jpeg"
        )
        
        with self.assertRaises(ValidationError) as context:
            validate_image_file(uploaded_file)
        
        # Check for either 'too small' or dimension error
        error_msg = str(context.exception).lower()
        self.assertTrue('too small' in error_msg or '50' in error_msg)
    
    def test_validate_numeric_field_valid(self):
        """Test validation of valid numeric fields."""
        result = validate_numeric_field("2.5", "Test Field", 0.0, 5.0, 1.0)
        self.assertEqual(result, 2.5)
    
    def test_validate_numeric_field_out_of_range(self):
        """Test rejection of out-of-range values."""
        with self.assertRaises(ValidationError):
            validate_numeric_field("10.0", "Test Field", 0.0, 5.0, 1.0)
    
    def test_validate_numeric_field_invalid_returns_default(self):
        """Test that invalid input returns default value."""
        result = validate_numeric_field("invalid", "Test Field", 0.0, 5.0, 1.0)
        self.assertEqual(result, 1.0)
    
    def test_validate_copies_list(self):
        """Test validation of copies list."""
        copies = validate_copies_list(["2", "3", "1"], 3)
        self.assertEqual(copies, [2, 3, 1])
    
    def test_validate_copies_list_invalid_values(self):
        """Test handling of invalid copy values."""
        copies = validate_copies_list(["invalid", "-1", "2"], 3)
        self.assertEqual(copies, [1, 1, 2])
    
    def test_validate_copies_list_too_many(self):
        """Test rejection of excessive copy counts."""
        with self.assertRaises(ValidationError):
            validate_copies_list(["101"], 1)


class UtilsTests(TestCase):
    """Tests for utility functions."""
    
    def test_cm_to_px(self):
        """Test centimeter to pixel conversion."""
        result = cm_to_px(1.0, dpi=300)
        # 1 cm at 300 DPI should be approximately 118 pixels
        self.assertAlmostEqual(result, 118, delta=2)
    
    def test_resolve_paper_size_a4_portrait(self):
        """Test A4 portrait paper size resolution."""
        w_pt, h_pt, w_cm, h_cm = resolve_paper_size("A4", "portrait")
        self.assertEqual(w_cm, 21.0)
        self.assertEqual(h_cm, 29.7)
    
    def test_resolve_paper_size_a4_landscape(self):
        """Test A4 landscape paper size resolution."""
        w_pt, h_pt, w_cm, h_cm = resolve_paper_size("A4", "landscape")
        self.assertEqual(w_cm, 29.7)
        self.assertEqual(h_cm, 21.0)
    
    def test_calculate_grid(self):
        """Test grid calculation."""
        cols, rows = calculate_grid(
            paper_w_cm=21.0,
            paper_h_cm=29.7,
            margin=1.0,
            col_gap=0.5,
            row_gap=0.5
        )
        # Should fit multiple photos
        self.assertGreater(cols, 0)
        self.assertGreater(rows, 0)
    
    def test_calculate_grid_minimum_one(self):
        """Test that grid always returns at least 1x1."""
        cols, rows = calculate_grid(
            paper_w_cm=5.0,
            paper_h_cm=5.0,
            margin=2.0,
            col_gap=1.0,
            row_gap=1.0
        )
        self.assertEqual(cols, 1)
        self.assertEqual(rows, 1)
    
    def test_crop_to_passport_aspect_ratio(self):
        """Test image cropping to passport aspect ratio."""
        # Create temporary test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', (1000, 1000), color='blue')
            img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # Crop the image
            result = crop_to_passport_aspect_ratio(tmp_path)
            self.assertTrue(result)
            
            # Verify aspect ratio
            img = Image.open(tmp_path)
            width, height = img.size
            aspect_ratio = width / height
            target_ratio = 3.5 / 4.5  # 7:9
            img.close()
            
            # Allow small tolerance
            self.assertAlmostEqual(aspect_ratio, target_ratio, places=2)
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class ViewTests(TestCase):
    """Tests for views."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def create_test_image_file(self):
        """Create a valid test image file for upload."""
        img = Image.new('RGB', (800, 600), color='green')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        return SimpleUploadedFile(
            "test_photo.jpg",
            img_io.read(),
            content_type="image/jpeg"
        )
    
    def test_index_get(self):
        """Test GET request to index page (requires login)."""
        # Login required - should redirect to login
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
        # After login, should succeed
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'StudioSheet')
    
    def test_index_post_no_files(self):
        """Test POST with no files uploaded (requires login)."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post('/', {
            'paper_size': 'A4',
            'orientation': 'portrait',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No photos uploaded')
    
    def test_index_post_with_valid_file(self):
        """Test POST with valid image file (requires login)."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        test_file = self.create_test_image_file()
        
        response = self.client.post('/', {
            'photos': test_file,
            'paper_size': 'A4',
            'orientation': 'portrait',
            'margin_cm': '1.0',
            'col_gap_cm': '0.5',
            'row_gap_cm': '0.5',
            'cut_lines': 'yes',
            'output_type': 'PDF',
            'copies[]': ['1'],
        })
        
        self.assertEqual(response.status_code, 200)
        # Should contain download link or success message
        # Note: actual file generation might fail in test environment
    
    def test_index_post_invalid_numeric_values(self):
        """Test POST with invalid numeric values (requires login)."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        test_file = self.create_test_image_file()
        
        response = self.client.post('/', {
            'photos': test_file,
            'paper_size': 'A4',
            'margin_cm': 'invalid',
            'col_gap_cm': '-5',
            'output_type': 'PDF',
        })
        
        # Should not crash, should use defaults
        self.assertEqual(response.status_code, 200)


class ConfigTests(TestCase):
    """Tests for configuration."""
    
    def test_passport_config_exists(self):
        """Test that passport config is properly defined."""
        self.assertIn('photo_width_cm', PASSPORT_CONFIG)
        self.assertIn('photo_height_cm', PASSPORT_CONFIG)
        self.assertIn('default_paper_size', PASSPORT_CONFIG)
    
    def test_passport_dimensions(self):
        """Test passport photo dimensions."""
        self.assertEqual(PASSPORT_CONFIG['photo_width_cm'], 3.5)
        self.assertEqual(PASSPORT_CONFIG['photo_height_cm'], 4.5)
    
    def test_paper_sizes_defined(self):
        """Test that standard paper sizes are defined."""
        self.assertIn('A4', PAPER_SIZES)
        self.assertIn('A3', PAPER_SIZES)
        self.assertIn('Letter', PAPER_SIZES)
        
        # Verify structure
        a4 = PAPER_SIZES['A4']
        self.assertIn('width_cm', a4)
        self.assertIn('height_cm', a4)


class AuthenticationTests(TestCase):
    """Tests for user authentication."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_login_page_loads(self):
        """Test login page loads correctly."""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign In')
    
    def test_login_success(self):
        """Test successful login."""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
        
        # User should be authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_failure(self):
        """Test login with wrong password."""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign In')
    
    def test_logout(self):
        """Test user logout."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Logout
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 302)


class PhotoGenerationModelTests(TestCase):
    """Tests for PhotoGeneration model."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_generation_with_user(self):
        """Test creating a generation record for authenticated user."""
        gen = PhotoGeneration.objects.create(
            user=self.user,
            session_id='test123',
            num_photos=3,
            paper_size='A4',
            orientation='portrait',
            output_type='PDF',
            output_path='/media/outputs/test123/file.pdf',
            output_url='/media/outputs/test123/file.pdf',
            file_size_bytes=1024,
            total_copies=9,
        )
        
        self.assertEqual(gen.user, self.user)
        self.assertEqual(gen.num_photos, 3)
        self.assertEqual(gen.paper_size, 'A4')
    
    def test_create_generation_anonymous(self):
        """Test creating a generation record for anonymous user."""
        gen = PhotoGeneration.objects.create(
            user=None,
            session_id='anon123',
            num_photos=1,
            paper_size='Letter',
            orientation='landscape',
            output_type='JPEG',
            output_path='/media/outputs/anon123/file.jpg',
            output_url='/media/outputs/anon123/file.jpg',
        )
        
        self.assertIsNone(gen.user)
        self.assertEqual(gen.session_id, 'anon123')
    
    def test_get_file_size_display(self):
        """Test file size display formatting."""
        gen = PhotoGeneration.objects.create(
            session_id='size_test',
            num_photos=1,
            output_path='/test/path',
            output_url='/test/url',
            file_size_bytes=1536,  # 1.5 KB
        )
        
        size_display = gen.get_file_size_display()
        self.assertIn('KB', size_display)
    
    def test_ordering(self):
        """Test that generations are ordered by creation date (newest first)."""
        gen1 = PhotoGeneration.objects.create(
            session_id='first',
            num_photos=1,
            output_path='/test/1',
            output_url='/test/1',
        )
        gen2 = PhotoGeneration.objects.create(
            session_id='second',
            num_photos=1,
            output_path='/test/2',
            output_url='/test/2',
        )
        
        generations = list(PhotoGeneration.objects.all())
        self.assertEqual(generations[0], gen2)
        self.assertEqual(generations[1], gen1)


class HistoryViewTests(TestCase):
    """Tests for history view."""
    
    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
    
    def test_history_requires_login(self):
        """Test that history page requires authentication."""
        response = self.client.get('/history/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_history_page_loads_for_authenticated_user(self):
        """Test history page loads for logged in user."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/history/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Photo Generation History')
    
    def test_history_displays_user_generations(self):
        """Test that history page shows user's generations."""
        # Create generation for user
        PhotoGeneration.objects.create(
            user=self.user,
            session_id='test123',
            num_photos=2,
            paper_size='A4',
            orientation='portrait',
            output_type='PDF',
            output_path='/test/file.pdf',
            output_url='/test/file.pdf',
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/history/')
        
        self.assertContains(response, 'PDF Generation')
        self.assertContains(response, '2')  # Check for the number
    
    def test_history_statistics(self):
        """Test that statistics are calculated correctly."""
        # Create multiple generations
        PhotoGeneration.objects.create(
            user=self.user,
            session_id='test1',
            num_photos=2,
            output_type='PDF',
            output_path='/test/1.pdf',
            output_url='/test/1.pdf',
            total_copies=4,
        )
        PhotoGeneration.objects.create(
            user=self.user,
            session_id='test2',
            num_photos=3,
            output_type='JPEG',
            output_path='/test/2.jpg',
            output_url='/test/2.jpg',
            total_copies=6,
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/history/')
        
        # Check statistics
        self.assertContains(response, '2')  # Total generations
        self.assertContains(response, '5')  # Total photos (2+3)


class ProfileViewTests(TestCase):
    """Tests for profile view."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
    
    def test_profile_requires_login(self):
        """Test that profile page requires authentication."""
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 302)
    
    def test_profile_page_loads(self):
        """Test profile page loads for authenticated user."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/profile/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'test@example.com')
