from pydantic import BaseModel, Field, HttpUrl


class ResumeURLRequest(BaseModel):
    """Request model for resume file URL"""
    resume_url: HttpUrl = Field(..., description="URL to the resume file (PDF, DOC, or DOCX)")


class CoverLetterRequest(BaseModel):
    """Request model for cover letter generation"""
    resume_url: HttpUrl = Field(..., description="URL to the resume file (PDF, DOC, or DOCX)")
    job_description: str = Field(..., description="Full job description in plain text", min_length=30)

