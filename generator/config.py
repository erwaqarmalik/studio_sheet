# generator/config.py

# Available photo sizes (width_cm, height_cm, label)
PHOTO_SIZES = {
    "passport_35x45": {"width": 3.5, "height": 4.5, "label": "Passport (3.5×4.5 cm)", "category": "Standard"},
    "passport_small": {"width": 2.5, "height": 3.5, "label": "Small Passport (2.5×3.5 cm)", "category": "Standard"},
    "id_card": {"width": 3.0, "height": 4.0, "label": "ID Card (3.0×4.0 cm)", "category": "Standard"},
    "visa_3x4": {"width": 3.0, "height": 4.0, "label": "Visa (3.0×4.0 cm)", "category": "Visa"},
    "visa_4x6": {"width": 4.0, "height": 6.0, "label": "Visa Large (4.0×6.0 cm)", "category": "Visa"},
    "uk_visa": {"width": 4.45, "height": 5.59, "label": "UK Visa (4.45×5.59 cm)", "category": "Visa"},
    "us_visa": {"width": 5.0, "height": 5.0, "label": "US Passport (5.0×5.0 cm)", "category": "Visa"},
    "schengen": {"width": 3.5, "height": 4.5, "label": "Schengen (3.5×4.5 cm)", "category": "Visa"},
    "australia": {"width": 4.5, "height": 5.5, "label": "Australia (4.5×5.5 cm)", "category": "Visa"},
    "canada": {"width": 3.5, "height": 4.5, "label": "Canada (3.5×4.5 cm)", "category": "Visa"},
    "custom": {"width": None, "height": None, "label": "Custom Size", "category": "Custom"},
}

PASSPORT_CONFIG = {
    # Default photo size (cm)
    "default_photo_size": "passport_35x45",
    "photo_width_cm": 3.5,
    "photo_height_cm": 4.5,

    # Layout defaults
    "default_margin_cm": 0.5,
    "default_col_gap_cm": 0.3,
    "default_row_gap_cm": 0.3,

    # Defaults
    "default_paper_size": "A4",
    "default_orientation": "portrait",
    "default_cut_lines": True,
    "default_output_type": "PDF",

    # Default copies per photo
    "default_copies": 6,
}
