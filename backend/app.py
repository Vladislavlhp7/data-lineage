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
import io
import random
import docx  # Import for DOCX support
from dotenv import load_dotenv  # Add this import

# Add these imports for transaction simulation
import uuid
import time
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

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
    # Simple summary without using Mistral API
    if not changes:
        return "No changes detected."
    
    # Generate a simple summary based on the number and type of changes
    additions = sum(1 for line in changes if line.startswith('+'))
    deletions = sum(1 for line in changes if line.startswith('-'))
    
    if additions == 0 and deletions == 0:
        return "File was modified but no text content changed."
    
    summary_parts = []
    if additions > 0:
        summary_parts.append(f"Added {additions} line{'s' if additions != 1 else ''}")
    if deletions > 0:
        summary_parts.append(f"Removed {deletions} line{'s' if deletions != 1 else ''}")
    
    summary = " and ".join(summary_parts)
    if len(changes) > 10:
        summary += ". Substantial changes were made to the file."
    
    return summary

def extract_file_content(file_content, filename, encoding='utf-8'):
    """Extract text content from files of different formats"""
    # Check file extension
    _, file_extension = os.path.splitext(filename.lower())
    
    if file_extension == '.docx':
        # Process DOCX file
        try:
            doc = docx.Document(io.BytesIO(file_content))
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing DOCX file: {str(e)}")
    else:
        # Process as text file with encoding detection
        try:
            detected_encoding = chardet.detect(file_content)['encoding'] or encoding
            return file_content.decode(detected_encoding)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error decoding text file: {str(e)}")

# API Endpoints
@app.post("/upload")
async def upload_file(file: UploadFile = FastAPIFile(...), db: SessionLocal = Depends(get_db)):
    """Upload a new file or a new version of an existing file"""
    try:
        content = await file.read()
        
        # Extract content based on file type
        content_str = extract_file_content(content, file.filename)
        
        # Create directory for this file
        file_dir = ensure_file_directory(file.filename)
        
        # Check if file with same name already exists
        existing_file = db.query(FileModel).filter(FileModel.filename == file.filename).first()
        
        if (existing_file):
            # Create new version of existing file
            version_number = existing_file.latest_version + 1
            existing_file.latest_version = version_number
            
            # Save content to version-specific file
            storage_path = save_file_content(file_dir, version_number, content_str)
            
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
            storage_path = save_file_content(file_dir, 1, content_str)
            
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
        
        if (latest_version):
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
        
        # Change the ordering to ascending (oldest to newest)
        versions = db.query(FileVersion).filter(
            FileVersion.file_id == file_id
        ).order_by(FileVersion.version_number.asc()).all()  # Changed from desc() to asc()
        
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

# Add Transaction Models
class TransactionStep(BaseModel):
    id: str
    name: str
    department: str
    description: str
    
class TransactionTransformation(BaseModel):
    field: str
    action: str
    description: str
    
class TransactionSimulationResponse(BaseModel):
    step_id: str
    step_name: str
    step_index: int
    department: str
    description: str
    current_data: Dict[str, Any]
    transformations: List[TransactionTransformation]
    progress: float
    is_complete: bool
    next_step: Optional[str] = None

@app.get("/transaction/init")
async def init_transaction():
    """Initialize a new transaction with random data"""
    transaction_id = f"T-{uuid.uuid4().hex[:8].upper()}"
    
    # Create sample initial transaction data
    transaction = {
        "tradeId": transaction_id,
        "clientId": f"C-{100000 + int(random.random() * 900000)}",
        "securityId": f"US-{10000 + int(random.random() * 90000)}",
        "quantity": int(1000 + random.random() * 9000),
        "price": round(50 + random.random() * 950, 2),
        "tradeDate": (datetime.now()).strftime("%Y-%m-%d"),
        "trader": "John Smith"
    }
    
    # Store in memory (would be in database in production)
    # In a real app, you'd store this in Redis or a database
    active_transactions[transaction_id] = {
        "data": transaction,
        "current_step": 0,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "transaction_id": transaction_id,
        "initial_data": transaction,
        "step": 0,
        "total_steps": len(transaction_data["steps"])
    }

