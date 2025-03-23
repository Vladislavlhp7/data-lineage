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
    const [error, setError] = useState(null);
    const [saving, setSaving] = useState(false);
    const [versions, setVersions] = useState([]);
    const [editMode, setEditMode] = useState(false);
    const [selectedVersion, setSelectedVersion] = useState(null);
    const [selectedContent, setSelectedContent] = useState('');

    useEffect(() => {
        fetchFile();
    }, [id]);

    const fetchFile = async () => {
        setLoading(true);
        setError(null);
        try {
            console.log(`Fetching file with id: ${id}`);
            const response = await axios.get(`http://localhost:8000/files/${id}`);
            console.log('File data received:', response.data);
            
            setFile(response.data);
            setFileContent(response.data.content);
            
            // Fetch all versions of this file
            const versionsResponse = await axios.get(`http://localhost:8000/files/${id}/versions`);
            console.log('Versions received:', versionsResponse.data);
            
            if (versionsResponse.data && versionsResponse.data.length > 0) {
                // Create version history from actual data and sort chronologically (v1→v2)
                const versionHistory = versionsResponse.data
                    .sort((a, b) => a.version - b.version) // Sort by version number in ascending order
                    .map(v => ({
                        version: v.version,
                        date: new Date(v.created_at).toLocaleDateString(),
                        summary: v.summary || `Version ${v.version}`,
                    }));
                
                setVersions(versionHistory);
                setSelectedVersion(response.data.version);
                setSelectedContent(response.data.content);
            }
        } catch (error) {
            console.error("Error fetching file:", error);
            setError('Failed to load file. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    const handleVersionSelect = async (version) => {
        try {
            // Fetch the content for the selected version
            const response = await axios.get(`http://localhost:8000/files/${id}/version/${version}`);
            setSelectedVersion(version);
            setSelectedContent(response.data.content);
            setEditMode(false); // Exit edit mode when switching versions
        } catch (error) {
            console.error(`Error fetching version ${version}:`, error);
        }
    };

    const handleFileSave = async () => {
        setSaving(true);
        try {
            const response = await axios.post(`http://localhost:8000/modify/${id}`, { new_content: fileContent });
            setSummary(response.data.summary);
            setEditMode(false);
            fetchFile();
        } catch (error) {
            console.error("Error saving file:", error);
        } finally {
            setSaving(false);
        }
    };

    const handleEditLatestVersion = () => {
        // Only allow editing the latest version
        if (selectedVersion === file.version) {
            setEditMode(true);
            setFileContent(selectedContent);
        }
    };

    if (loading) {
        return (
            <div className="loading">
                <i className="fas fa-spinner fa-spin"></i> Loading file...
            </div>
        );
    }

    if (error) {
        return (
            <div className="error-container">
                <div className="back-link">
                    <Link to="/">
                        <i className="fas fa-arrow-left"></i> Back to Files
                    </Link>
                </div>
                <div className="error-message">
                    <i className="fas fa-exclamation-circle"></i>
                    <p>{error}</p>
                </div>
                <button className="retry-button" onClick={fetchFile}>
                    <i className="fas fa-redo"></i> Retry
                </button>
            </div>
        );
    }

    if (!file) {
        return (
            <div className="error-container">
                <div className="back-link">
                    <Link to="/">
                        <i className="fas fa-arrow-left"></i> Back to Files
                    </Link>
                </div>
                <div className="error-message">
                    <i className="fas fa-exclamation-circle"></i>
                    <p>File not found or could not be loaded.</p>
                </div>
                <button className="retry-button" onClick={fetchFile}>
                    <i className="fas fa-redo"></i> Retry
                </button>
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
                    
                    <h2 className="lineage-title">File History</h2>
                    
                    <div className="graph-container">
                        <div className="lineage-graph-horizontal">
                            {versions.map((ver, index) => (
                                <React.Fragment key={ver.version}>
                                    <div 
                                        className={`version-node ${ver.version === selectedVersion ? 'current' : ''}`}
                                        onClick={() => handleVersionSelect(ver.version)}
                                    >
                                        <div className="version-card">
                                            <div className="version-number">v{ver.version}</div>
                                            <div className="version-date">{ver.date}</div>
                                            <div className="file-icon">
                                                <i className="fas fa-file-alt"></i>
                                            </div>
                                            {ver.version === selectedVersion && (
                                                <div className="selected-indicator"></div>
                                            )}
                                        </div>
                                    </div>
                                    
                                    {index < versions.length - 1 && (
                                        <div className="version-connector-horizontal">
                                            <div className="connector-line"></div>
                                            <div className="connector-label">
                                                <span>Changes made</span>
                                            </div>
                                            <div className="arrow-right">
                                                <i className="fas fa-chevron-right"></i>
                                            </div>
                                        </div>
                                    )}
                                </React.Fragment>
                            ))}
                        </div>
                    </div>
                    
                    <div className="version-info">
                        <h3>Viewing Version {selectedVersion}</h3>
                        {selectedVersion === file.version ? (
                            <span className="latest-badge">Latest Version</span>
                        ) : (
                            <span className="history-badge">Historical Version</span>
                        )}
                    </div>
                    
                    <div className="content-panel">
                        {editMode ? (
                            <div className="file-editor-panel">
                                <h2>Edit File Content</h2>
                                <textarea 
                                    value={fileContent} 
                                    onChange={(e) => setFileContent(e.target.value)} 
                                    placeholder="Enter file content here..."
                                />
                                <div className="button-group">
                                    <button 
                                        className="cancel-button" 
                                        onClick={() => {
                                            setEditMode(false);
                                            setFileContent(file.content);
                                        }}
                                    >
                                        <i className="fas fa-times"></i> Cancel
                                    </button>
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
                            </div>
                        ) : (
                            <div className="file-content-panel">
                                <div className="panel-header">
                                    <h2>File Content</h2>
                                    {selectedVersion === file.version && (
                                        <button 
                                            className="edit-button" 
                                            onClick={handleEditLatestVersion}
                                        >
                                            <i className="fas fa-pencil-alt"></i> Edit
                                        </button>
                                    )}
                                </div>
                                <pre className="content-display">{selectedContent}</pre>
                            </div>
                        )}
                    </div>
                    
                    {selectedVersion !== file.version && (
                        <div className="version-navigation">
                            <button 
                                className="navigate-latest-btn"
                                onClick={() => handleVersionSelect(file.version)}
                            >
                                <i className="fas fa-forward"></i> Go to Latest Version
                            </button>
                        </div>
                    )}
                    
                    {summary && selectedVersion === file.version && (
                        <div className="summary-panel">
                            <h2>Last Change Summary</h2>
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
