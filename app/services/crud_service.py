from sqlalchemy.orm import Session
from app import models

def get_item(db: Session, model, item_id: int):
    return db.query(model).filter(model.id == item_id).first()

def get_items(db: Session, model, skip: int = 0, limit: int = 100):
    return db.query(model).offset(skip).limit(limit).all()

def create_item(db: Session, model, item):
    db_item = model(**item)
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