@app.get("/transaction/{transaction_id}/process")
async def process_transaction_step(transaction_id: str, step_index: int = None):
    """Process a transaction step"""
    # Check if transaction exists
    if transaction_id not in active_transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    transaction = active_transactions[transaction_id]
    
    # If step_index is provided, validate it
    if step_index is not None:
        if step_index < 0 or step_index >= len(transaction_data["steps"]):
            raise HTTPException(status_code=400, detail="Invalid step index")
        # Update the current step if valid
        transaction["current_step"] = step_index
    else:
        # Use the current step
        step_index = transaction["current_step"]
    
    # Check if we've reached the end
    if step_index >= len(transaction_data["steps"]):
        return {
            "is_complete": True,
            "message": "Transaction processing complete"
        }
    
    # Get the current step
    current_step = transaction_data["steps"][step_index]
    
    # Apply transformations for this step
    apply_transformations(transaction, step_index)
    
    # Get transformation definitions for this step
    transformations = []
    if step_index > 0:  # No transformations for the first step
        transformations = transaction_data["transformations"].get(current_step["id"], [])
    
    # Create the response
    response = {
        "step_id": current_step["id"],
        "step_name": current_step["name"],
        "step_index": step_index,
        "department": current_step["department"],
        "description": current_step["description"],
        "current_data": transaction["data"],
        "transformations": transformations,
        "progress": (step_index + 1) / len(transaction_data["steps"]) * 100,
        "is_complete": step_index == len(transaction_data["steps"]) - 1
    }
    
    # If there's a next step, include it
    if step_index < len(transaction_data["steps"]) - 1:
        response["next_step"] = transaction_data["steps"][step_index + 1]["id"]
        
    # If not the last step, increment the current step
    if step_index < len(transaction_data["steps"]) - 1:
        transaction["current_step"] = step_index + 1
    
    return response

@app.get("/transaction/{transaction_id}/reset")
async def reset_transaction(transaction_id: str):
    """Reset a transaction to the initial state"""
    # Check if transaction exists
    if transaction_id not in active_transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get the basic transaction info and reset to step 0
    transaction = active_transactions[transaction_id]
    
    # Reset to initial step
    transaction["current_step"] = 0
    
    # Reset the data to initial values
    transaction["data"] = {
        "tradeId": transaction["data"]["tradeId"],
        "clientId": transaction["data"]["clientId"],
        "securityId": transaction["data"]["securityId"],
        "quantity": transaction["data"]["quantity"],
        "price": transaction["data"]["price"],
        "tradeDate": transaction["data"]["tradeDate"],
        "trader": transaction["data"]["trader"]
    }
    
    return {
        "message": "Transaction reset successfully",
        "transaction_id": transaction_id,
        "current_step": 0,
        "data": transaction["data"]
    }

# In-memory storage for active transactions (would use DB in production)
active_transactions = {}

def apply_transformations(transaction, step_index):
    """Apply transformations for the given step to the transaction data"""
    if step_index == 0:  # No transformations for the first step
        return
        
    current_step = transaction_data["steps"][step_index]
    step_id = current_step["id"]
    transformations = transaction_data["transformations"].get(step_id, [])
    
    for transform in transformations:
        field = transform["field"]
        action = transform["action"]
        
        if action == "added":
            # Add new fields based on field name
            if field == "validationStatus":
                transaction["data"][field] = "VALID"
            elif field == "validationTimestamp":
                transaction["data"][field] = datetime.now().isoformat()
            elif field == "securityName":
                transaction["data"][field] = "Sample Corp Common Stock"
            elif field == "marketValue":
                price = transaction["data"]["price"]
                quantity = transaction["data"]["quantity"]
                transaction["data"][field] = round(price * quantity, 2)
            elif field == "currency":
                transaction["data"][field] = "USD"
            elif field == "exchangeRate":
                transaction["data"][field] = 1.0
            elif field == "settlementDate":
                trade_date = datetime.strptime(transaction["data"]["tradeDate"], "%Y-%m-%d")
                settlement_date = trade_date + timedelta(days=2)  # T+2 settlement
                transaction["data"][field] = settlement_date.strftime("%Y-%m-%d")
            elif field == "varValue":
                market_value = transaction["data"].get("marketValue", 0)
                transaction["data"][field] = round(market_value * 0.05, 2)
            elif field == "deltaValue":
                transaction["data"][field] = 0.65
            elif field == "gammaValue":
                transaction["data"][field] = 0.12
            elif field == "settlementCurrency":
                transaction["data"][field] = "USD"
            elif field == "settlementInstructions":
                transaction["data"][field] = "SWIFT: BKCHGB2L"
            elif field == "accountDetails":
                transaction["data"][field] = f"ACCT: {74000000 + int(random.random() * 999999)}"
            elif field == "securityType":
                transaction["data"][field] = "STOCK"
            elif field == "tradingDesk":
                transaction["data"][field] = "EQUITY-TRADING-1"
            elif field == "reportingStatus":
                transaction["data"][field] = "REPORTED"
            elif field == "reportedTimestamp":
                transaction["data"][field] = datetime.now().isoformat()
            elif field == "regulatoryId":
                transaction["data"][field] = f"REG-{10000 + int(random.random() * 90000)}"
        elif action == "renamed":
            # Handle renamed fields
            if field == "valueCurrency" and "currency" in transaction["data"]:
                transaction["data"][field] = transaction["data"]["currency"]
                del transaction["data"]["currency"]

