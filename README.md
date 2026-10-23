# AI-Powered Intelligent Recruitment and Local Talent Discovery System

## Project Overview
The AI-Powered Intelligent Recruitment and Local Talent Discovery System is a web-based application designed to simplify recruitment. It helps HR professionals manage job postings, find suitable candidates, compare skills, and discover local talent.

## Objectives
- Reduce manual resume screening effort.
- Match candidate skills with job requirements.
- Help HR professionals shortlist suitable candidates.
- Support local talent discovery based on location.
- Provide a platform for candidates to explore job opportunities.

## Features
- User login and registration
- HR dashboard and job posting
- Candidate profile management
- Resume upload
- AI-based skill matching
- Candidate shortlisting
- Local talent discovery
- Job recommendations and application tracking

## Technologies Used
- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, FastAPI
- **Database:** Project-configured database
- **Development Tool:** Visual Studio Code

## Project Structure
```text
AI_Recruitment_System/
├── backend/
│   ├── main.py
│   ├── ai_matcher.py
│   ├── database.py
│   └── requirements.txt
├── static/
│   ├── css/
│   ├── js/
│   └── style.css
├── uploads/
├── index.html
├── login.html
├── register.html
├── candidate-dashboard.html
├── hr-dashboard.html
├── find-candidates.html
├── local-talent.html
└── post-job.html
```

## How to Run
1. Install Python and the required project dependencies.
2. Open the project folder in Visual Studio Code.
3. Open a terminal in the backend folder.
4. Install dependencies using:

   `pip install -r requirements.txt`

5. Start the backend server:

   `python -m uvicorn main:app --reload --port 8000`

6. Open the frontend using Live Server or the configured web server.

## Expected Outcome
The system aims to make recruitment more efficient by helping recruiters identify suitable candidates and discover local talent.

## Future Enhancements
- Advanced resume parsing
- Email notifications
- Interview scheduling
- Improved AI-based candidate recommendations

## Author
Keerthiga J

## License
This project is developed for academic purposes.
