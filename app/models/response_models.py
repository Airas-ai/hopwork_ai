from pydantic import BaseModel, Field
from typing import Optional, List


class ATSScoreResponse(BaseModel):
    """Response model for ATS score evaluation"""
    score: float = Field(..., description="ATS score out of 100", ge=0, le=100)
    feedback: str = Field(..., description="Detailed feedback about the resume")
    strengths: List[str] = Field(default_factory=list, description="List of resume strengths")
    weaknesses: List[str] = Field(default_factory=list, description="List of resume weaknesses")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    file_type: str = Field(..., description="Type of file that was processed")


class CoverLetterResponse(BaseModel):
    """Response model for generated cover letter"""
    cover_letter: str = Field(..., description="Generated cover letter text")
    model_used: str = Field(..., description="Gemini model used for generation")
    job_title: Optional[str] = Field(None, description="Detected or provided job title")
    company_name: Optional[str] = Field(None, description="Detected or provided company name")
    notes: Optional[str] = Field(None, description="Additional notes or tips for customization")


class ATSResumeResponse(BaseModel):
    """Response model for regenerated ATS-optimized resume"""
    regenerated_resume: str = Field(..., description="ATS-optimized resume content in plain text")
    model_used: str = Field(..., description="Gemini model used for regeneration")
    notes: Optional[str] = Field(
        None,
        description="Optional notes about what was improved (formatting, keywords, structure, etc.)",
    )

