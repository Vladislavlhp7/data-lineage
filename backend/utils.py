import os
import shutil
import difflib
import io
import docx

def ensure_file_directory(filename, upload_folder):
    """Create directory for a file if it doesn't exist"""
    file_dir = os.path.join(upload_folder, filename.replace('.', '_'))
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

def extract_docx_text(docx_bytes):
    """Extract text from a DOCX file"""
    try:
        doc = docx.Document(io.BytesIO(docx_bytes))
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        raise Exception(f"Error processing DOCX: {str(e)}")

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
