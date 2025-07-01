from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, services
from app.dependencies import get_db, get_current_active_user
from app.utils.email import send_notification

router = APIRouter(
    prefix="/contact",
    tags=["Contact Us"],
)

@router.post("", response_model=schemas.ContactSubmission, status_code=status.HTTP_201_CREATED)
async def submit_contact_form(contact: schemas.ContactSubmissionCreate, db: Session = Depends(get_db)):
    try:
        saved_contact = services.crud_service.create_item(
            db=db,
            model=models.ContactSubmission,
            item=contact
        )

        body = f"""
        New Contact Form Submission

        Name: {contact.name}
        Email: {contact.email}
        Message: {contact.message}
        Submitted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        try:
            await send_notification(subject="New Contact Form Submission", body=body)
        except Exception as email_error:
            print(f"[Email Error] {email_error}")

        return saved_contact

    except Exception as e:
        print(f"[API Error] {e}")
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")

@router.get("", response_model=List[schemas.ContactSubmission])
def view_contact_submissions(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    """
    View all contact form submissions. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view submissions")
    submissions = services.crud_service.get_items(db, model=models.ContactSubmission, skip=skip, limit=limit)
    return submissions

@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete or archive a contact submission. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete submissions")

    db_submission = services.crud_service.delete_item(db, model=models.ContactSubmission, item_id=submission_id)
    if not db_submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return