# DataDoctor AI

An intelligent, web-based platform for dataset analysis.

## Features
- Data Quality Doctor
- Automatic interactive dashboards
- AI Insights Assistant
- Pattern Discovery
- Interactive Data Cleaning
- PDF and Excel report exports
- CSV and Excel uploads

## Technology Stack
- Python, Flask
- Pandas, NumPy, Scikit-learn
- Plotly
- HTML, CSS, JavaScript

## Project Structure
```text
DataDoctor-AI/
├── app.py
├── modules/
├── templates/
├── static/
├── uploads/
├── backups/
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation
1. Clone your GitHub repository.
2. Open the project directory.
3. Install dependencies:
   `pip install -r requirements.txt`
4. Set a secure SECRET_KEY environment variable.
5. Run `python app.py`.
6. Open the local Flask URL in your browser.

## Security
- Maximum upload size: 16 MB.
- Supported formats: CSV, XLSX, XLS.
- Uploaded datasets and backups are excluded from Git.
- Environment secret files are excluded from Git.
- Configure a persistent secret key in production.

## Development Status
Main modules and automated tests completed.
Deployment and final documentation are pending.

## Author
DataDoctor AI Project
