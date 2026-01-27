"""
File validation utilities for passport photo generator.
"""
import os
import io
from typing import Union
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from PIL import Image

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MIN_IMAGE_DIMENSION = 100  # pixels
MAX_IMAGE_DIMENSION = 10000  # pixels


def validate_image_file(file: UploadedFile) -> bool:
    """
    Validate uploaded image file.
    
    Args:
        file: Django UploadedFile object
        
    Raises:
        ValidationError: If file is invalid with specific error message
        
    Returns:
        True if validation passes
    """
    # Check extension
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '{ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check size
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(
            f"File too large ({file.size / (1024*1024):.1f}MB). "
            f"Maximum size: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )
    
    # Verify it's actually an image and check dimensions
    try:
        # Read file content into memory to avoid issues with closed files
        file.seek(0) if hasattr(file, 'seek') else None
        file_content = file.read()
        file.seek(0) if hasattr(file, 'seek') else None
        
        # Verify it's a valid image
        img = Image.open(io.BytesIO(file_content))
        img.verify()
        
        # Reopen to get dimensions (verify() invalidates the image)
        img = Image.open(io.BytesIO(file_content))
        width, height = img.size
        img.close()
        
        # Check dimensions
        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            raise ValidationError(
                f"Image too small ({width}x{height}px). "
                f"Minimum dimension: {MIN_IMAGE_DIMENSION}px"
            )
        
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            raise ValidationError(
                f"Image too large ({width}x{height}px). "
                f"Maximum dimension: {MAX_IMAGE_DIMENSION}px"
            )
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid or corrupted image file: {str(e)}")
    
    return True


def validate_numeric_field(
    value: Union[str, int, float], 
    field_name: str,
    min_val: float,
    max_val: float,
    default: float
) -> float:
    """
    Validate and convert numeric field with bounds checking.
    
    Args:
        value: Value to validate (can be string, int, or float)
        field_name: Name of field for error messages
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        default: Default value to return if validation fails
    
    Returns:
        Validated float value
        
    Raises:
        ValidationError: If value is out of bounds
    """
    try:
        num_val = float(value)
        
        if num_val < min_val or num_val > max_val:
            raise ValidationError(
                f"{field_name} must be between {min_val} and {max_val}. "
                f"Got: {num_val}"
            )
        
        return num_val
        
    except (ValueError, TypeError):
        return default


def validate_copies_list(copies_list: list, num_photos: int) -> list:
    """
    Validate and sanitize copies list.
    
    Args:
        copies_list: List of copy counts (may be strings)
        num_photos: Expected number of photos
    
    Returns:
        List of validated integer copy counts
    """
    validated = []
    
    for i, val in enumerate(copies_list):
        try:
            copies = int(val)
            if copies < 1:
                copies = 1
            elif copies > 100:  # Reasonable limit
                raise ValidationError(f"Too many copies requested for photo {i+1}: {copies}. Maximum: 100")
            validated.append(copies)
        except (ValueError, TypeError):
            validated.append(1)
    
    # Pad with defaults if needed
    while len(validated) < num_photos:
        validated.append(1)
    
    return validated