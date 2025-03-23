import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import './Home.css';

function Home() {
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);

    useEffect(() => {
        fetchFiles();
    }, []);

    const fetchFiles = async () => {
        setLoading(true);
        try {
            const response = await axios.get('http://localhost:8000/files');
            setFiles(response.data);
        } catch (error) {
            console.error("Error fetching files:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        
        setUploading(true);
        setUploadProgress(0);
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            // Simple logging to debug the request
            console.log('Uploading file:', file.name);
            
            const response = await axios.post('http://localhost:8000/upload', formData, {
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    setUploadProgress(percentCompleted);
                    console.log(`Upload progress: ${percentCompleted}%`);
                }
            });
            
            console.log('Upload response:', response);
            
            // Simulate completion for small files
            if (uploadProgress < 100) {
                setUploadProgress(100);
                await new Promise(resolve => setTimeout(resolve, 500));
            }
            
            fetchFiles();
        } catch (error) {
            console.error("Error uploading file:", error);
            alert(`Upload failed: ${error.response?.data?.detail || error.message}`);
        } finally {
            setUploading(false);
        }
    };

    const handleFileDelete = async (fileId, event) => {
        event.preventDefault();
        event.stopPropagation();
        
        if (window.confirm("Are you sure you want to delete this file?")) {
            try {
                await axios.delete(`http://localhost:8000/delete/${fileId}`);
                fetchFiles();
            } catch (error) {
                console.error("Error deleting file:", error);
            }
        }
    };

    const handleFileSelect = async (fileId) => {
        try {
            // Fetch the file content before navigating
            await axios.get(`http://localhost:8000/files/${fileId}`);
        } catch (error) {
            console.error(`Error pre-fetching file ${fileId}:`, error);
        }
    };

    // Group files by unique filename (keeping only the latest version)
    const uniqueFiles = files.reduce((acc, file) => {
        if (!acc[file.filename] || acc[file.filename].version < file.version) {
            acc[file.filename] = file;
        }
        return acc;
    }, {});

    const uniqueFileList = Object.values(uniqueFiles);

    return (
        <div className="home-container">
            <h1>File Repository</h1>
            <div className="upload-section">
                <label className="file-upload-btn">
                    <i className="fas fa-cloud-upload-alt"></i> Upload New File
                    <input type="file" onChange={handleFileUpload} disabled={uploading} />
                </label>
            </div>
            
            {uploading && (
                <div className="upload-progress-container">
                    <div className="upload-progress-bar" style={{ width: `${uploadProgress}%` }}></div>
                    <div className="upload-progress-text">{uploadProgress}% Uploaded</div>
                </div>
            )}
            
            {loading ? (
                <div className="loading">
                    <i className="fas fa-spinner fa-spin"></i> Loading files...
                </div>
            ) : (
                <>
                    <h2 className="section-title">Your Files</h2>
                    <div className="files-grid">
                        {uniqueFileList.length === 0 ? (
                            <div className="no-files">
                                <i className="fas fa-folder-open"></i>
                                <p>No files found. Upload your first file!</p>
                            </div>
                        ) : (
                            uniqueFileList.map(file => (
                                <Link 
                                    to={`/file/${file.id}`} 
                                    key={file.id} 
                                    className="file-card"
                                    onClick={() => handleFileSelect(file.id)}
                                >
                                    <div className="file-icon">
                                        <i className="fas fa-file-alt"></i>
                                    </div>
                                    <div className="file-info">
                                        <h3 className="file-name">{file.filename}</h3>
                                        <span className="file-version">Version {file.version}</span>
                                    </div>
                                    <button className="delete-btn" onClick={(e) => handleFileDelete(file.id, e)}>
                                        <i className="fas fa-trash"></i>
                                    </button>
                                </Link>
                            ))
                        )}
                    </div>
                </>
            )}
        </div>
    );
}

export default Home;
