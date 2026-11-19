import os
import shutil
from uuid import uuid4
from fastapi import HTTPException, UploadFile, status
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

load_dotenv()

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists("/app/static"):
    STATIC_DIR = "/app/static"
else:
    STATIC_DIR = os.path.join(BASE_DIR, "static")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".pdf"}

def get_static_dir(folder_name: str = "") -> str:
    target_dir = os.path.join(STATIC_DIR, folder_name) if folder_name else STATIC_DIR
    os.makedirs(target_dir, exist_ok=True)
    return target_dir

def save_upload_file(upload_file: UploadFile, folder_name: str) -> str:
    if not upload_file or not upload_file.filename:
        return None

    ext = os.path.splitext(upload_file.filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if os.getenv("CLOUDINARY_CLOUD_NAME") and os.getenv("CLOUDINARY_API_KEY"):
        try:
            upload_file.file.seek(0)
            result = cloudinary.uploader.upload(
                upload_file.file,
                folder=f"nawiri/{folder_name}",
                resource_type="auto"
            )
            return result.get("secure_url")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload to Cloudinary: {str(e)}"
            )
    else:
        folder_path = get_static_dir(folder_name)
        filename = f"{uuid4().hex}{ext}"
        file_path = os.path.join(folder_path, filename)
        try:
            upload_file.file.seek(0)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
        return f"/static/{folder_name}/{filename}"

def delete_file(file_url_or_path: str, folder_name: str = None) -> bool:
    if not file_url_or_path:
        return False
        
    if "cloudinary.com" in file_url_or_path:
        try:
            parts = file_url_or_path.split("/")
            if "upload" in parts:
                upload_idx = parts.index("upload")
                
                # Extract resource_type (image, video, raw) from URL
                resource_type = "image"
                if upload_idx > 0:
                    resource_type = parts[upload_idx - 1]

                if parts[upload_idx + 1].startswith("v") and parts[upload_idx + 1][1:].isdigit():
                    public_id_with_ext = "/".join(parts[upload_idx + 2:])
                else:
                    public_id_with_ext = "/".join(parts[upload_idx + 1:])
                    
                public_id = os.path.splitext(public_id_with_ext)[0]
                cloudinary.uploader.destroy(public_id, resource_type=resource_type)
                return True
        except Exception as e:
            print(f"Warning: Could not delete from Cloudinary: {e}")
            return False

    filename = os.path.basename(file_url_or_path.split("?")[0])

    if folder_name:
        target_path = os.path.join(STATIC_DIR, folder_name, filename)
    else:
        parts = file_url_or_path.replace("\\", "/",).strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "static":
            target_path = os.path.join(STATIC_DIR, parts[1], filename)
        else:
            target_path = os.path.join(STATIC_DIR, filename)

    if os.path.exists(target_path):
        try:
            os.remove(target_path)
            return True
        except Exception as e:
            print(f"Warning: Could not delete file at {target_path}: {e}")
            return False
    return False
