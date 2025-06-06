from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, services
from app.dependencies import get_db, get_current_active_user

router = APIRouter(
    prefix="/api/blog",
    tags=["Blogs / News"],
)

@router.get("", response_model=List[schemas.Blog])
def read_all_blogs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all blog posts. This is a public endpoint.
    """
    blogs = services.crud_service.get_items(db, model=models.BlogPost, skip=skip, limit=limit)
    return blogs

@router.get("/{blog_id}", response_model=schemas.Blog)
def read_blog_by_id(blog_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific blog post by its ID. This is a public endpoint.
    """
    db_blog = services.crud_service.get_item(db, model=models.BlogPost, item_id=blog_id)
    if db_blog is None:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return db_blog

@router.post("", response_model=schemas.Blog, status_code=status.HTTP_201_CREATED)
def create_new_blog_post(
    blog: schemas.BlogCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new blog post. Requires admin privileges.
    The author_id is automatically assigned to the current authenticated user.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create blog posts")
    
    # Manually create the blog post to assign the author_id
    db_blog = models.BlogPost(**blog.dict(), author_id=current_user.id)
    db.add(db_blog)
    db.commit()
    db.refresh(db_blog)
    return db_blog

@router.put("/{blog_id}", response_model=schemas.Blog)
def update_blog_post(
    blog_id: int,
    blog_update: schemas.BlogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update an existing blog post. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update blog posts")

    db_blog = services.crud_service.get_item(db, model=models.BlogPost, item_id=blog_id)
    if not db_blog:
        raise HTTPException(status_code=404, detail="Blog post not found")

    update_data = blog_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_blog, key, value)
    
    db.commit()
    db.refresh(db_blog)
    return db_blog

@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_post(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a blog post. Requires admin privileges.
    """
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete blog posts")
    
    db_blog = services.crud_service.delete_item(db, model=models.BlogPost, item_id=blog_id)
    if not db_blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    return