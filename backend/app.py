from fastapi import FastAPI, UploadFile, File as FastAPIFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
import os
import difflib
import requests
import chardet
from datetime import datetime
import shutil
from typing import List, Optional

# Setup FastAPI app
app = FastAPI(title="Data Lineage API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = "sqlite:///./files.db"
UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class FileModel(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    latest_version = Column(Integer, nullable=False, default=1)
    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan")

class FileVersion(Base):
    __tablename__ = "file_versions"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    file = relationship("FileModel", back_populates="versions")
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    storage_path = Column(String, nullable=False)
    change_summary = Column(Text, nullable=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Pydantic schemas
class ModifyFileRequest(BaseModel):
    new_content: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions
def ensure_file_directory(filename):
    """Create directory for a file if it doesn't exist"""
    file_dir = os.path.join(UPLOAD_FOLDER, filename.replace('.', '_'))
    os.makedirs(file_dir, exist_ok=True)
    return file_dir

def get_version_path(file_dir, version_number):
    """Get the path for a specific version of a file"""
    return os.path.join(file_dir, f"v{version_number}.txt")

def save_file_content(file_dir, version_number, content, encoding='utf-8'):
    """Save file content to a specific version"""
    storage_path = get_version_path(file_dir, version_number)
    with open(storage_path, "w", encoding=encoding) as f:
        f.write(content)
    return storage_path

def delete_file_directory(file_dir):
    """Delete a file directory and all its versions"""
    if os.path.exists(file_dir):
        shutil.rmtree(file_dir)

def generate_diff(old_content, new_content):
    """Generate a unified diff between two content strings"""
    return list(difflib.unified_diff(old_content.splitlines(), new_content.splitlines()))

def summarize_changes(changes):
    """Summarize changes between two versions of a file"""
    change_text = "\n".join(changes)
    
    # Mistral API call commented out for now
    # response = requests.post(
    #     "https://api.mistral.ai/summarize",
    #     json={"text": change_text},
    #     headers={"Authorization": "Bearer YOUR_API_KEY"}
    # )
    # summary = response.json()
    # return summary['summary']
    
    return "This is a dummy summary of the changes."

# API Endpoints
@app.post("/upload")
async def upload_file(file: UploadFile = FastAPIFile(...), db: SessionLocal = Depends(get_db)):
    """Upload a new file or a new version of an existing file"""
    try:
        content = await file.read()
        encoding = chardet.detect(content)['encoding'] or 'utf-8'  # Provide a default encoding
        content_str = content.decode(encoding)
        
        # Create directory for this file
        file_dir = ensure_file_directory(file.filename)
        
        # Check if file with same name already exists
        existing_file = db.query(FileModel).filter(FileModel.filename == file.filename).first()
        
        if existing_file:
            # Create new version of existing file
            version_number = existing_file.latest_version + 1
            existing_file.latest_version = version_number
            
            # Save content to version-specific file
            storage_path = save_file_content(file_dir, version_number, content_str, encoding)
            
            # Create new version record
            new_version = FileVersion(
                file_id=existing_file.id,
                version_number=version_number,
                content=content_str,
                storage_path=storage_path,
                change_summary="File uploaded as new version"
            )
            db.add(new_version)
        else:
            # Create new file record
            new_file = FileModel(filename=file.filename, latest_version=1)
            db.add(new_file)
            db.flush()  # To get the new file ID
            
            # Save content to version-specific file
            storage_path = save_file_content(file_dir, 1, content_str, encoding)
            
            # Create initial version record
            new_version = FileVersion(
                file_id=new_file.id,
                version_number=1,
                content=content_str,
                storage_path=storage_path,
                change_summary="Initial file upload"
            )
            db.add(new_version)
        
        db.commit()
        return JSONResponse(content={"message": "File uploaded successfully"}, status_code=200)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.delete("/delete/{file_id}")
async def delete_file(file_id: int, db: SessionLocal = Depends(get_db)):
    """Delete a file and all its versions"""
    try:
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if file is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete file directory if it exists
        file_dir = ensure_file_directory(file.filename)
        delete_file_directory(file_dir)
        
        # Delete from database
        db.delete(file)
        db.commit()
        
        return JSONResponse(content={"message": "File deleted successfully"}, status_code=200)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

@app.post("/modify/{file_id}")
async def modify_file(file_id: int, request: ModifyFileRequest, db: SessionLocal = Depends(get_db)):
    """Modify an existing file, creating a new version"""
    try:
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if file is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the latest version
        latest_version = db.query(FileVersion).filter(
            FileVersion.file_id == file_id,
            FileVersion.version_number == file.latest_version
        ).first()
        
        if latest_version is None:
            raise HTTPException(status_code=404, detail="File version not found")
        
        old_content = latest_version.content
        new_version_number = file.latest_version + 1
        
        # Create directory for this file if it doesn't exist
        file_dir = ensure_file_directory(file.filename)
        
        # Store the new version with incremented version number
        storage_path = save_file_content(file_dir, new_version_number, request.new_content)
        
        # Generate summary of changes
        changes = generate_diff(old_content, request.new_content)
        summary = summarize_changes(changes)
        
        # Create new version record
        new_version = FileVersion(
            file_id=file.id,
            version_number=new_version_number,
            content=request.new_content,
            storage_path=storage_path,
            change_summary=summary
        )
        db.add(new_version)
        
        # Update file's latest version
        file.latest_version = new_version_number
        
        db.commit()
        
        return JSONResponse(
            content={
                "message": "File modified successfully", 
                "summary": summary, 
                "version": new_version_number
            }, 
            status_code=200
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error modifying file: {str(e)}")

@app.get("/files")
async def list_files(db: SessionLocal = Depends(get_db)):
    """List all files"""
    files = db.query(FileModel).all()
    result = []
    
    for file in files:
        latest_version = db.query(FileVersion).filter(
            FileVersion.file_id == file.id,
            FileVersion.version_number == file.latest_version
        ).first()
        
        if latest_version:
            result.append({
                "id": file.id,
                "filename": file.filename,
                "version": file.latest_version,
                "created_at": latest_version.created_at.isoformat() if latest_version.created_at else None
            })
    
    return result

@app.get("/files/{file_id}")
async def get_file(file_id: int, db: SessionLocal = Depends(get_db)):
    """Get a specific file by ID"""
    try:
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if file is None:
            raise HTTPException(status_code=404, detail=f"File with id {file_id} not found")
        
        # Get the latest version by default
        latest_version = db.query(FileVersion).filter(
            FileVersion.file_id == file_id,
            FileVersion.version_number == file.latest_version
        ).first()
        
        if latest_version is None:
            raise HTTPException(status_code=404, detail="File version not found")
        
        return {
            "id": file.id,
            "filename": file.filename,
            "content": latest_version.content,
            "version": file.latest_version,
            "created_at": latest_version.created_at.isoformat() if latest_version.created_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

@app.get("/files/{file_id}/versions")
async def get_file_versions(file_id: int, db: SessionLocal = Depends(get_db)):
    """Get all versions of a specific file"""
    try:
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if file is None:
            raise HTTPException(status_code=404, detail=f"File with id {file_id} not found")
        
        versions = db.query(FileVersion).filter(
            FileVersion.file_id == file_id
        ).order_by(FileVersion.version_number.desc()).all()
        
        return [
            {
                "version": v.version_number,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "summary": v.change_summary
            } for v in versions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file versions: {str(e)}")

@app.get("/files/{file_id}/version/{version_number}")
async def get_file_version(file_id: int, version_number: int, db: SessionLocal = Depends(get_db)):
    """Get a specific version of a file"""
    try:
        file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if file is None:
            raise HTTPException(status_code=404, detail=f"File with id {file_id} not found")
        
        version = db.query(FileVersion).filter(
            FileVersion.file_id == file_id,
            FileVersion.version_number == version_number
        ).first()
        
        if version is None:
            raise HTTPException(status_code=404, detail=f"Version {version_number} not found")
        
        return {
            "id": file.id,
            "filename": file.filename,
            "content": version.content,
            "version": version.version_number,
            "created_at": version.created_at.isoformat() if version.created_at else None,
            "summary": version.change_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file version: {str(e)}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
