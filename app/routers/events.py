from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, services
from app.dependencies import get_db, get_current_active_user
from app.utils.email import send_notification

router = APIRouter(
    prefix="/api/events",
    tags=["Events"],
)

@router.get("", response_model=List[schemas.Event])
def get_all_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all events. Public endpoint.
    """
    events = services.crud_service.get_items(db, model=models.Event, skip=skip, limit=limit)
    return events

@router.post("", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
def create_new_event(
    event: schemas.EventCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new event. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create events")
    return services.crud_service.create_item(db=db, model=models.Event, item=event)

@router.put("/{event_id}", response_model=schemas.Event)
def update_event(
    event_id: int,
    event_update: schemas.EventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update an existing event. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update events")

    db_event = services.crud_service.get_item(db, model=models.Event, item_id=event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = event_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete an event. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete events")
    
    db_event = services.crud_service.delete_item(db, model=models.Event, item_id=event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return

@router.post("/register", response_model=schemas.EventRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_for_event(
    registration: schemas.EventRegistrationCreate,
    db: Session = Depends(get_db)
):
    """
    Public route: Register for an event (no authentication required).
    Sends email notification upon successful registration.
    """
    # Check if event exists
    event = db.query(models.Event).filter(models.Event.id == registration.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Save registration to DB
    new_registration = models.EventRegistration(
        name=registration.name,
        email=registration.email,
        event_id=registration.event_id
    )
    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)

    # Send email notification
    try:
        body = f"""
        New Event Registration
        Name: {registration.name}
        Email: {registration.email}
        Event: {event.title}
        Registered at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        await send_notification(
            subject="New Event Registration",
            body=body
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}") from e

    return new_registration

@router.get("/{event_id}", response_model=schemas.Event)
def get_event_by_id(event_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single event by its ID. Public endpoint.
    """
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
