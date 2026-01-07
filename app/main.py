from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from app.models.response_models import ATSScoreResponse, CoverLetterResponse, ATSResumeResponse
from app.utils.file_processor import FileProcessor
from app.utils.gemini_service import GeminiService
from config import settings

# Initialize services
file_processor = FileProcessor()
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
async def resume_ats_score(file: UploadFile = File(...)):
    """
    Evaluate a resume file and return ATS compatibility score
    
    Args:
        file: Resume file (doc, docx, or pdf)
        
    Returns:
        ATSScoreResponse with score, feedback, strengths, weaknesses, and recommendations
    """
    # Validate Gemini service is configured
    if not gemini_service:
        raise HTTPException(
            status_code=500,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY in environment variables."
        )
    
    # Validate file extension
    if not FileProcessor.is_valid_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(FileProcessor.ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    try:
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > FileProcessor.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {FileProcessor.MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Extract text from file
        try:
            resume_text = FileProcessor.extract_text(file_content, file.filename)
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
        file_type = FileProcessor.get_file_type(file.filename)
        
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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@app.post("/cover_letter_generator", response_model=CoverLetterResponse)
async def cover_letter_generator(
    job_description: str = Form(..., description="Job description text"),
    file: UploadFile = File(..., description="Candidate resume file (pdf, doc, or docx)"),
):
    """
    Generate a customized cover letter based on job description and resume.

    Args:
        job_description: Full job description in plain text.
        file: Resume file (pdf, doc, or docx).

    Returns:
        CoverLetterResponse with generated cover letter and metadata.
    """
    if not gemini_service:
        raise HTTPException(
            status_code=500,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY in environment variables.",
        )

    if not FileProcessor.is_valid_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(FileProcessor.ALLOWED_EXTENSIONS)}",
        )

    try:
        file_content = await file.read()

        if len(file_content) > FileProcessor.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {FileProcessor.MAX_FILE_SIZE / (1024*1024)}MB",
            )

        try:
            resume_text = FileProcessor.extract_text(file_content, file.filename)
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

        if not job_description or len(job_description.strip()) < 30:
            raise HTTPException(
                status_code=400,
                detail="Job description is too short. Please provide a detailed job description.",
            )

        try:
            result = gemini_service.generate_cover_letter(
                resume_text=resume_text, job_description=job_description
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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while generating cover letter: {str(e)}",
        )


@app.post("/ats_resume_generator", response_model=ATSResumeResponse)
async def ats_resume_generator(
    file: UploadFile = File(..., description="Candidate resume file (pdf, doc, or docx)"),
):
    """
    Regenerate a resume to be ATS-friendly and better structured.

    Args:
        file: Resume file (pdf, doc, or docx).

    Returns:
        ATSResumeResponse with regenerated resume text and metadata.
    """
    if not gemini_service:
        raise HTTPException(
            status_code=500,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY in environment variables.",
        )

    if not FileProcessor.is_valid_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(FileProcessor.ALLOWED_EXTENSIONS)}",
        )

    try:
        file_content = await file.read()

        if len(file_content) > FileProcessor.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {FileProcessor.MAX_FILE_SIZE / (1024*1024)}MB",
            )

        try:
            resume_text = FileProcessor.extract_text(file_content, file.filename)
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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while regenerating resume: {str(e)}",
        )

