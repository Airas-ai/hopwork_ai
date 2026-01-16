from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.response_models import ATSScoreResponse, CoverLetterResponse, ATSResumeResponse
from app.models.request_models import ResumeURLRequest, CoverLetterRequest
from app.utils.file_processor import FileProcessor
from app.utils.gemini_service import GeminiService
from app.utils.url_downloader import URLDownloader
from config import settings

# Initialize services
file_processor = FileProcessor()
url_downloader = URLDownloader()
gemini_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    global gemini_service
    try:
        gemini_service = GeminiService()
    except ValueError as e:
        print(f"Warning: {e}")
    yield
    # Shutdown (if needed)
    pass


app = FastAPI(
    title="Resume AI Assistant API",
    description=(
        "API for evaluating resumes, providing ATS compatibility scores, "
        "generating tailored cover letters, and regenerating ATS-optimized resumes "
        "using Gemini models."
    ),
    version="1.2.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Resume ATS Score API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gemini_configured": settings.is_gemini_configured
    }


@app.post("/resume_ats_score", response_model=ATSScoreResponse)
async def resume_ats_score(request: ResumeURLRequest):
    """
    Evaluate a resume file from URL and return ATS compatibility score
    
    Args:
        request: ResumeURLRequest with resume_url (URL to doc, docx, or pdf file)
        
    Returns:
        ATSScoreResponse with score, feedback, strengths, weaknesses, and recommendations
    """
    # Validate Gemini service is configured
    if not gemini_service:
        raise HTTPException(
            status_code=500,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY in environment variables."
        )
    
    try:
        # Download file from URL
        file_content, filename = await url_downloader.download_file(str(request.resume_url))
        
        # Extract text from file
        try:
            resume_text = FileProcessor.extract_text(file_content, filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract sufficient text from the resume file. Please ensure the file is not corrupted."
            )
        
        # Analyze resume with Gemini Pro
        try:
            analysis_result = gemini_service.analyze_resume_for_ats(resume_text)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")
        
        # Get file type
        file_type = FileProcessor.get_file_type(filename)
        
        # Return response
        return ATSScoreResponse(
            score=analysis_result["score"],
            feedback=analysis_result["feedback"],
            strengths=analysis_result["strengths"],
            weaknesses=analysis_result["weaknesses"],
            recommendations=analysis_result["recommendations"],
            file_type=file_type
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@app.post("/cover_letter_generator", response_model=CoverLetterResponse)
async def cover_letter_generator(request: CoverLetterRequest):
    """
    Generate a customized cover letter based on job description and resume.

    Args:
        request: CoverLetterRequest with resume_url and job_description

    Returns:
        CoverLetterResponse with generated cover letter and metadata.
    """
    if not gemini_service:
        raise HTTPException(
            status_code=500,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY in environment variables.",
        )

    try:
        # Download file from URL
        file_content, filename = await url_downloader.download_file(str(request.resume_url))

        # Extract text from file
        try:
            resume_text = FileProcessor.extract_text(file_content, filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract sufficient text from the resume file. "
                    "Please ensure the file is not corrupted."
                ),
            )

        if not request.job_description or len(request.job_description.strip()) < 30:
            raise HTTPException(
                status_code=400,
                detail="Job description is too short. Please provide a detailed job description.",
            )

        try:
            result = gemini_service.generate_cover_letter(
                resume_text=resume_text, job_description=request.job_description
            )
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"Error generating cover letter: {str(e)}")

        return CoverLetterResponse(
            cover_letter=result["cover_letter"],
            model_used=result["model_used"],
            job_title=result.get("job_title") or None,
            company_name=result.get("company_name") or None,
            notes=result.get("notes") or None,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while generating cover letter: {str(e)}",
        )


@app.post("/ats_resume_generator", response_model=ATSResumeResponse)
async def ats_resume_generator(request: ResumeURLRequest):
    """
    Regenerate a resume to be ATS-friendly and better structured.

    Args:
        request: ResumeURLRequest with resume_url (URL to pdf, doc, or docx file)

    Returns:
        ATSResumeResponse with regenerated resume text and metadata.
    """
    if not gemini_service:
        raise HTTPException(
            status_code=500,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY in environment variables.",
        )

    try:
        # Download file from URL
        file_content, filename = await url_downloader.download_file(str(request.resume_url))

        # Extract text from file
        try:
            resume_text = FileProcessor.extract_text(file_content, filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract sufficient text from the resume file. "
                    "Please ensure the file is not corrupted."
                ),
            )

        try:
            result = gemini_service.generate_ats_optimized_resume(resume_text=resume_text)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"Error regenerating resume: {str(e)}")

        return ATSResumeResponse(
            regenerated_resume=result["regenerated_resume"],
            model_used=result["model_used"],
            notes=result.get("notes") or None,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while regenerating resume: {str(e)}",
        )

