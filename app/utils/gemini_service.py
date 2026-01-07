import google.generativeai as genai
import json
import re
from typing import Dict, Any
from config import settings


class GeminiService:
    """Service for interacting with Google Gemini Pro API"""
    
    def __init__(self):
        if not settings.is_gemini_configured:
            raise ValueError("GEMINI_API_KEY is not configured. Please set it in your .env file.")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # List of available models based on API key access
        # Order: best quality first, then faster/cheaper alternatives
        self.model_names = [
            "gemini-2.5-pro",           # Best quality for complex analysis
            "gemini-2.5-flash",         # Fast and efficient
            "gemini-pro-latest",        # Stable fallback
            "gemini-flash-latest",       # Fast fallback
            "gemini-2.0-flash",         # Alternative option
        ]
        
        # Try to get available models and filter to only those that support generateContent
        try:
            all_models = genai.list_models()
            available_model_names = []
            for model in all_models:
                model_name = model.name.split('/')[-1]
                # Check if model supports generateContent
                if 'generateContent' in model.supported_generation_methods:
                    available_model_names.append(model_name)
            
            # Filter our preferred list to only include available models
            self.model_names = [
                name for name in self.model_names 
                if name in available_model_names
            ]
            
            # If none of our preferred models are available, use any available model
            if not self.model_names and available_model_names:
                self.model_names = available_model_names[:5]  # Take first 5 available
        except Exception:
            # If listing models fails, use our default list
            pass
        
        if not self.model_names:
            raise ValueError(
                "No Gemini models available. Please check your API key permissions."
            )
        
        # Initialize with first model name (will be tried during first API call)
        self.model = genai.GenerativeModel(self.model_names[0])
        self.current_model_index = 0
    
    def analyze_resume_for_ats(self, resume_text: str) -> Dict[str, Any]:
        """
        Analyze resume text and generate ATS score with detailed feedback
        
        Args:
            resume_text: Extracted text from resume file
            
        Returns:
            Dictionary containing score, feedback, strengths, weaknesses, and recommendations
        """
        prompt = f"""You are an expert ATS (Applicant Tracking System) resume analyzer. 
Analyze the following resume and provide a comprehensive evaluation.

Resume Text:
{resume_text}

Please provide your analysis in the following JSON format:
{{
    "score": <number between 0-100>,
    "feedback": "<detailed feedback about the resume's ATS compatibility>",
    "strengths": ["<strength1>", "<strength2>", ...],
    "weaknesses": ["<weakness1>", "<weakness2>", ...],
    "recommendations": ["<recommendation1>", "<recommendation2>", ...]
}}

Consider the following ATS evaluation criteria:
1. Keyword optimization and relevance
2. Formatting and structure (ATS-friendly formatting)
3. Section completeness (contact info, work experience, education, skills)
4. Use of standard section headers
5. File format compatibility
6. Absence of graphics/images that ATS can't read
7. Proper use of dates and formatting
8. Quantifiable achievements and metrics
9. Industry-specific keywords
10. Overall readability and parsing by ATS systems

Provide a score from 0-100 where:
- 90-100: Excellent ATS compatibility
- 70-89: Good ATS compatibility with minor improvements needed
- 50-69: Fair ATS compatibility, significant improvements recommended
- 0-49: Poor ATS compatibility, major overhaul needed

Respond ONLY with valid JSON, no additional text or markdown formatting."""

        # Try models until one works
        response = None
        last_error = None
        
        for i in range(len(self.model_names)):
            try:
                # Try current model or next one if previous failed
                if i > 0:
                    self.model = genai.GenerativeModel(self.model_names[i])
                    self.current_model_index = i
                
                response = self.model.generate_content(prompt)
                break  # Success, exit loop
            except Exception as e:
                last_error = e
                # If this is the last model, raise error
                if i == len(self.model_names) - 1:
                    raise ValueError(
                        f"Error calling Gemini API: {str(e)}. "
                        f"Tried models: {', '.join(self.model_names)}. "
                        f"Please check your API key permissions."
                    )
                continue
        
        if response is None:
            raise ValueError(f"Failed to get response from any Gemini model. Last error: {str(last_error)}")
        
        try:
            # Handle both old and new API response formats
            if hasattr(response, 'text'):
                response_text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text.strip()
            else:
                response_text = str(response).strip()
            
            # Clean the response to extract JSON
            # Remove markdown code blocks if present
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*', '', response_text)
            response_text = response_text.strip()
            
            # Parse JSON response
            result = json.loads(response_text)
            
            # Validate and ensure score is within range
            score = float(result.get("score", 0))
            score = max(0, min(100, score))  # Clamp between 0-100
            
            return {
                "score": round(score, 2),
                "feedback": result.get("feedback", "No feedback provided"),
                "strengths": result.get("strengths", []),
                "weaknesses": result.get("weaknesses", []),
                "recommendations": result.get("recommendations", [])
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing Gemini response: {str(e)}")

    def generate_cover_letter(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """
        Generate a customized cover letter based on resume and job description.

        Returns:
            Dict with cover_letter text and metadata.
        """
        prompt = f"""You are an expert career coach and professional cover letter writer.

Use the following candidate resume and job description to write a highly tailored, ATS-friendly,
and compelling cover letter that the candidate can use to apply for this specific role.

--- RESUME ---
{resume_text}

--- JOB DESCRIPTION ---
{job_description}

Write a personalized cover letter that:
- Clearly aligns the candidate's experience with the job requirements
- Highlights 3–5 key achievements that match the role
- Uses a professional but warm tone
- Is concise (around 350–500 words)
- Avoids repeating the resume verbatim
- Avoids making up fake companies or roles

Try to infer the job title and company name from the job description if possible.

Return your answer in the following JSON format ONLY:
{{
  "cover_letter": "<full cover letter text>",
  "job_title": "<detected or inferred job title, or empty string if unknown>",
  "company_name": "<detected or inferred company name, or empty string if unknown>",
  "notes": "<optional notes or suggestions for the candidate, can be empty>"
}}"""

        # Try models until one works
        response = None
        last_error = None

        for i in range(len(self.model_names)):
            try:
                if i > 0:
                    self.model = genai.GenerativeModel(self.model_names[i])
                    self.current_model_index = i

                response = self.model.generate_content(prompt)
                break
            except Exception as e:
                last_error = e
                if i == len(self.model_names) - 1:
                    raise ValueError(
                        f"Error calling Gemini API for cover letter: {str(e)}. "
                        f"Tried models: {', '.join(self.model_names)}. "
                        f"Please check your API key permissions."
                    )
                continue

        if response is None:
            raise ValueError(f"Failed to get response from any Gemini model. Last error: {str(last_error)}")

        try:
            if hasattr(response, "text"):
                response_text = response.text.strip()
            elif hasattr(response, "candidates") and response.candidates:
                response_text = response.candidates[0].content.parts[0].text.strip()
            else:
                response_text = str(response).strip()

            response_text = re.sub(r"```json\s*", "", response_text)
            response_text = re.sub(r"```\s*", "", response_text)
            response_text = response_text.strip()

            result = json.loads(response_text)

            cover_letter = result.get("cover_letter", "").strip()
            if not cover_letter:
                raise ValueError("Gemini response did not contain a cover_letter field.")

            return {
                "cover_letter": cover_letter,
                "model_used": self.model_names[self.current_model_index],
                "job_title": result.get("job_title") or "",
                "company_name": result.get("company_name") or "",
                "notes": result.get("notes") or "",
            }

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini cover letter response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing Gemini cover letter response: {str(e)}")

    def generate_ats_optimized_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Regenerate the resume to be ATS-optimized and better structured.

        Returns:
            Dict with regenerated resume text and metadata.
        """
        prompt = f"""You are an expert resume writer and ATS optimization specialist.

Take the following resume content and regenerate it to:
- Improve clarity, structure, and readability
- Use standard ATS-friendly section headings (e.g., SUMMARY, EXPERIENCE, EDUCATION, SKILLS)
- Avoid complex tables, columns, images, and graphics
-,Use bullet points where appropriate
- Emphasize quantified achievements and relevant keywords
- Keep the content truthful and do NOT invent new experience or companies
- Preserve all important information from the original resume

--- ORIGINAL RESUME ---
{resume_text}

Return your answer in the following JSON format ONLY:
{{
  "regenerated_resume": "<full regenerated resume in plain text, with clear section headings>",
  "notes": "<brief explanation (2-4 bullet sentences) of the key improvements you made, or empty string>"
}}"""

        # Try models until one works
        response = None
        last_error = None

        for i in range(len(self.model_names)):
            try:
                if i > 0:
                    self.model = genai.GenerativeModel(self.model_names[i])
                    self.current_model_index = i

                response = self.model.generate_content(prompt)
                break
            except Exception as e:
                last_error = e
                if i == len(self.model_names) - 1:
                    raise ValueError(
                        f"Error calling Gemini API for ATS resume generation: {str(e)}. "
                        f"Tried models: {', '.join(self.model_names)}. "
                        f"Please check your API key permissions."
                    )
                continue

        if response is None:
            raise ValueError(f"Failed to get response from any Gemini model. Last error: {str(last_error)}")

        try:
            if hasattr(response, "text"):
                response_text = response.text.strip()
            elif hasattr(response, "candidates") and response.candidates:
                response_text = response.candidates[0].content.parts[0].text.strip()
            else:
                response_text = str(response).strip()

            response_text = re.sub(r"```json\\s*", "", response_text)
            response_text = re.sub(r"```\\s*", "", response_text)
            response_text = response_text.strip()

            result = json.loads(response_text)

            regenerated_resume = result.get("regenerated_resume", "").strip()
            if not regenerated_resume:
                raise ValueError("Gemini response did not contain a regenerated_resume field.")

            return {
                "regenerated_resume": regenerated_resume,
                "model_used": self.model_names[self.current_model_index],
                "notes": result.get("notes") or "",
            }

        except json.JSONDecodeError:
            # Fallback: treat the whole response text as the regenerated resume
            # This avoids failing the request if the model did not follow JSON instructions
            return {
                "regenerated_resume": response_text.strip(),
                "model_used": self.model_names[self.current_model_index],
                "notes": "Model returned non-JSON response; used raw text as regenerated resume.",
            }
        except Exception as e:
            raise ValueError(f"Error processing Gemini ATS resume response: {str(e)}")

