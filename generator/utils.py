import os
import io
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from PIL import Image, ImageDraw
import zipfile
from .config import PASSPORT_CONFIG

logger = logging.getLogger('generator')

# ==================================================
# CONSTANTS
# ==================================================
PHOTO_W_CM = PASSPORT_CONFIG["photo_width_cm"]
PHOTO_H_CM = PASSPORT_CONFIG["photo_height_cm"]
DPI = 300

# Cut line settings
CUT_LINE_WIDTH_PDF = 0.4
CUT_LINE_SIZE_PDF = 5
CUT_LINE_SIZE_IMG = 15
CUT_LINE_WIDTH_IMG = 1

# JPEG quality
JPEG_QUALITY = 95

PAPER_SIZES = {
    "A4": {"width_cm": 21.0, "height_cm": 29.7},
    "A3": {"width_cm": 29.7, "height_cm": 42.0},
    "Letter": {"width_cm": 21.59, "height_cm": 27.94}
}


# ==================================================
# HELPERS
# ==================================================
def cm_to_px(value_cm: float, dpi: int = DPI) -> int:
    """Convert centimeters to pixels at given DPI."""
    return int((value_cm * cm) / 72 * dpi)


def resolve_paper_size(paper_size: str, orientation: str) -> Tuple[float, float, float, float]:
    """
    Resolve paper size and orientation to dimensions.
    
    Args:
        paper_size: Paper size key (e.g., "A4", "A3", "Letter")
        orientation: "portrait" or "landscape"
    
    Returns:
        Tuple of (width_pt, height_pt, width_cm, height_cm)
    """
    size = PAPER_SIZES.get(paper_size, PAPER_SIZES["A4"])

    # FORCE numeric conversion
    w_cm = float(size["width_cm"])
    h_cm = float(size["height_cm"])

    if orientation == "landscape":
        w_cm, h_cm = h_cm, w_cm

    return w_cm * cm, h_cm * cm, w_cm, h_cm


