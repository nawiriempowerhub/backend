import os
import shutil
from uuid import uuid4
from fastapi import HTTPException, UploadFile, status

# Absolute path to app/static
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".pdf"}

def get_static_dir(folder_name: str = "") -> str:
    """Returns absolute path to app/static/<folder_name> and ensures it exists."""
    target_dir = os.path.join(STATIC_DIR, folder_name) if folder_name else STATIC_DIR
    os.makedirs(target_dir, exist_ok=True)
    return target_dir

def save_upload_file(upload_file: UploadFile, folder_name: str) -> str:
    """
    Saves an uploaded file into app/static/<folder_name>/ and returns a relative web path.
    Example return value: '/static/media/3f82a1...png'
    """
    if not upload_file or not upload_file.filename:
        return None

    # Validate file extension
    ext = os.path.splitext(upload_file.filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )

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
    """
    Deletes a static file from disk given its relative web path, URL, or filename.
    """
    if not file_url_or_path:
        return False

    filename = os.path.basename(file_url_or_path.split("?")[0])

    if folder_name:
        target_path = os.path.join(STATIC_DIR, folder_name, filename)
    else:
        parts = file_url_or_path.replace("\\", "/").strip("/").split("/")
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
