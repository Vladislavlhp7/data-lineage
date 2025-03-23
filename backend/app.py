from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import os
import difflib
import requests
import chardet

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./files.db"
UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FileModel(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)

Base.metadata.create_all(bind=engine)

class ModifyFileRequest(BaseModel):
    new_content: str

def summarize_changes(changes):
    change_text = "\n".join(changes)
    # response = requests.post(
    #     "https://api.mistral.ai/summarize",
    #     json={"text": change_text},
    #     headers={"Authorization": "Bearer YOUR_API_KEY"}
    # )
    # summary = response.json()
    # return summary['summary']
    return "This is a dummy summary of the changes."

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    encoding = chardet.detect(content)['encoding']
    content_str = content.decode(encoding)
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content_str)
    db = SessionLocal()
    new_file = FileModel(filename=file.filename, content=content_str, version=1)
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    db.close()
    return JSONResponse(content={"message": "File uploaded successfully"}, status_code=200)

@app.delete("/delete/{file_id}")
async def delete_file(file_id: int):
    db = SessionLocal()
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if file is None:
        db.close()
        raise HTTPException(status_code=404, detail="File not found")
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(file)
    db.commit()
    db.close()
    return JSONResponse(content={"message": "File deleted successfully"}, status_code=200)

@app.post("/modify/{file_id}")
async def modify_file(file_id: int, request: ModifyFileRequest):
    db = SessionLocal()
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if file is None:
        db.close()
        raise HTTPException(status_code=404, detail="File not found")
    old_content = file.content
    file.content = request.new_content
    file.version += 1
    db.commit()
    db.refresh(file)
    db.close()
    changes = list(difflib.unified_diff(old_content.splitlines(), request.new_content.splitlines()))
    summary = summarize_changes(changes)
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "w") as f:
        f.write(request.new_content)
    return JSONResponse(content={"message": "File modified successfully", "summary": summary}, status_code=200)

@app.get("/files")
async def list_files():
    db = SessionLocal()
    files = db.query(FileModel).all()
    db.close()
    return [{"id": file.id, "filename": file.filename, "version": file.version} for file in files]

@app.get("/files/{file_id}")
async def get_file(file_id: int):
    db = SessionLocal()
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    db.close()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"id": file.id, "filename": file.filename, "content": file.content, "version": file.version}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