def calculate_grid(paper_w_cm: float, paper_h_cm: float, margin: float, 
                   col_gap: float, row_gap: float, photo_w_cm: float = None, 
                   photo_h_cm: float = None) -> Tuple[int, int]:
    """
    Calculate grid dimensions for photo layout.
    
    Args:
        paper_w_cm: Paper width in cm
        paper_h_cm: Paper height in cm
        margin: Margin in cm
        col_gap: Column gap in cm
        row_gap: Row gap in cm
        photo_w_cm: Photo width in cm (default: 3.5 cm)
        photo_h_cm: Photo height in cm (default: 4.5 cm)
    
    Returns:
        Tuple of (columns, rows)
    """
    if photo_w_cm is None:
        photo_w_cm = PASSPORT_CONFIG["photo_width_cm"]
    if photo_h_cm is None:
        photo_h_cm = PASSPORT_CONFIG["photo_height_cm"]
    usable_w = paper_w_cm - 2 * margin
    usable_h = paper_h_cm - 2 * margin

    cols = int((usable_w + col_gap) // (photo_w_cm + col_gap))
    rows = int((usable_h + row_gap) // (photo_h_cm + row_gap))

    return max(cols, 1), max(rows, 1)


def draw_cut_lines_pdf(c: canvas.Canvas, x: float, y: float, w: float, h: float, 
                       size: float = CUT_LINE_SIZE_PDF) -> None:
    """Draw corner cut lines on PDF canvas."""
    c.setLineWidth(CUT_LINE_WIDTH_PDF)
    for dx, dy in [(0, 0), (w, 0), (0, h), (w, h)]:
        c.line(x + dx, y + dy, x + dx + (size if dx == 0 else -size), y + dy)
        c.line(x + dx, y + dy, x + dx, y + dy + (size if dy == 0 else -size))


def draw_cut_lines_img(draw: ImageDraw.Draw, x: int, y: int, w: int, h: int, 
                       size: int = CUT_LINE_SIZE_IMG) -> None:
    """Draw corner cut lines on PIL ImageDraw."""
    draw.line((x, y, x + size, y), fill="black", width=CUT_LINE_WIDTH_IMG)
    draw.line((x, y, x, y + size), fill="black", width=CUT_LINE_WIDTH_IMG)
    draw.line((x + w, y, x + w - size, y), fill="black", width=CUT_LINE_WIDTH_IMG)
    draw.line((x + w, y, x + w, y + size), fill="black", width=CUT_LINE_WIDTH_IMG)
    draw.line((x, y + h, x + size, y + h), fill="black", width=CUT_LINE_WIDTH_IMG)
    draw.line((x, y + h, x, y + h - size), fill="black", width=CUT_LINE_WIDTH_IMG)
    draw.line((x + w, y + h, x + w - size, y + h), fill="black", width=CUT_LINE_WIDTH_IMG)
    draw.line((x + w, y + h, x + w, y + h - size), fill="black", width=CUT_LINE_WIDTH_IMG)


def crop_to_passport_aspect_ratio(image_path: str, width_cm: float = None, height_cm: float = None) -> bool:
    """
    Crop an image to match photo aspect ratio.
    Uses centered cropping to preserve the center of the image.
    
    Args:
        image_path: Path to the image file to crop
        width_cm: Target width in cm (default: 3.5 cm)
        height_cm: Target height in cm (default: 4.5 cm)
    
    Returns:
        True if cropping was successful, False otherwise
    """
    if width_cm is None:
        width_cm = PASSPORT_CONFIG["photo_width_cm"]
    if height_cm is None:
        height_cm = PASSPORT_CONFIG["photo_height_cm"]
    try:
        # Open and load image (not using context manager since we need to save after)
        img = Image.open(image_path)
        
        # Convert to RGB if necessary (handles RGBA, P, etc.)
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        original_width, original_height = img.size
        target_aspect = width_cm / height_cm
        current_aspect = original_width / original_height
        
        # If aspect ratios match (within small tolerance), no cropping needed
        if abs(current_aspect - target_aspect) < 0.001:
            img.close()
            return True
        
        # Calculate crop dimensions
        if current_aspect > target_aspect:
            # Image is wider than target - crop width
            new_width = int(original_height * target_aspect)
            new_height = original_height
            left = (original_width - new_width) // 2
            top = 0
            right = left + new_width
            bottom = new_height
        else:
            # Image is taller than target - crop height
            new_width = original_width
            new_height = int(original_width / target_aspect)
            left = 0
            top = (original_height - new_height) // 2
            right = new_width
            bottom = top + new_height
        
        # Perform centered crop
        cropped_img = img.crop((left, top, right, bottom))
        img.close()
        
        # Save the cropped image, preserving original format
        # Determine output format from file extension
        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            cropped_img.save(image_path, "JPEG", quality=JPEG_QUALITY, subsampling=0)
        elif ext == '.png':
            cropped_img.save(image_path, "PNG")
        else:
            # Default to JPEG
            cropped_img.save(image_path, "JPEG", quality=JPEG_QUALITY, subsampling=0)
        
        cropped_img.close()
        return True
        
    except Exception as e:
        # Log error but don't raise - let caller handle
        return False


def remove_background(image_path: str, bg_color: str = "#FFFFFF") -> bool:
    """
    Remove background from an image and replace with solid color.
    Optimized for limited server resources.
    
    Args:
        image_path: Path to the image file
        bg_color: Hex color code for background (default: white)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from rembg import remove
        
        # Open and potentially resize image
        img = Image.open(image_path)
        original_size = img.size
        max_dimension = 2000  # Limit for memory efficiency
        
        # Resize if too large
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            logger.info(f"Resized from {original_size} to {new_size} for processing")
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        input_data = buffer.getvalue()
        
        # Remove background with lighter model
        from rembg import new_session
        session = new_session('u2net_human_seg')
        output_data = remove(input_data, session=session)
        
        # Open as PIL Image
        img = Image.open(io.BytesIO(output_data)).convert("RGBA")
        
        # Convert hex color to RGB
        bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        # Create new image with solid background
        background = Image.new("RGB", img.size, bg_rgb)
        
        # Paste the image with transparency
        background.paste(img, (0, 0), img)
        
        # Save the result
        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            background.save(image_path, "JPEG", quality=JPEG_QUALITY, subsampling=0)
        elif ext == '.png':
            background.save(image_path, "PNG")
        else:
            background.save(image_path, "JPEG", quality=JPEG_QUALITY, subsampling=0)
        
        background.close()
        img.close()
        
        logger.info(f"Background removed from {os.path.basename(image_path)}")
        return True
        
    except ImportError:
        logger.error("rembg library not installed. Run: pip install rembg")
        return False
    except Exception as e:
        logger.error(f"Error removing background: {e}", exc_info=True)
        return False


# ==================================================
# PDF GENERATOR
# ==================================================
def generate_pdf(
    photos: List[str],
    copies_map: Dict[str, int],
    paper_size: str,
    orientation: str,
    margin_cm: float,
    col_gap_cm: float,
    row_gap_cm: float,
    cut_lines: bool,
    output_dir: str,
    photo_width_cm: float = None,
    photo_height_cm: float = None,
    cut_line_style: str = "full",
) -> str:
    """
    Generate a PDF file with photos arranged in a grid.
    
    Args:
        photos: List of photo file paths
        copies_map: Dictionary mapping photo paths to number of copies
        paper_size: Paper size key (e.g., "A4", "A3", "Letter")
        orientation: "portrait" or "landscape"
        margin_cm: Margin in centimeters
        col_gap_cm: Column gap in centimeters
        row_gap_cm: Row gap in centimeters
        cut_lines: Whether to draw cut lines
        output_dir: Output directory path
        photo_width_cm: Photo width in cm (default: 3.5 cm)
        photo_height_cm: Photo height in cm (default: 4.5 cm)
        cut_line_style: Style of cut lines - "full" for complete lines or "crosshair" for registration marks
    
    Returns:
        Path to the generated PDF file
    
    Raises:
        IOError: If output directory doesn't exist or file cannot be written
    """
    if photo_width_cm is None:
        photo_width_cm = PASSPORT_CONFIG["photo_width_cm"]
    if photo_height_cm is None:
        photo_height_cm = PASSPORT_CONFIG["photo_height_cm"]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"passport_{ts}.pdf")

    paper_w_pt, paper_h_pt, paper_w_cm, paper_h_cm = resolve_paper_size(
        paper_size, orientation
    )

    c = canvas.Canvas(output_path, pagesize=(paper_w_pt, paper_h_pt))

    photo_w = photo_width_cm * cm
    photo_h = photo_height_cm * cm

    cols, rows = calculate_grid(
        paper_w_cm,
        paper_h_cm,
        margin_cm,
        col_gap_cm,
        row_gap_cm,
        photo_width_cm,
        photo_height_cm,
    )

    per_page = cols * rows
    slot = 0

    # Calculate centering offsets
    grid_width_cm = cols * photo_width_cm + (cols - 1) * col_gap_cm if cols > 0 else 0
    grid_height_cm = rows * photo_height_cm + (rows - 1) * row_gap_cm if rows > 0 else 0
    usable_w_cm = paper_w_cm - 2 * margin_cm
    usable_h_cm = paper_h_cm - 2 * margin_cm
    offset_x_cm = (usable_w_cm - grid_width_cm) / 2 if cols > 0 else 0
    offset_y_cm = (usable_h_cm - grid_height_cm) / 2 if rows > 0 else 0

    for img_path in photos:
        if not os.path.exists(img_path):
            continue  # Skip missing files
        
        copies = copies_map.get(img_path, 1)
        for _ in range(copies):
            if slot == per_page:
                c.showPage()
                slot = 0

            col = slot % cols
            row = slot // cols

            x = (margin_cm + offset_x_cm + col * (photo_width_cm + col_gap_cm)) * cm
            y = paper_h_pt - (
                (margin_cm + offset_y_cm + photo_height_cm + row * (photo_height_cm + row_gap_cm)) * cm
            )

            try:
                c.drawImage(img_path, x, y, photo_w, photo_h, mask="auto")
            except Exception:
                # Skip corrupted images
                continue

            # Draw thin border around photo
            c.setStrokeColorRGB(0, 0, 0)  # Black border
            c.setLineWidth(0.3)  # Thinner professional border
            c.rect(x, y, photo_w, photo_h, stroke=1, fill=0)

            if cut_lines:
                draw_cut_lines_pdf(c, x, y, photo_w, photo_h)

            slot += 1

    # Draw cut lines based on style
    if cut_lines and (rows > 1 or cols > 1):
        if cut_line_style == "crosshair":
            # Professional registration marks (crosshairs)
            mark_size = 0.5 * cm  # Size of crosshair marks
            c.setLineWidth(0.5)
            c.setDash([3, 2])  # Dashed pattern
            
            # Draw crosshairs at intersections
            for row in range(rows + 1):
                for col in range(cols + 1):
                    # Skip the four absolute corners
                    if (row == 0 or row == rows) and (col == 0 or col == cols):
                        continue
                    
                    # Calculate position
                    if row == 0:
                        # Top edge - place crosshair above photos
                        y_pos = paper_h_pt - ((margin_cm + offset_y_cm - 0.3) * cm)
                    elif row == rows:
                        # Bottom edge - place crosshair below photos
                        y_pos = paper_h_pt - ((margin_cm + offset_y_cm + grid_height_cm + 0.3) * cm)
                    else:
                        # Between photos - in the gap center
                        y_pos = paper_h_pt - ((margin_cm + offset_y_cm + row * photo_height_cm + (row - 0.5) * row_gap_cm) * cm)
                    
                    if col == 0:
                        # Left edge - place crosshair left of photos
                        x_pos = ((margin_cm + offset_x_cm - 0.3) * cm)
                    elif col == cols:
                        # Right edge - place crosshair right of photos
                        x_pos = ((margin_cm + offset_x_cm + grid_width_cm + 0.3) * cm)
                    else:
                        # Between photos - in the gap center
                        x_pos = (margin_cm + offset_x_cm + col * photo_width_cm + (col - 0.5) * col_gap_cm) * cm
                    
                    # Draw horizontal line in blue
                    c.setStrokeColorRGB(0.0, 0.4, 0.8)  # Blue
                    c.line(x_pos - mark_size, y_pos, x_pos + mark_size, y_pos)
                    
                    # Draw vertical line in red
                    c.setStrokeColorRGB(0.8, 0.0, 0.2)  # Red
                    c.line(x_pos, y_pos - mark_size, x_pos, y_pos + mark_size)
            
            c.setDash()  # Reset dash pattern
        else:
            # Full cut lines (default)
            c.setStrokeColorRGB(0.4, 0.4, 0.4)
            c.setLineWidth(0.2)
            c.setDash([3, 2])
            
            # Horizontal cut lines
            if rows > 1:
                for row in range(1, rows):
                    y_line = paper_h_pt - ((margin_cm + offset_y_cm + row * photo_height_cm + (row - 0.5) * row_gap_cm) * cm)
                    x_start = (margin_cm + offset_x_cm) * cm
                    x_end = (margin_cm + offset_x_cm + grid_width_cm) * cm
                    c.line(x_start, y_line, x_end, y_line)
            
            # Vertical cut lines
            if cols > 1:
                for col in range(1, cols):
                    x_line = (margin_cm + offset_x_cm + col * photo_width_cm + (col - 0.5) * col_gap_cm) * cm
                    y_start = paper_h_pt - ((margin_cm + offset_y_cm) * cm)
                    y_end = paper_h_pt - ((margin_cm + offset_y_cm + grid_height_cm) * cm)
                    c.line(x_line, y_start, x_line, y_end)
            
            c.setDash()

    c.save()
    return output_path


def zip_files(files: List[str], output_dir: str) -> str:
    """
    Create a ZIP archive containing the specified files.
    
    Args:
        files: List of file paths to include in the ZIP
        output_dir: Output directory for the ZIP file
    
    Returns:
        Path to the created ZIP file
    """
def generate_jpeg(
    photos: List[str],
    copies_map: Dict[str, int],
    paper_size: str,
    orientation: str,
    margin_cm: float,
    col_gap_cm: float,
    row_gap_cm: float,
    cut_lines: bool,
    output_dir: str,
    photo_width_cm: float = None,
    photo_height_cm: float = None,
    cut_line_style: str = "full",
) -> List[str]:
    """
    Generate JPEG files with photos arranged in a grid.
    
    Args:
        photos: List of photo file paths
        copies_map: Dictionary mapping photo paths to number of copies
        paper_size: Paper size key (e.g., "A4", "A3", "Letter")
        orientation: "portrait" or "landscape"
        margin_cm: Margin in centimeters
        col_gap_cm: Column gap in centimeters
        row_gap_cm: Row gap in centimeters
        cut_lines: Whether to draw cut lines
        output_dir: Output directory path
        photo_width_cm: Photo width in cm (default: 3.5 cm)
        photo_height_cm: Photo height in cm (default: 4.5 cm)
        cut_line_style: Style of cut lines - "full" for complete lines or "crosshair" for registration marks
    
    Returns:
        List of paths to the generated JPEG files
    
    Raises:
        IOError: If output directory doesn't exist or files cannot be written
    """
    if photo_width_cm is None:
        photo_width_cm = PASSPORT_CONFIG["photo_width_cm"]
    if photo_height_cm is None:
        photo_height_cm = PASSPORT_CONFIG["photo_height_cm"]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # -----------------------------
    # PAPER SIZE
    # -----------------------------
    size = PAPER_SIZES.get(paper_size, PAPER_SIZES["A4"])
    paper_w_cm = float(size["width_cm"])
    paper_h_cm = float(size["height_cm"])

    if orientation == "landscape":
        paper_w_cm, paper_h_cm = paper_h_cm, paper_w_cm

    paper_w_px = cm_to_px(paper_w_cm)
    paper_h_px = cm_to_px(paper_h_cm)

    # -----------------------------
    # Layout calculation
    margin_px = cm_to_px(margin_cm)
    col_gap_px = cm_to_px(col_gap_cm)
    row_gap_px = cm_to_px(row_gap_cm)

    photo_w_px = cm_to_px(photo_width_cm)
    photo_h_px = cm_to_px(photo_height_cm)

    usable_w = paper_w_px - 2 * margin_px
    usable_h = paper_h_px - 2 * margin_px

    cols = max(1, int((usable_w + col_gap_px) / (photo_w_px + col_gap_px)))
    rows = max(1, int((usable_h + row_gap_px) / (photo_h_px + row_gap_px)))

    # Calculate centering offsets
    grid_width_px = cols * photo_w_px + (cols - 1) * col_gap_px if cols > 0 else 0
    grid_height_px = rows * photo_h_px + (rows - 1) * row_gap_px if rows > 0 else 0
    offset_x_px = (usable_w - grid_width_px) / 2 if cols > 0 else 0
    offset_y_px = (usable_h - grid_height_px) / 2 if rows > 0 else 0

    # -----------------------------
    # EXPAND PHOTOS BY COPIES
    # -----------------------------
    expanded = []
    for path in photos:
        if os.path.exists(path):
            expanded.extend([path] * copies_map.get(path, 1))

    if not expanded:
        return []

    # -----------------------------
    # PAGE GENERATION
    # -----------------------------
    pages = []
    idx = 0

    while idx < len(expanded):
        page = Image.new("RGB", (paper_w_px, paper_h_px), "white")
        
        # Store positions for cut lines (if needed)
        photo_positions = []

        for r in range(rows):
            for c in range(cols):
                if idx >= len(expanded):
                    break

                x = margin_px + offset_x_px + c * (photo_w_px + col_gap_px)
                y = margin_px + offset_y_px + r * (photo_h_px + row_gap_px)

                try:
                    img = Image.open(expanded[idx])
                    img = img.convert("RGB")
                    img = img.resize((photo_w_px, photo_h_px), Image.LANCZOS)
                    # Load the image data completely before pasting
                    img.load()
                    page.paste(img, (int(x), int(y)))
                    img.close()
                    
                    # Draw thin border around photo
                    draw_temp = ImageDraw.Draw(page)
                    draw_temp.rectangle(
                        [int(x), int(y), int(x + photo_w_px), int(y + photo_h_px)],
                        outline=(0, 0, 0),  # Black border
                        width=1  # Thinner professional border
                    )
                    
                    if cut_lines:
                        photo_positions.append((int(x), int(y), photo_w_px, photo_h_px))
                except Exception as e:
                    # Skip corrupted images
                    logger.warning(f"Failed to process image {expanded[idx]}: {e}")
                    idx += 1
                    continue

                idx += 1

        # Draw cut lines after all images are pasted
        if cut_lines and (rows > 1 or cols > 1):
            draw = ImageDraw.Draw(page)
            
            if cut_line_style == "crosshair":
                # Professional registration marks (crosshairs)
                mark_size = int(cm_to_px(0.5))
                dash_length = 8
                gap_length = 4
                offset_edge = int(cm_to_px(0.3))  # Offset for edge crosshairs
                
                # Draw crosshairs at intersections
                for row in range(rows + 1):
                    for col in range(cols + 1):
                        # Skip the four absolute corners
                        if (row == 0 or row == rows) and (col == 0 or col == cols):
                            continue
                        
                        # Calculate position
                        if row == 0:
                            # Top edge - place crosshair above photos
                            y_pos = int(margin_px + offset_y_px - offset_edge)
                        elif row == rows:
                            # Bottom edge - place crosshair below photos
                            y_pos = int(margin_px + offset_y_px + grid_height_px + offset_edge)
                        else:
                            # Between photos - in the gap center
                            y_pos = int(margin_px + offset_y_px + row * photo_h_px + (row - 0.5) * row_gap_px)
                        
                        if col == 0:
                            # Left edge - place crosshair left of photos
                            x_pos = int(margin_px + offset_x_px - offset_edge)
                        elif col == cols:
                            # Right edge - place crosshair right of photos
                            x_pos = int(margin_px + offset_x_px + grid_width_px + offset_edge)
                        else:
                            # Between photos - in the gap center
                            x_pos = int(margin_px + offset_x_px + col * photo_w_px + (col - 0.5) * col_gap_px)
                        
                        # Draw dashed horizontal crosshair line in blue
                        blue_color = (0, 102, 204)  # Blue
                        x_current = x_pos - mark_size
                        x_end = x_pos + mark_size
                        while x_current < x_end:
                            x_next = min(x_current + dash_length, x_end)
                            draw.line([(x_current, y_pos), (x_next, y_pos)], fill=blue_color, width=2)
                            x_current = x_next + gap_length
                        
                        # Draw dashed vertical crosshair line in red
                        red_color = (204, 0, 51)  # Red
                        y_current = y_pos - mark_size
                        y_end = y_pos + mark_size
                        while y_current < y_end:
                            y_next = min(y_current + dash_length, y_end)
                            draw.line([(x_pos, y_current), (x_pos, y_next)], fill=red_color, width=2)
                            y_current = y_next + gap_length
            else:
                # Full cut lines (default)
                dash_length = 8
                gap_length = 4
                line_color = (100, 100, 100)
                
                # Horizontal cut lines
                if rows > 1:
                    for row in range(1, rows):
                        y_line = int(margin_px + offset_y_px + row * photo_h_px + (row - 0.5) * row_gap_px)
                        x_start = int(margin_px + offset_x_px)
                        x_end = int(margin_px + offset_x_px + grid_width_px)
                        
                        x_current = x_start
                        while x_current < x_end:
                            x_next = min(x_current + dash_length, x_end)
                            draw.line([(x_current, y_line), (x_next, y_line)], fill=line_color, width=1)
                            x_current = x_next + gap_length
                
                # Vertical cut lines
                if cols > 1:
                    for col in range(1, cols):
                        x_line = int(margin_px + offset_x_px + col * photo_w_px + (col - 0.5) * col_gap_px)
                        y_start = int(margin_px + offset_y_px)
                        y_end = int(margin_px + offset_y_px + grid_height_px)
                        
                        y_current = y_start
                        while y_current < y_end:
                            y_next = min(y_current + dash_length, y_end)
                            draw.line([(x_line, y_current), (x_line, y_next)], fill=line_color, width=1)
                            y_current = y_next + gap_length

        pages.append(page)

    # -----------------------------
    # SAVE JPEG FILES
    # -----------------------------
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_files = []

    for i, page in enumerate(pages, start=1):
        filename = f"passport_page_{i}_{timestamp}.jpg"
        path = os.path.join(output_dir, filename)
        page.save(path, "JPEG", quality=JPEG_QUALITY, subsampling=0)
        output_files.append(path)

    return output_files
