import httpx
from typing import Tuple
from app.utils.file_processor import FileProcessor


class URLDownloader:
    """Utility class for downloading files from URLs"""
    
    MAX_FILE_SIZE = FileProcessor.MAX_FILE_SIZE
    TIMEOUT = 30.0  # 30 seconds timeout
    
    @staticmethod
    async def download_file(url: str) -> Tuple[bytes, str]:
        """
        Download a file from a URL and return its content and filename
        
        Args:
            url: URL to the file
            
        Returns:
            Tuple of (file_content: bytes, filename: str)
            
        Raises:
            ValueError: If download fails or file is invalid
        """
        try:
            async with httpx.AsyncClient(timeout=URLDownloader.TIMEOUT) as client:
                response = await client.get(url)
                response.raise_for_status()  # Raise exception for bad status codes
                
                # Get filename from URL or Content-Disposition header
                filename = URLDownloader._extract_filename(url, response.headers)
                
                # Validate file size
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > URLDownloader.MAX_FILE_SIZE:
                    raise ValueError(
                        f"File size ({int(content_length) / (1024*1024):.2f}MB) exceeds "
                        f"maximum allowed size of {URLDownloader.MAX_FILE_SIZE / (1024*1024)}MB"
                    )
                
                file_content = response.content
                
                # Validate actual downloaded size
                if len(file_content) > URLDownloader.MAX_FILE_SIZE:
                    raise ValueError(
                        f"File size ({len(file_content) / (1024*1024):.2f}MB) exceeds "
                        f"maximum allowed size of {URLDownloader.MAX_FILE_SIZE / (1024*1024)}MB"
                    )
                
                # Validate file extension
                if not FileProcessor.is_valid_extension(filename):
                    raise ValueError(
                        f"Invalid file type. Allowed types: {', '.join(FileProcessor.ALLOWED_EXTENSIONS)}"
                    )
                
                return file_content, filename
                
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Failed to download file: HTTP {e.response.status_code} - {e.response.text}")
        except httpx.TimeoutException:
            raise ValueError(f"Request timed out after {URLDownloader.TIMEOUT} seconds")
        except httpx.RequestError as e:
            raise ValueError(f"Failed to download file: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error downloading file: {str(e)}")
    
    @staticmethod
    def _extract_filename(url: str, headers: dict) -> str:
        """Extract filename from URL or Content-Disposition header"""
        # Try Content-Disposition header first
        content_disposition = headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"\'')
            if filename:
                return filename
        
        # Fallback to URL path
        url_path = url.split('?')[0]  # Remove query parameters
        filename = url_path.split('/')[-1]
        
        # If no extension, try to infer from Content-Type
        if '.' not in filename:
            content_type = headers.get('content-type', '')
            if 'pdf' in content_type.lower():
                filename = 'resume.pdf'
            elif 'msword' in content_type.lower() or 'wordprocessingml' in content_type.lower():
                filename = 'resume.docx'
            else:
                filename = 'resume.pdf'  # Default to PDF
        
        return filename

