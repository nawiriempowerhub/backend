from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, services
from app.dependencies import get_db, get_current_active_user
from app.utils.email import send_notification

router = APIRouter(
    prefix="/volunteers",
    tags=["Volunteer Applications"],
)

@router.post("", response_model=schemas.Volunteer, status_code=status.HTTP_201_CREATED)
async def submit_volunteer_application(volunteer: schemas.VolunteerCreate, db: Session = Depends(get_db)):
    """
    Submit a volunteer application form. Saves to DB and sends email notification.
    """
    try:
        # Save to DB
        saved = services.crud_service.create_item(
            db=db, model=models.Volunteer, item=volunteer
        )

        # Send email
        body = f"""
        New Volunteer Application
        Name: {volunteer.name}
        Email: {volunteer.email}
        Phone: {volunteer.phone or 'Not provided'}
        Motivation: {volunteer.motivation or 'Not provided'}
        Submitted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        await send_notification(
            subject="New Volunteer Application",
            body=body
        )

        return saved
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")

@router.get("", response_model=List[schemas.Volunteer])
def view_all_volunteer_applications(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    """
    View all volunteer applications. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view applications")
    applications = services.crud_service.get_items(db, model=models.Volunteer, skip=skip, limit=limit)
    return applications

@router.put("/{application_id}", response_model=schemas.Volunteer)
def update_volunteer_application_status(
    application_id: int,
    status_update: schemas.VolunteerStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update the status of a volunteer application (e.g., Pending, Approved, Rejected).
    Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update applications")

    db_application = services.crud_service.get_item(db, model=models.Volunteer, item_id=application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")

    db_application.status = status_update.status
    db.commit()
    db.refresh(db_application)
    return db_application

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_volunteer_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete or archive a volunteer application. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete applications")

    db_application = services.crud_service.delete_item(db, model=models.Volunteer, item_id=application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
        
    return