# Load transaction data from JSON file
TRANSACTION_FILE = os.path.join(os.path.dirname(__file__), "transactions.json")

def load_transaction_data():
    try:
        with open(TRANSACTION_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Transaction file not found: {TRANSACTION_FILE}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in transaction file: {e}")

transaction_data = load_transaction_data()

# API Endpoints
@app.get("/transaction/steps")
async def get_transaction_steps():
    """Get all steps in the transaction process"""
    return transaction_data["steps"]

@app.get("/transaction/init")
async def init_transaction():
    """Initialize a new transaction with random data"""
    transaction_id = f"T-{uuid.uuid4().hex[:8].upper()}"
    
    # Create sample initial transaction data
    transaction = {
        "tradeId": transaction_id,
        "clientId": f"C-{100000 + int(random.random() * 900000)}",
        "securityId": f"US-{10000 + int(random.random() * 90000)}",
        "quantity": int(1000 + random.random() * 9000),
        "price": round(50 + random.random() * 950, 2),
        "tradeDate": (datetime.now()).strftime("%Y-%m-%d"),
        "trader": "John Smith"
    }
    
    # Store in memory (would be in database in production)
    active_transactions[transaction_id] = {
        "data": transaction,
        "current_step": 0,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "transaction_id": transaction_id,
        "initial_data": transaction,
        "step": 0,
        "total_steps": len(transaction_data["steps"])  # Use transaction_data["steps"]
    }

@app.get("/transaction/{transaction_id}/process")
async def process_transaction_step(transaction_id: str, step_index: int = None):
    """Process a transaction step"""
    # Check if transaction exists
    if transaction_id not in active_transactions:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    transaction = active_transactions[transaction_id]
    
    # If step_index is provided, validate it
    if step_index is not None:
        if step_index < 0 or step_index >= len(transaction_data["steps"]):  # Use transaction_data["steps"]
            raise HTTPException(status_code=400, detail="Invalid step index")
    else:
        step_index = transaction["current_step"]
    
    # Check if we've reached the end
    if step_index >= len(transaction_data["steps"]):  # Use transaction_data["steps"]
        raise HTTPException(status_code=400, detail="Transaction already completed")
    
    # Get the current step
    current_step = transaction_data["steps"][step_index]  # Use transaction_data["steps"]
    
    # Apply transformations for this step
    transformations = transaction_data["transformations"].get(current_step["id"], [])
    for transform in transformations:
        field = transform["field"]
        action = transform["action"]
        
        if action == "added":
            transaction["data"][field] = f"Sample value for {field}"
        elif action == "renamed":
            old_field = field.replace("value", "currency")  # Example renaming logic
            transaction["data"][field] = transaction["data"].pop(old_field, None)
    
    # Create the response
    response = {
        "step_id": current_step["id"],
        "step_name": current_step["name"],
        "step_index": step_index,
        "department": current_step["department"],
        "description": current_step["description"],
        "current_data": transaction["data"],
        "transformations": transformations,
        "progress": (step_index + 1) / len(transaction_data["steps"]) * 100,  # Use transaction_data["steps"]
        "is_complete": step_index == len(transaction_data["steps"]) - 1  # Use transaction_data["steps"]
    }
    
    # If not the last step, increment the current step
    if step_index < len(transaction_data["steps"]) - 1:  # Use transaction_data["steps"]
        transaction["current_step"] += 1
    
    return response

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
