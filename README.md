# Job Finder API

A FastAPI-based job search application that aggregates and filters job listings from multiple sources using LLM-based relevance matching.

## Features

- Aggregates job listings from LinkedIn, Indeed, and Rozee.pk
- Uses job filtering  for intelligent job matching
- Filters jobs based on position, experience, skills, location, and salary
- Returns structured job listings with detailed information

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a .env file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## API Endpoints

### POST /find-jobs

Search for jobs based on specific criteria.

#### Request Body
```json
{
    "position": "Full Stack Engineer",
    "experience": "2 years",
    "salary": "70,000 PKR to 120,000 PKR",
    "jobNature": "onsite",
    "location": "Peshawar, Pakistan",
    "skills": "full stack, MERN, Node.js, Express.js, React.js, Next.js, Firebase, TailwindCSS, CSS Frameworks, Tokens handling"
}
```

#### Response
```json
{
    "message": "Job search completed successfully",
    "total_jobs": 2,
    "relevant_jobs": [
        {
            "job_title": "Full Stack Engineer",
            "company": "XYZ Pvt Ltd",
            "experience": "2+ years",
            "jobNature": "onsite",
            "location": "Islamabad, Pakistan",
            "salary": "100,000 PKR",
            "apply_link": "https://linkedin.com/job123",
            "description": "Job description here..."
        }
    ]
}
```

## How It Works

1. The API receives job search criteria from the user
2. It scrapes job listings from multiple sources (LinkedIn, Indeed, Rozee.pk)
3. Each job listing is analyzed by an LLM to determine relevance based on:
   - Position match
   - Experience requirements
   - Required skills
   - Location preference
   - Salary range
   - Job nature (onsite/remote)
4. Relevant jobs are returned in a structured format

## Technologies Used

- FastAPI
- OpenAI GPT-3.5
- LangChain
- BeautifulSoup4
- Python-dotenv

## Future Improvements

- Add more job sources like (Indeed, Rozee.pk)
- Implement real-time job scraping
- Add job application filtering using LLM
- Implement user authentication
- Add job recommendations based on the user profile 
