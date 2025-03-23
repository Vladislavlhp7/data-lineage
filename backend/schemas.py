from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ModifyFileRequest(BaseModel):
    new_content: str

class FileVersion(BaseModel):
    version: int
    created_at: Optional[datetime] = None
    summary: Optional[str] = None
    
    class Config:
        orm_mode = True

class File(BaseModel):
    id: int
    filename: str
    version: int
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class FileContent(File):
    content: str
