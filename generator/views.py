import os
import json
import logging
from uuid import uuid4
from typing import Dict, List, Optional
from django.shortcuts import render
from django.conf import settings
from django.utils.text import get_valid_filename
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required

from .models import PhotoGeneration
from .tasks import generate_photosheet_task
from .utils import (
    generate_pdf,
    generate_jpeg,
    zip_files,
    crop_to_passport_aspect_ratio,
    remove_background,
    PAPER_SIZES,
)
from .config import PASSPORT_CONFIG, PHOTO_SIZES
from .validators import (
    validate_image_file,
    validate_numeric_field,
    validate_copies_list,
)

logger = logging.getLogger('generator')


@login_required(login_url='generator:login')
def index(request: HttpRequest) -> HttpResponse:
    """
    Main view for passport photo generator.
    Requires user login. Handles file uploads and generates PDF/JPEG output.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        Rendered HTML response with context
    """
    output_url: Optional[str] = None
    error: Optional[str] = None
    processing_message: Optional[str] = None
    processing_session_id: Optional[str] = None
    processing_generation_id: Optional[int] = None

    if request.method == "POST":
        try:
            # ==================================================
            # 1. FILE UPLOADS WITH VALIDATION
            # ==================================================
            uploaded_files = request.FILES.getlist("photos")
            if not uploaded_files:
                raise ValueError("No photos uploaded. Please select at least one photo.")
            
            if len(uploaded_files) > 50:  # Reasonable limit
                raise ValueError(f"Too many files uploaded ({len(uploaded_files)}). Maximum: 50 files.")

            # Validate all files before processing
            for idx, f in enumerate(uploaded_files, 1):
                try:
                    validate_image_file(f)
                except ValidationError as e:
                    raise ValidationError(f"File {idx} ({f.name}): {str(e)}")

            session_id = uuid4().hex
            output_dir = os.path.join(
                settings.MEDIA_ROOT, "outputs", session_id
            )
            os.makedirs(output_dir, exist_ok=True)

            # ==================================================
            # DETERMINE PHOTO SIZE FIRST (needed for cropping)
            # ==================================================
            photo_size = request.POST.get(
                "default_photo_size",
                PASSPORT_CONFIG["default_photo_size"],
            )
            
            photo_width_cm = PASSPORT_CONFIG["photo_width_cm"]
            photo_height_cm = PASSPORT_CONFIG["photo_height_cm"]
            
            # Handle custom size
            if photo_size == "custom":
                custom_width = validate_numeric_field(
                    request.POST.get("custom_width_cm"),
                    "Custom width",
                    min_val=1.0,
                    max_val=20.0,
                    default=PASSPORT_CONFIG["photo_width_cm"]
                )
                custom_height = validate_numeric_field(
                    request.POST.get("custom_height_cm"),
                    "Custom height",
                    min_val=1.0,
                    max_val=20.0,
                    default=PASSPORT_CONFIG["photo_height_cm"]
                )
                photo_width_cm = custom_width
                photo_height_cm = custom_height
            else:
                # Use preset size
                if photo_size in PHOTO_SIZES:
                    size_info = PHOTO_SIZES[photo_size]
                    photo_width_cm = size_info["width"]
                    photo_height_cm = size_info["height"]

            saved_photos = []
            for f in uploaded_files:
                # Sanitize filename to prevent path traversal
                safe_name = get_valid_filename(f.name)
                file_path = os.path.join(output_dir, safe_name)
                
                with open(file_path, "wb+") as dest:
                    for chunk in f.chunks():
                        dest.write(chunk)
                
                # Crop image to match selected photo aspect ratio
                crop_to_passport_aspect_ratio(file_path, photo_width_cm, photo_height_cm)
                
                saved_photos.append(file_path)
            
            # ==================================================
            # BACKGROUND REMOVAL (if enabled)
            # ==================================================
            remove_bg = request.POST.get("remove_bg", "no") == "yes"
            bg_color = request.POST.get("bg_color", PASSPORT_CONFIG["default_bg_color"])

            # ==================================================
            # 2. COPIES PER PHOTO
            # ==================================================
            copies_list = request.POST.getlist("copies[]")
            validated_copies = validate_copies_list(copies_list, len(saved_photos))
            
            copies_map: Dict[str, int] = {}
            for idx, photo_path in enumerate(saved_photos):
                copies_map[photo_path] = validated_copies[idx]

            # ==================================================
            # 3. OPTIONS (WITH CENTRAL DEFAULTS)
            # ==================================================
            paper_size = request.POST.get(
                "paper_size",
                PASSPORT_CONFIG["default_paper_size"],
            )
            
            # Validate paper size
            if paper_size not in PAPER_SIZES:
                paper_size = PASSPORT_CONFIG["default_paper_size"]

            orientation = request.POST.get(
                "orientation",
                PASSPORT_CONFIG["default_orientation"],
            )
            
            # Validate orientation
            if orientation not in ["portrait", "landscape"]:
                orientation = PASSPORT_CONFIG["default_orientation"]

            margin_cm = validate_numeric_field(
                request.POST.get("margin_cm", PASSPORT_CONFIG["default_margin_cm"]),
                "Margin",
                min_val=0.0,
                max_val=5.0,
                default=PASSPORT_CONFIG["default_margin_cm"]
            )

            col_gap_cm = validate_numeric_field(
                request.POST.get("col_gap_cm", PASSPORT_CONFIG["default_col_gap_cm"]),
                "Column gap",
                min_val=0.0,
                max_val=5.0,
                default=PASSPORT_CONFIG["default_col_gap_cm"]
            )

            row_gap_cm = validate_numeric_field(
                request.POST.get("row_gap_cm", PASSPORT_CONFIG["default_row_gap_cm"]),
                "Row gap",
                min_val=0.0,
                max_val=5.0,
                default=PASSPORT_CONFIG["default_row_gap_cm"]
            )

            # Handle cut line type
            cut_line_type = request.POST.get("cut_line_type", "full")
            cut_lines = cut_line_type != "none"
            cut_line_style = "crosshair" if cut_line_type == "crosshair" else "full"

            output_type = request.POST.get(
                "output_type",
                PASSPORT_CONFIG["default_output_type"],
            )

            # ==================================================
            # 4. GENERATE OUTPUT (async if enabled)
            # ==================================================
            celery_available = settings.CELERY_ENABLED and hasattr(generate_photosheet_task, 'delay')
            if celery_available:
                total_copies = sum(copies_map.values())
                generation = PhotoGeneration.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    session_id=session_id,
                    num_photos=len(saved_photos),
                    paper_size=paper_size,
                    orientation=orientation,
                    output_type=output_type,
                    output_path='',
                    output_url='',
                    file_size_bytes=None,
                    total_copies=total_copies,
                    status='processing',
                )

                task = generate_photosheet_task.delay(
                    session_id=session_id,
                    user_id=request.user.id if request.user.is_authenticated else None,
                    saved_photos=saved_photos,
                    copies_map=copies_map,
                    paper_size=paper_size,
                    orientation=orientation,
                    margin_cm=margin_cm,
                    col_gap_cm=col_gap_cm,
                    row_gap_cm=row_gap_cm,
                    cut_lines=cut_lines,
                    output_type=output_type,
                    photo_width_cm=photo_width_cm,
                    photo_height_cm=photo_height_cm,
                    remove_bg=remove_bg,
                    bg_color=bg_color,
                    cut_line_style=cut_line_style,
                )

                generation.task_id = task.id
                generation.save(update_fields=['task_id'])
                processing_message = "Your photosheet is being processed. Please wait..."
                processing_session_id = session_id
                processing_generation_id = generation.id
                logger.info(f"Queued generation task for session {session_id}")
            else:
                if remove_bg:
                    for photo_path in saved_photos:
                        success = remove_background(photo_path, bg_color)
                        if not success:
                            logger.warning(f"Failed to remove background from {os.path.basename(photo_path)}")

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

                else:  # JPEG
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

                logger.info(f"Successfully generated {output_type} for session {session_id}")
                
                try:
                    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else None
                    total_copies = sum(copies_map.values())
                    PhotoGeneration.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        session_id=session_id,
                        num_photos=len(saved_photos),
                        paper_size=paper_size,
                        orientation=orientation,
                        output_type=output_type,
                        output_path=output_path,
                        output_url=output_url,
                        file_size_bytes=file_size,
                        total_copies=total_copies,
                        status='completed',
                    )
                    logger.info(f"Saved generation history for session {session_id}")
                except Exception as e:
                    logger.error(f"Failed to save generation history: {e}", exc_info=True)

        except ValidationError as e:
            error = str(e)
            logger.warning(f"Validation error: {error}")
        except ValueError as e:
            error = str(e)
            logger.warning(f"Value error: {error}")
        except Exception as e:
            error = "An error occurred while processing your request. Please try again."
            logger.error(f"Error generating passport: {e}", exc_info=True)

    # ==================================================
    # 6. RENDER PAGE
    # ==================================================
    return render(
        request,
        "generator/index.html",
        {
            "output_url": output_url,
            "processing_message": processing_message,
            "processing_session_id": processing_session_id,
            "processing_generation_id": processing_generation_id,
            "error": error,
            "paper_sizes": PAPER_SIZES.keys(),
            "paper_sizes_json": json.dumps(PAPER_SIZES),
            "config_json": json.dumps(PASSPORT_CONFIG),
            "photo_sizes": PHOTO_SIZES,
            "photo_sizes_json": json.dumps(PHOTO_SIZES),
        },
    )