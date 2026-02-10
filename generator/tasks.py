import os
import io
import base64
import logging

try:
    from celery import shared_task
except Exception:
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
from django.conf import settings
from django.utils import timezone
from PIL import Image

from .models import PhotoGeneration
from .utils import (
    generate_pdf,
    generate_jpeg,
    zip_files,
    crop_to_passport_aspect_ratio,
    remove_background,
)

logger = logging.getLogger('generator')


@shared_task(bind=True)
def generate_photosheet_task(
    self,
    session_id,
    user_id,
    saved_photos,
    copies_map,
    paper_size,
    orientation,
    margin_cm,
    col_gap_cm,
    row_gap_cm,
    cut_lines,
    output_type,
    photo_width_cm,
    photo_height_cm,
    remove_bg,
    bg_color,
    cut_line_style="full",
):
    """Generate photosheet asynchronously and update PhotoGeneration record."""
    try:
        # Crop photos to target aspect ratio
        for photo_path in saved_photos:
            crop_to_passport_aspect_ratio(photo_path, photo_width_cm, photo_height_cm)

        # Optional background removal
        if remove_bg:
            for photo_path in saved_photos:
                success = remove_background(photo_path, bg_color)
                if not success:
                    logger.warning(f"Failed to remove background from {os.path.basename(photo_path)}")

        # Generate output
        output_dir = os.path.join(settings.MEDIA_ROOT, "outputs", session_id)

        if output_type == "PDF":
            output_path = generate_pdf(
                photos=saved_photos,
                copies_map=copies_map,
                paper_size=paper_size,
                orientation=orientation,
                margin_cm=margin_cm,
                col_gap_cm=col_gap_cm,
                row_gap_cm=row_gap_cm,
                cut_lines=cut_lines,
                output_dir=output_dir,
                photo_width_cm=photo_width_cm,
                photo_height_cm=photo_height_cm,
                cut_line_style=cut_line_style,
            )
        else:
            jpeg_files = generate_jpeg(
                photos=saved_photos,
                copies_map=copies_map,
                paper_size=paper_size,
                orientation=orientation,
                margin_cm=margin_cm,
                col_gap_cm=col_gap_cm,
                row_gap_cm=row_gap_cm,
                cut_lines=cut_lines,
                output_dir=output_dir,
                photo_width_cm=photo_width_cm,
                photo_height_cm=photo_height_cm,
                cut_line_style=cut_line_style,
            )
            output_path = jpeg_files[0] if len(jpeg_files) == 1 else zip_files(jpeg_files, output_dir)

        output_url = settings.MEDIA_URL + f"outputs/{session_id}/" + os.path.basename(output_path)
        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else None
        total_copies = sum(copies_map.values()) if copies_map else 0

        PhotoGeneration.objects.filter(session_id=session_id).update(
            output_path=output_path,
            output_url=output_url,
            file_size_bytes=file_size,
            total_copies=total_copies,
            status='completed',
            error_message='',
        )

        logger.info(f"Generated output for session {session_id}")
        return {'success': True, 'output_url': output_url}
    except Exception as e:
        logger.error(f"Task failed for session {session_id}: {e}", exc_info=True)
        PhotoGeneration.objects.filter(session_id=session_id).update(
            status='failed',
            error_message=str(e),
        )
        return {'success': False, 'error': str(e)}


@shared_task(bind=True)
def remove_background_task(self, image_data, bg_color):
    """Remove background asynchronously and return base64 image data. Optimized for limited resources."""
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        image_bytes = base64.b64decode(image_data)
        
        # Optimize: Resize large images
        img_temp = Image.open(io.BytesIO(image_bytes))
        if max(img_temp.size) > 2000:
            ratio = 2000 / max(img_temp.size)
            new_size = (int(img_temp.size[0] * ratio), int(img_temp.size[1] * ratio))
            img_temp = img_temp.resize(new_size, Image.LANCZOS)
            buffer = io.BytesIO()
            img_temp.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
        
        from rembg import remove, new_session
        # Use lighter u2net_human_seg model for passport photos
        session = new_session('u2net_human_seg')
        output_bytes = remove(image_bytes, session=session)
        img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

        hex_color = bg_color.lstrip('#').strip().upper()
        if len(hex_color) != 6:
            return {'success': False, 'error': f'Invalid color format: {bg_color}. Expected #RRGGBB'}
        bg_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        background = Image.new("RGB", img.size, bg_rgb)
        background.paste(img, (0, 0), img)

        output_buffer = io.BytesIO()
        background.save(output_buffer, format='JPEG', quality=95, subsampling=0)
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')

        return {'success': True, 'image': f'data:image/jpeg;base64,{output_base64}'}
    except Exception as e:
        logger.error(f"Background removal task failed: {e}", exc_info=True)
        return {'success': False, 'error': 'Failed to process image'}
