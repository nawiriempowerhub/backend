from sqlalchemy import Column, Integer, String
from database import Base, engine, SessionLocal

# Dummy model
class TestUser(Base):
    __tablename__ = "test_users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

# Create the table
Base.metadata.create_all(bind=engine)

# Insert a test record
db = SessionLocal()
new_user = TestUser(name="Alice")
db.add(new_user)
db.commit()

# Query the table
users = db.query(TestUser).all()
print("Users in test_users table:", [user.name for user in users])

# Clean up session
db.close()
