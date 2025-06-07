from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from app import models
from typing import Any, Dict, Union

def get_item(db: Session, model, item_id: int):
    return db.query(model).filter(model.id == item_id).first()

def get_items(db: Session, model, skip: int = 0, limit: int = 100):
    return db.query(model).offset(skip).limit(limit).all()

def create_item(db: Session, model: type[Any], item: Union[BaseModel, Dict[str, Any]]):
    """
    Creates a new item in the database based on the provided SQLAlchemy model
    and a Pydantic model or dictionary of item data. Handles Pydantic HttpUrl
    conversion and tags.
    """

    # Normalize item to dict whether it's a Pydantic model or already a dict
    if hasattr(item, "dict"):
        item_data = item.dict()
    elif isinstance(item, dict):
        item_data = item
    else:
        raise TypeError("Expected a Pydantic model or dictionary")

    # Process item to convert Pydantic types (like HttpUrl) to DB-compatible types
    processed_item = {}
    for key, value in item_data.items():
        if isinstance(value, HttpUrl):
            processed_item[key] = str(value)  # Convert HttpUrl to string
        elif key == 'tags' and isinstance(value, list):
            # Convert list of tags to comma-separated string if DB expects TEXT
            processed_item[key] = ",".join(value)
        else:
            processed_item[key] = value

    db_item = model(**processed_item)

    # Add, commit, and refresh the item in the database session
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item

def delete_item(db: Session, model, item_id: int):
    db_item = db.query(model).filter(model.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item

def update_item(db: Session, model, item_id: int, update_data: dict):
    db_item = db.query(model).filter(model.id == item_id).first()
    if not db_item:
        return None

    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item
