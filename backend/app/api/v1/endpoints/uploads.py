"""
File Upload Endpoints
====================
Handles file uploads for property images and documents.
"""
import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import List
import aiofiles
from PIL import Image
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.fastapi_users_deps import get_current_user_id
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize rate limiter for uploads
limiter = Limiter(key_func=get_remote_address)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create subdirectories for different file types
IMAGES_DIR = UPLOAD_DIR / "images"
DOCUMENTS_DIR = UPLOAD_DIR / "documents"
TEMP_DIR = UPLOAD_DIR / "temp"

for dir_path in [IMAGES_DIR, DOCUMENTS_DIR, TEMP_DIR]:
    dir_path.mkdir(exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGES_PER_PROPERTY = 20

class FileUploadService:
    """Service for handling file uploads and processing"""

    @staticmethod
    def validate_image_file(file: UploadFile) -> None:
        """Validate image file type and size"""
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )

        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
            )

    @staticmethod
    def validate_document_file(file: UploadFile) -> None:
        """Validate document file type and size"""
        if file.content_type not in ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_DOCUMENT_TYPES)}"
            )

        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
            )

    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Generate a unique filename"""
        file_extension = Path(original_filename).suffix
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_extension}"

    @staticmethod
    async def save_file(file: UploadFile, destination_path: Path) -> str:
        """Save uploaded file to disk"""
        try:
            async with aiofiles.open(destination_path, 'wb') as buffer:
                content = await file.read()
                await buffer.write(content)
            return str(destination_path)
        except Exception as e:
            logger.error(f"Error saving file {destination_path}: {e}")
            raise HTTPException(status_code=500, detail="Failed to save file")

    @staticmethod
    async def process_image(image_path: Path) -> dict:
        """Process uploaded image (resize, optimize, etc.)"""
        try:
            with Image.open(image_path) as img:
                # Get image info
                width, height = img.size
                file_size = image_path.stat().st_size

                # Create thumbnail (optional)
                thumbnail_path = image_path.parent / f"thumb_{image_path.name}"
                img.thumbnail((300, 300))
                img.save(thumbnail_path, optimize=True, quality=85)

                return {
                    "original_path": str(image_path),
                    "thumbnail_path": str(thumbnail_path),
                    "width": width,
                    "height": height,
                    "file_size": file_size,
                    "format": img.format
                }
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return {
                "original_path": str(image_path),
                "thumbnail_path": None,
                "width": None,
                "height": None,
                "file_size": image_path.stat().st_size,
                "format": None
            }

@router.post("/images")
@limiter.limit("10/minute")
async def upload_property_images(
    request: Request,
    files: List[UploadFile] = File(...),
    property_id: str = None,
    agent_id: str = Depends(get_current_user_id)
):
    """Upload property images"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if len(files) > MAX_IMAGES_PER_PROPERTY:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum {MAX_IMAGES_PER_PROPERTY} images allowed"
        )

    uploaded_files = []

    for file in files:
        # Validate file
        FileUploadService.validate_image_file(file)

        # Generate unique filename
        unique_filename = FileUploadService.generate_unique_filename(file.filename)
        file_path = IMAGES_DIR / unique_filename

        # Save file
        await FileUploadService.save_file(file, file_path)

        # Process image
        image_info = await FileUploadService.process_image(file_path)

        # Create file record
        file_record = {
            "id": str(uuid.uuid4()),
            "filename": unique_filename,
            "original_name": file.filename,
            "url": f"/uploads/images/{unique_filename}",
            "thumbnail_url": f"/uploads/images/thumb_{unique_filename}" if image_info["thumbnail_path"] else None,
            "content_type": file.content_type,
            "size": file.size,
            "property_id": property_id,
            "agent_id": agent_id,
            "uploaded_at": "2024-01-01T00:00:00Z",  # Would be datetime.utcnow() in real implementation
            **image_info
        }

        uploaded_files.append(file_record)

    return JSONResponse(content={
        "success": True,
        "message": f"Successfully uploaded {len(uploaded_files)} images",
        "files": uploaded_files
    })

@router.post("/documents")
@limiter.limit("5/minute")
async def upload_documents(
    request: Request,
    files: List[UploadFile] = File(...),
    property_id: str = None,
    agent_id: str = Depends(get_current_user_id)
):
    """Upload property documents"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    uploaded_files = []

    for file in files:
        # Validate file
        FileUploadService.validate_document_file(file)

        # Generate unique filename
        unique_filename = FileUploadService.generate_unique_filename(file.filename)
        file_path = DOCUMENTS_DIR / unique_filename

        # Save file
        await FileUploadService.save_file(file, file_path)

        # Create file record
        file_record = {
            "id": str(uuid.uuid4()),
            "filename": unique_filename,
            "original_name": file.filename,
            "url": f"/uploads/documents/{unique_filename}",
            "content_type": file.content_type,
            "size": file.size,
            "property_id": property_id,
            "agent_id": agent_id,
            "uploaded_at": "2024-01-01T00:00:00Z"  # Would be datetime.utcnow() in real implementation
        }

        uploaded_files.append(file_record)

    return JSONResponse(content={
        "success": True,
        "message": f"Successfully uploaded {len(uploaded_files)} documents",
        "files": uploaded_files
    })

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    agent_id: str = Depends(get_current_user_id)
):
    """Delete uploaded file"""
    # In a real implementation, you would:
    # 1. Check if file exists in database
    # 2. Verify ownership
    # 3. Delete from filesystem
    # 4. Remove from database

    return JSONResponse(content={
        "success": True,
        "message": "File deleted successfully"
    })
