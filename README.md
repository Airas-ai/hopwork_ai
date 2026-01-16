# Hopwork AI - Resume ATS Score API

FastAPI backend for evaluating resumes and providing ATS (Applicant Tracking System) compatibility scores using Google's Gemini Pro.

## Features

- Resume file processing from URLs (PDF, DOCX, DOC)
- Text extraction from multiple file formats
- ATS score evaluation using Gemini Pro
- Customized cover letter generation
- ATS-optimized resume regeneration
- Detailed feedback, strengths, weaknesses, and recommendations

## Setup

### Prerequisites

- Python 3.8+
- Google Gemini API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd hopwork_ai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

5. Run the application:

**Standard way (recommended):**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Alternative (using convenience script):**
```bash
python run.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### POST /resume_ats_score

Evaluate a resume file from URL and return ATS compatibility score.

**Request:**
- Method: POST
- Content-Type: application/json
- Body: JSON with `resume_url` field containing the URL to the resume file

**Request Body:**
```json
{
  "resume_url": "https://hopwork-bucket.s3.us-east-1.amazonaws.com/uploads/resume.pdf"
}
```

**Response:**
```json
{
  "score": 85.5,
  "feedback": "Detailed feedback about the resume...",
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"],
  "recommendations": ["recommendation1", "recommendation2"],
  "file_type": "pdf"
}
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/resume_ats_score" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"resume_url": "https://hopwork-bucket.s3.us-east-1.amazonaws.com/uploads/resume.pdf"}'
```

### POST /cover_letter_generator

Generate a customized cover letter based on a job description and a resume file from URL.

**Request:**
- Method: POST
- Content-Type: application/json
- Body: JSON with `resume_url` and `job_description` fields

**Request Body:**
```json
{
  "resume_url": "https://hopwork-bucket.s3.us-east-1.amazonaws.com/uploads/resume.pdf",
  "job_description": "We are looking for a Senior Software Engineer with experience in..."
}
```

**Response:**
```json
{
  "cover_letter": "Full generated cover letter text...",
  "model_used": "gemini-2.5-pro",
  "job_title": "Senior Software Engineer",
  "company_name": "Acme Corp",
  "notes": "You can tweak the second paragraph to mention your latest project."
}
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/cover_letter_generator" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_url": "https://hopwork-bucket.s3.us-east-1.amazonaws.com/uploads/resume.pdf",
    "job_description": "We are looking for a Senior Software Engineer..."
  }'
```

### POST /ats_resume_generator

Regenerate a resume from URL to be ATS-friendly and better structured.

**Request:**
- Method: POST
- Content-Type: application/json
- Body: JSON with `resume_url` field

**Request Body:**
```json
{
  "resume_url": "https://hopwork-bucket.s3.us-east-1.amazonaws.com/uploads/resume.pdf"
}
```

**Response:**
```json
{
  "regenerated_resume": "ATS-optimized resume content...",
  "model_used": "gemini-2.5-pro",
  "notes": "Improved formatting, structure, and keyword optimization."
}
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/ats_resume_generator" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"resume_url": "https://hopwork-bucket.s3.us-east-1.amazonaws.com/uploads/resume.pdf"}'
```

## Project Structure

```
hopwork_ai/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request_models.py   # Request Pydantic models
│   │   └── response_models.py  # Response Pydantic models
│   └── utils/
│       ├── __init__.py
│       ├── file_processor.py    # File processing utilities
│       ├── gemini_service.py    # Gemini Pro integration
│       └── url_downloader.py    # URL file download utilities
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
└── README.md
```

## Supported File Formats

- PDF (.pdf)
- Microsoft Word (.docx)
- Legacy Word (.doc) - Note: Requires conversion to DOCX or PDF

## Error Handling

The API includes comprehensive error handling for:
- Invalid file URLs or unreachable URLs
- Invalid file types
- File size limits (10MB max)
- Text extraction failures
- Gemini API errors
- Missing configuration
- Network timeouts (30 seconds)

## License

MIT