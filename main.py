import json
from fpdf import FPDF
import os
from matplotlib.font_manager import FontProperties, findSystemFonts
import tkinter as tk
from tkinter import ttk
import logging
from fpdf.enums import XPos, YPos
from datetime import datetime
import requests
from urllib.parse import urlparse
from pathlib import Path
import io
import platform
import sys
import traceback

# Global variables
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = f'font_scanner_{TIMESTAMP}.log'

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)
LOG_PATH = os.path.join('logs', LOG_FILENAME)

# Set up logging with both file and console handlers
def setup_logging():
    """Configure logging to output to both file and console."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(LOG_PATH, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Log unhandled exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception

def log_system_info():
    """Log system information for debugging purposes."""
    try:
        logging.info("=== System Information ===")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Platform: {platform.platform()}")
        logging.info(f"OS: {platform.system()} {platform.release()}")
        logging.info(f"Machine: {platform.machine()}")
        logging.info(f"Processor: {platform.processor()}")
        logging.info(f"Working directory: {os.getcwd()}")
        logging.info("=== End System Information ===")
    except Exception as e:
        logging.error(f"Error logging system info: {str(e)}")
        logging.debug(traceback.format_exc())

def get_system_fonts():
    """Get list of available system fonts."""
    try:
        fonts = []
        font_paths = findSystemFonts()
        logging.info(f"Found {len(font_paths)} font files")
        
        for font_path in font_paths:
            try:
                font = FontProperties(fname=font_path)
                font_name = font.get_name()
                if font_name:
                    fonts.append(font_name)
            except Exception as e:
                logging.debug(f"Skipped font {font_path}: {str(e)}")
        
        unique_fonts = sorted(list(set(fonts)))
        logging.info(f"Successfully loaded {len(unique_fonts)} unique fonts")
        return unique_fonts
    except Exception as e:
        logging.error(f"Error getting system fonts: {str(e)}")
        logging.debug(traceback.format_exc())
        return ["Helvetica", "Arial", "Times New Roman"]  # Fallback fonts

def create_timestamped_folders():
    """Create timestamped folders for the current run."""
    timestamp_folder = f"output_{TIMESTAMP}"
    image_folder = os.path.join(timestamp_folder, "images")
    
    # Create folders
    os.makedirs(timestamp_folder, exist_ok=True)
    os.makedirs(image_folder, exist_ok=True)
    
    logging.info(f"Created output folder: {timestamp_folder}")
    logging.info(f"Created images folder: {image_folder}")
    
    return timestamp_folder, image_folder

def download_image(url, person_index, image_folder):
    """Download image from URL and save to timestamped folder."""
    try:
        # Generate filename
        filename = f"person_{person_index}.jpg"
        image_path = os.path.join(image_folder, filename)
        
        # Download image
        response = requests.get(url)
        response.raise_for_status()
        
        # Get the actual image URL from the API response
        if url.startswith('https://dog.ceo/api/'):
            try:
                image_data = response.json()
                if 'message' in image_data:
                    actual_url = image_data['message']
                    # Download the actual image
                    response = requests.get(actual_url)
                    response.raise_for_status()
            except Exception as e:
                logging.error(f"Error parsing dog API response: {str(e)}")
                return None
        
        # Verify content type is an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            logging.error(f"Invalid content type for image: {content_type}")
            return None
        
        # Save image
        with open(image_path, 'wb') as f:
            f.write(response.content)
        
        logging.info(f"Successfully downloaded image to: {image_path}")
        return image_path
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error downloading image {url}: {str(e)}")
    except Exception as e:
        logging.error(f"Error downloading image {url}: {str(e)}")
        logging.debug(traceback.format_exc())
    return None

def generate_pdf(data, selected_font, output_folder, image_folder):
    """Generate PDF with the given data and font."""
    logging.info(f"Starting PDF generation with font: {selected_font}")
    
    try:
        # Initialize PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Constants for layout
        CONTACTS_PER_PAGE = 5
        PAGE_WIDTH = 210  # A4 width in mm
        PAGE_HEIGHT = 297  # A4 height in mm
        LEFT_MARGIN = 10
        RIGHT_MARGIN = 10
        TOP_MARGIN = 20
        BOTTOM_MARGIN = 20
        IMAGE_WIDTH = 30
        IMAGE_HEIGHT = 30
        TEXT_LEFT_MARGIN = LEFT_MARGIN + IMAGE_WIDTH + 5
        CONTACT_HEIGHT = (PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN) / CONTACTS_PER_PAGE
        LINE_HEIGHT = 5

        # Add timestamp to first page
        pdf.add_page()
        pdf.set_font("Helvetica", 'I', 8)
        pdf.cell(0, 5, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        pdf.add_page()

        # Process each person
        for idx, person in enumerate(data['people'], 1):
            try:
                # Calculate position for new contact
                contact_position = (idx - 1) % CONTACTS_PER_PAGE
                if contact_position == 0 and idx > 1:
                    pdf.add_page()

                # Calculate Y position for this contact
                y_position = TOP_MARGIN + (contact_position * CONTACT_HEIGHT)
                current_y = y_position

                # Download and add image
                image_url = person['image']
                image_path = download_image(image_url, idx, image_folder)
                
                if image_path and os.path.exists(image_path):
                    try:
                        pdf.image(image_path, x=LEFT_MARGIN, y=current_y, 
                                w=IMAGE_WIDTH, h=IMAGE_HEIGHT)
                        logging.debug(f"Added image to PDF: {image_path}")
                    except Exception as e:
                        logging.error(f"Error adding image to PDF: {str(e)}")

                # Set position for text (to the right of image)
                pdf.set_xy(TEXT_LEFT_MARGIN, current_y)

                # Add name (new!)
                pdf.set_font("Helvetica", 'B', 14)
                name = person.get('name', 'Name not specified')
                pdf.cell(0, LINE_HEIGHT, txt=str(name), 
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                # Add location
                pdf.set_xy(TEXT_LEFT_MARGIN, pdf.get_y())
                pdf.set_font("Helvetica", 'B', 12)
                location = person.get('location', 'Location not specified')
                pdf.cell(0, LINE_HEIGHT, txt=str(location), 
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                # Add phone
                pdf.set_xy(TEXT_LEFT_MARGIN, pdf.get_y())
                pdf.set_font("Helvetica", '', 10)
                phone = person.get('phone', 'Phone not specified')
                pdf.cell(0, LINE_HEIGHT, txt=f"Phone: {phone}", 
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                # Add description (with word wrap)
                pdf.set_xy(TEXT_LEFT_MARGIN, pdf.get_y())
                pdf.set_font("Helvetica", '', 8)
                description = person.get('description', 'No description available')
                
                # Calculate available width for description
                available_width = PAGE_WIDTH - TEXT_LEFT_MARGIN - RIGHT_MARGIN
                
                # Calculate available height for description
                available_height = CONTACT_HEIGHT - (pdf.get_y() - current_y) - 5
                
                # Split description to fit available space
                pdf.multi_cell(available_width, LINE_HEIGHT, txt=str(description)[:500] + "...")

                # Add separator line
                if contact_position < CONTACTS_PER_PAGE - 1:
                    pdf.line(LEFT_MARGIN, y_position + CONTACT_HEIGHT - 2,
                            PAGE_WIDTH - RIGHT_MARGIN, y_position + CONTACT_HEIGHT - 2)

                logging.debug(f"Added person {idx} to PDF")
                
            except Exception as e:
                logging.error(f"Error processing person {idx}: {str(e)}")
                logging.debug(traceback.format_exc())
                continue
        
        # Save PDF to output folder
        output_filename = os.path.join(output_folder, f"contacts.pdf")
        pdf.output(output_filename)
        logging.info(f"PDF generated successfully: {output_filename}")
        return output_filename
        
    except Exception as e:
        logging.error(f"Error in PDF generation: {str(e)}")
        logging.debug(traceback.format_exc())
        raise

def main():
    try:
        # Initialize logging
        setup_logging()
        logging.info("=== Application Started ===")
        
        # Log system information
        log_system_info()
        
        # Create timestamped folders
        output_folder, image_folder = create_timestamped_folders()
        
        # Load JSON data
        try:
            with open('response.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
            logging.info("Successfully loaded JSON data")
        except Exception as e:
            logging.error(f"Error reading JSON file: {str(e)}")
            logging.debug(traceback.format_exc())
            return 1

        # Generate PDF
        try:
            output_file = generate_pdf(data, "Helvetica", output_folder, image_folder)
            print(f"PDF generated successfully as '{output_file}'")
            logging.info(f"PDF generation completed: {output_file}")
            
        except Exception as e:
            logging.error(f"Error generating output: {str(e)}")
            logging.debug(traceback.format_exc())
            return 1
            
    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
        logging.debug(traceback.format_exc())
        return 1
    
    logging.info("=== Application Completed Successfully ===")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
