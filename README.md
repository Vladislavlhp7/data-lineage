# Data Lineage Application

A full-stack application for tracking changes to files over time with visual data lineage capabilities. This application allows users to upload text files, make modifications, and visualize the history of changes.

## Features

- File upload and storage
- File editing with version history tracking
- Visual representation of file lineage
- Change summaries between versions
- Responsive UI for desktop and mobile

## Tech Stack

### Backend
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- SQLite (Database)
- Mistral AI API (for summarizing changes)

### Frontend
- React
- React Router
- Axios (for API requests)
- CSS for styling
- Font Awesome (for icons)

## Project Structure

```
data-lineage/
├── backend/              # FastAPI server
│   ├── app.py            # Main application file
│   ├── requirements.txt  # Python dependencies
│   └── uploaded_files/   # Directory for stored files
├── frontend/             # React application
│   ├── public/           # Static files
│   ├── src/              # React source code
│   ├── package.json      # Node.js dependencies
│   └── ...
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Vladislavlhp7/data-lineage.git
   cd data-lineage
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate
   ```

3. Install the Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install the Node.js dependencies:
   ```bash
   npm install
   # or, if using yarn
   yarn install
   ```

## Running the Application

### Start the Backend Server

1. From the backend directory, run:
   ```bash
   cd ../backend
   python app.py
   ```
   The server will start at `http://localhost:8000`.

2. Access the FastAPI documentation:
   - API documentation: `http://localhost:8000/docs`
   - Alternative documentation: `http://localhost:8000/redoc`

### Start the Frontend Server

1. From the frontend directory, run:
   ```bash
   cd ../frontend
   npm start
   # or, if using yarn
   yarn start
   ```
   The development server will start at `http://localhost:3000`.

2. Open your browser and navigate to `http://localhost:3000`.

## Usage Guide

### Home Page

- The home page displays all your files in a user-friendly interface.
- Upload new files using the "Upload New File" button.
- Click on any file card to view and edit the file.
- Delete files by clicking the trash icon.

### File Lineage View

- View the file's version history represented as a timeline.
- Edit the file content in the text editor.
- Save changes to create a new version.
- View a summary of the changes made between versions.

## Development Notes

### Backend API Endpoints

- `GET /files`: List all files
- `GET /files/{file_id}`: Get a specific file by ID
- `POST /upload`: Upload a new file
- `POST /modify/{file_id}`: Modify an existing file
- `DELETE /delete/{file_id}`: Delete a file

### Mistral API Integration

The application uses Mistral AI API for summarizing changes between file versions. To enable this feature:

1. Replace the placeholder API key in `app.py`:
   ```python
   # Replace this:
   # "Authorization": "Bearer YOUR_API_KEY"
   # With your actual API key:
   "Authorization": "Bearer your_actual_api_key_here"
   ```

2. Uncomment the API call in the `summarize_changes` function.

## Troubleshooting

### Node.js Crypto Module Issues

If you encounter crypto-related errors when starting the frontend, update the start script in `package.json` to include:

```json
"start": "export NODE_OPTIONS=--openssl-legacy-provider && react-scripts start"
```

### CORS Issues

If you encounter CORS issues, ensure the backend CORS middleware is properly configured in `app.py`.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.