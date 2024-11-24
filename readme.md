# JSON Contact List Processor

A Python application that processes a JSON contact list and generates both PDF and HTML outputs with proper formatting and image handling. The application downloads profile images, organizes them in timestamped folders, and creates professional-looking documents.

## Repository
[digest-json-and-create-a-webpage](https://github.com/pleabargain/digest-json-and-create-a-webpage)

video

https://www.youtube.com/watch?v=dIt15HE9k4Q



## Features
- Processes JSON contact data
- Downloads and manages profile images
- Generates formatted PDF output (5 contacts per page)
- Creates responsive HTML output
- Includes timestamped file organization
- Comprehensive logging system
- Error handling and debugging support
- Font selection capability
- Proper image aspect ratio handling

## Requirements
```python
fpdf==2.7.6
matplotlib>=3.7.1
requests>=2.31.0
```

## Installation
1. Clone the repository:
```bash
git clone https://github.com/pleabargain/digest-json-and-create-a-webpage.git
cd digest-json-and-create-a-webpage
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage
1. Prepare your JSON data file (`response.json`) with the following structure:
```json
{
  "people": [
    {
      "name": "Person Name",
      "phone": "Phone Number",
      "location": "Location",
      "image": "Image URL",
      "description": "Description text..."
    }
  ]
}
```

2. Run the application:
```bash
python main.py
```

## Output Structure
The application creates a timestamped folder structure for each run:
```
output_YYYYMMDD_HHMMSS/
    ├── images/
    │   ├── person_1.jpg
    │   ├── person_2.jpg
    │   └── ...
    ├── contacts.pdf
    └── index.html
```

## Logging
- Logs are stored in the `logs` directory
- Each run creates a timestamped log file
- Comprehensive debug information is available in logs

## Error Handling
- Graceful handling of network errors
- Image download fallbacks
- Font selection fallbacks
- Comprehensive error logging

## Development
- Python 3.11+ recommended
- Uses FPDF for PDF generation
- Matplotlib for font management
- Requests for image downloads

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

