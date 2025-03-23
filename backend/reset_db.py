import os
import shutil
from app import Base, engine, UPLOAD_FOLDER

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    print("Database schema reset successfully!")

def reset_upload_folder():
    if os.path.exists(UPLOAD_FOLDER):
        print(f"Removing upload folder: {UPLOAD_FOLDER}")
        shutil.rmtree(UPLOAD_FOLDER)
    
    print(f"Creating empty upload folder: {UPLOAD_FOLDER}")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    print("Upload folder reset successfully!")

if __name__ == "__main__":
    confirm = input("This will delete all data in the database and upload folder. Continue? (y/n): ")
    if confirm.lower() == 'y':
        reset_database()
        reset_upload_folder()
        print("Reset complete!")
    else:
        print("Operation cancelled.")
