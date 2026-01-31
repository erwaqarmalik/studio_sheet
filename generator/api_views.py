"""
API views for background removal and other image processing.
"""
import os
import io
import base64
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from PIL import Image

logger = logging.getLogger('generator')


@csrf_exempt
@require_http_methods(["POST"])
def remove_background_api(request):
    """
    API endpoint for AI-powered background removal.
    Accepts base64 encoded image and background color, returns processed image.
    """
    try:
        # Get image data from request
        image_data = request.POST.get('image')
        bg_color = request.POST.get('bg_color', '#FFFFFF')
        
        if not image_data:
            return JsonResponse({'error': 'No image data provided'}, status=400)
        
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Import and use rembg
        try:
            from rembg import remove
            logger.info("rembg imported successfully, processing image...")
        except ImportError as e:
            logger.error(f"rembg library import failed: {e}")
            return JsonResponse({'error': 'Background removal service not available. Please install rembg.'}, status=500)
        
        # Remove background using rembg AI (may download model on first use)
        try:
            logger.info(f"Processing image, size: {len(image_bytes)} bytes")
            output_bytes = remove(image_bytes)
            logger.info(f"Background removed, output size: {len(output_bytes)} bytes")
        except Exception as e:
            logger.error(f"rembg processing failed: {e}", exc_info=True)
            return JsonResponse({'error': f'Background removal failed: {str(e)}. The AI model may need to download on first use.'}, status=500)
        
        # Open as PIL Image
        img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
        
        # Convert hex color to RGB with validation
        hex_color = bg_color.lstrip('#').strip()
        
        # Validate hex color format
        if len(hex_color) != 6:
            logger.error(f"Invalid hex color format: {bg_color} (cleaned: {hex_color})")
            return JsonResponse({'error': f'Invalid color format: {bg_color}. Expected format: #RRGGBB'}, status=400)
        
        try:
            bg_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            logger.info(f"Parsed color {bg_color} to RGB: {bg_rgb}")
        except ValueError as e:
            logger.error(f"Failed to parse hex color {bg_color}: {e}")
            return JsonResponse({'error': f'Invalid hex color: {bg_color}. Use format #RRGGBB (e.g., #FFFFFF)'}, status=400)
        
        # Create new image with solid background
        background = Image.new("RGB", img.size, bg_rgb)
        background.paste(img, (0, 0), img)
        
        # Convert to base64
        output_buffer = io.BytesIO()
        background.save(output_buffer, format='JPEG', quality=95, subsampling=0)
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        
        logger.info(f"Background removed successfully, output size: {len(output_base64)} bytes")
        
        return JsonResponse({
            'success': True,
            'image': f'data:image/jpeg;base64,{output_base64}'
        })
        
    except Exception as e:
        logger.error(f"Error in background removal API: {e}", exc_info=True)
        return JsonResponse({'error': f'Processing failed: {str(e)}'}, status=500)
