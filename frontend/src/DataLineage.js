import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';
import './DataLineage.css';

function DataLineage() {
    const { id } = useParams();
    const [file, setFile] = useState(null);
    const [fileContent, setFileContent] = useState('');
    const [summary, setSummary] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [versions, setVersions] = useState([]);

    useEffect(() => {
        fetchFile();
    }, [id]);

    const fetchFile = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`http://localhost:8000/files/${id}`);
            setFile(response.data);
            setFileContent(response.data.content);
            
            // For demo purposes, create mock version history
            const mockVersions = [];
            for (let i = 1; i <= response.data.version; i++) {
                mockVersions.push({
                    version: i,
                    date: new Date(Date.now() - (response.data.version - i) * 86400000).toLocaleDateString(),
                    summary: i === response.data.version ? "Current version" : `Version ${i} changes`
                });
            }
            setVersions(mockVersions);
        } catch (error) {
            console.error("Error fetching file:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleFileSave = async () => {
        setSaving(true);
        try {
            const response = await axios.post(`http://localhost:8000/modify/${id}`, { new_content: fileContent });
            setSummary(response.data.summary);
            fetchFile();
        } catch (error) {
            console.error("Error saving file:", error);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="loading">
                <i className="fas fa-spinner fa-spin"></i> Loading file...
            </div>
        );
    }

    return (
        <div className="lineage-container">
            <div className="back-link">
                <Link to="/">
                    <i className="fas fa-arrow-left"></i> Back to Files
                </Link>
            </div>
            
            {file && (
                <>
                    <div className="file-header">
                        <h1>{file.filename}</h1>
                        <span className="version-badge">Version {file.version}</span>
                    </div>
                    
                    <div className="lineage-graph">
                        {versions.map((ver, index) => (
                            <React.Fragment key={ver.version}>
                                <div className={`version-node ${ver.version === file.version ? 'current' : ''}`}>
                                    <div className="version-circle">{ver.version}</div>
                                    <div className="version-details">
                                        <span className="version-date">{ver.date}</span>
                                        <span className="version-summary">{ver.summary}</span>
                                    </div>
                                </div>
                                {index < versions.length - 1 && (
                                    <div className="version-connector"></div>
                                )}
                            </React.Fragment>
                        ))}
                    </div>
                    
                    <div className="file-editor-panel">
                        <h2>Edit File Content</h2>
                        <textarea 
                            value={fileContent} 
                            onChange={(e) => setFileContent(e.target.value)} 
                            placeholder="Enter file content here..."
                        />
                        <button 
                            className="save-button" 
                            onClick={handleFileSave} 
                            disabled={saving}
                        >
                            {saving ? (
                                <>
                                    <i className="fas fa-spinner fa-spin"></i> Saving...
                                </>
                            ) : (
                                <>
                                    <i className="fas fa-save"></i> Save Changes
                                </>
                            )}
                        </button>
                    </div>
                    
                    {summary && (
                        <div className="summary-panel">
                            <h2>Change Summary</h2>
                            <div className="summary-content">
                                <i className="fas fa-info-circle"></i>
                                <p>{summary}</p>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

export default DataLineage;
