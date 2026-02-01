"""
API views for background removal and other image processing.
"""
import io
import base64
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from PIL import Image

logger = logging.getLogger('generator')

# Check if rembg is available on startup
REMBG_AVAILABLE = False
try:
    from rembg import remove
    REMBG_AVAILABLE = True
    logger.info("rembg library is available")
except ImportError as e:
    logger.warning(f"rembg library not available: {e}. Background removal will be disabled.")


@csrf_exempt
@require_http_methods(["POST"])
def remove_background_api(request):
    """
    API endpoint for AI-powered background removal.
    Accepts base64 encoded image and background color, returns processed image.
    """
    # Check if rembg is available
    if not REMBG_AVAILABLE:
        logger.error("Background removal requested but rembg is not installed")
        return JsonResponse({
            'error': 'Background removal service is not available. Please contact support.',
            'success': False
        }, status=503)  # Service Unavailable
    
    try:
        # Get image data from request
        image_data = request.POST.get('image')
        bg_color = request.POST.get('bg_color', '#FFFFFF')
        
        if not image_data:
            logger.error("No image data provided in request")
            return JsonResponse({'error': 'No image data provided'}, status=400)
        
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_data)
            if len(image_bytes) == 0:
                logger.error("Decoded image is empty")
                return JsonResponse({'error': 'Invalid image data'}, status=400)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            return JsonResponse({'error': 'Invalid image format'}, status=400)
        
        # Process image with rembg
        try:
            logger.info(f"Processing image, size: {len(image_bytes)} bytes")
            output_bytes = remove(image_bytes)
            logger.info(f"Background removed, output size: {len(output_bytes)} bytes")
        except Exception as e:
            logger.error(f"rembg processing failed: {e}", exc_info=True)
            return JsonResponse({
                'error': 'Failed to process image. The AI model may be downloading on first use. Please try again in a moment.',
                'success': False
            }, status=503)  # Service Unavailable
        
        # Open as PIL Image
        try:
            img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
        except Exception as e:
            logger.error(f"Failed to open processed image: {e}")
            return JsonResponse({'error': 'Failed to process image'}, status=500)
        
        # Convert hex color to RGB with validation
        hex_color = bg_color.lstrip('#').strip().upper()
        
        # Validate hex color format
        if len(hex_color) != 6:
            logger.error(f"Invalid hex color format: {bg_color} (cleaned: {hex_color})")
            return JsonResponse({
                'error': f'Invalid color format: {bg_color}. Expected format: #RRGGBB'
            }, status=400)
        
        try:
            bg_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            logger.info(f"Parsed color {bg_color} to RGB: {bg_rgb}")
        except ValueError as e:
            logger.error(f"Failed to parse hex color {bg_color}: {e}")
            return JsonResponse({
                'error': f'Invalid hex color: {bg_color}. Use format #RRGGBB (e.g., #FFFFFF)'
            }, status=400)
        
        # Create new image with solid background
        try:
            background = Image.new("RGB", img.size, bg_rgb)
            background.paste(img, (0, 0), img)
        except Exception as e:
            logger.error(f"Failed to create background: {e}")
            return JsonResponse({'error': 'Failed to apply background color'}, status=500)
        
        # Convert to base64
        try:
            output_buffer = io.BytesIO()
            background.save(output_buffer, format='JPEG', quality=95, subsampling=0)
            output_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
            logger.info(f"Successfully processed image, output size: {len(output_base64)} bytes")
        except Exception as e:
            logger.error(f"Failed to encode output image: {e}")
            return JsonResponse({'error': 'Failed to encode output image'}, status=500)
        
        return JsonResponse({
            'success': True,
            'image': f'data:image/jpeg;base64,{output_base64}'
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in background removal API: {e}", exc_info=True)
        return JsonResponse({
            'error': 'An unexpected error occurred. Please try again.',
            'success': False
        }, status=500)
