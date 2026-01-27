# Passport Photo Generator

A Django web application for generating passport photos in PDF or JPEG format with customizable layouts.

## Features

- Upload multiple photos
- Customize number of copies per photo
- Adjustable paper size (A4, A3, Letter)
- Portrait/Landscape orientation
- Customizable margins and gaps
- Optional cut lines
- PDF or JPEG output
- Responsive design

## Requirements

- Python 3.8+
- Django 5.0.4
- Pillow 10.0.0+
- ReportLab 4.0.0+
- python-decouple 3.8+

## Installation

1. Clone the repository
2. Install dependencies:h
   pip install -r requirements.txt
   3. Create a `.env` file (copy from `.env.example`):sh
   cp .env.example .env
   4. Update `.env` with your settings:
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   5. Run migrations:h
   python manage.py migrate
   6. Create logs directory:
   mkdir logs
   7. Run the development server:
   
   python manage.py runserver
   ## Usage

1. Open your browser and navigate to `http://localhost:8000`
2. Select one or more photos
3. Adjust settings (paper size, orientation, margins, etc.)
4. Click "Generate Output"
5. Download the generated PDF or JPEG file

## Security Notes

- Never commit `.env` file to version control
- Change `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Configure `ALLOWED_HOSTS` for your domain
- File uploads are limited to 10MB per file
- Only image files (JPG, JPEG, PNG) are accepted

## License

MIT