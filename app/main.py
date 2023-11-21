from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import SessionLocal, engine
import boto3
import os
import datetime

models.Base.metadata.create_all(bind=engine)


session = boto3.Session()

s3 = session.client('s3')

bucket_name = "pedropmc-bucket"

instance_id = os.getenv("INSTANCE")

key = f"logs/log_{instance_id}.txt"

app = FastAPI()

# Upload the modified file back to S3
s3.upload_file("start.txt", bucket_name, key)

def log(string):
    ct = datetime.datetime.now()
    string += f" {ct}\n"
    # Download the file from S3 to a local temp file
    local_temp_file = 'temp_file.txt'  # Replace with your local path
    s3.download_file(bucket_name, key, local_temp_file)
    # Append the string to the local file
    with open(local_temp_file, 'a') as f:
        f.write(string)
    # Upload the modified file back to S3
    s3.upload_file(local_temp_file, bucket_name, key)
    



# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/quotes/", response_model=schemas.Member)
def create_member(member: schemas.MemberCreate, db: Session = Depends(get_db)):
    return crud.create_member(db=db, member=member)

@app.get("/")
def hello_world():
    log("Hello World")
    return "Hello World"

@app.get("/quotes/", response_model=list[schemas.Member])
def read_members(db: Session = Depends(get_db)):
    members = crud.get_members(db)
    return members

@app.get("/quotes/{member_id}", response_model=schemas.Member)
def read_member(member_id: int, db: Session = Depends(get_db)):
    db_member = crud.get_member(db, member_id=member_id)
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return db_member

@app.put("/quotes/{member_id}", response_model=schemas.Member)
def update_member(member_id: int, member: schemas.MemberUpdate, db: Session = Depends(get_db)):
    db_member = crud.get_member(db, member_id=member_id)
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return crud.update_member(db=db, member=member, member_id=member_id)

@app.delete("/quotes/{member_id}", response_model=schemas.DeletedResponse)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_member(db=db, member_id=member_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Member deleted successfully", "deleted_member_id": member_id}
