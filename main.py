# job_finder.py
from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import time
from pydantic import BaseModel
from typing import List, Optional
import random
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI(title="Job Finder API", 
              description="API to fetch job listings from LinkedIn based on user inputs")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input model
class JobSearchRequest(BaseModel):
    position: str
    experience: Optional[str] = None
    salary: Optional[str] = None
    jobNature: Optional[str] = "any"  # onsite, remote, hybrid, any
    location: Optional[str] = "Pakistan"
    skills: Optional[str] = None

# Output models
class JobListing(BaseModel):
    job_title: str
    company: str
    experience: Optional[str] = None
    jobNature: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    apply_link: str
    description: Optional[str] = None

class JobSearchResponse(BaseModel):
    relevant_jobs: List[JobListing]

@app.post("/api/job-search", response_model=JobSearchResponse)
async def search_jobs(search_request: JobSearchRequest):
    title = search_request.position
    location = search_request.location
    
    try:
        job_listings = fetch_linkedin_jobs(search_request)
        filtered_jobs = filter_jobs(job_listings, search_request)
        return {"relevant_jobs": filtered_jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

def fetch_linkedin_jobs(search_request: JobSearchRequest, max_jobs=10):
    title = search_request.position
    location = search_request.location
    
    job_list = []
    start = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    while len(job_list) < max_jobs:
        try:
            list_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={title}&location={location}&start={start}"
            response = requests.get(list_url, headers=headers)
            
            if response.status_code != 200:
                break
                
            list_soup = BeautifulSoup(response.text, "html.parser")
            page_jobs = list_soup.find_all("li")
            
            if not page_jobs:
                break
                
            id_list = []
            for job in page_jobs:
                try:
                    base_card_div = job.find("div", {"class": "base-card"})
                    if base_card_div and base_card_div.get("data-entity-urn"):
                        job_id = base_card_div.get("data-entity-urn").split(":")[-1]
                        id_list.append(job_id)
                except Exception as e:
                    print(f"Error extracting job ID: {e}")
                    continue
            
            for job_id in id_list:
                job_details = fetch_job_details(job_id)
                if job_details and job_details.get("job_title") and job_details.get("company"):
                    job_list.append(job_details)
                
                if len(job_list) >= max_jobs:
                    break
                time.sleep(random.uniform(1, 2))
            
            start += len(page_jobs)
            if len(page_jobs) < 25:
                break
                
        except Exception as e:
            print(f"Error fetching jobs: {e}")
            break
            
    return job_list

def fetch_job_details(job_id):
    try:
        job_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        job_response = requests.get(job_url, headers=headers)
        
        if job_response.status_code != 200:
            return None
            
        job_soup = BeautifulSoup(job_response.text, "html.parser")
        job_post = {}
        
        # Job Title
        title = job_soup.select_one("h2[class*=top-card-layout__title]")
        job_post["job_title"] = title.get_text(strip=True) if title else None
        
        # Company Name
        company = job_soup.select_one("a[class*=topcard__org-name-link], span[class*=topcard__flavor]")
        job_post["company"] = company.get_text(strip=True) if company else None
        
        # Extract all criteria items
        criteria_items = job_soup.find_all("div", class_="job-criteria-item")
        
        # Experience Level
        experience = None
        for item in criteria_items:
            label = item.find("h3", class_="job-criteria-subheader")
            if label and any(keyword in label.get_text(strip=True).lower() for keyword in ["experience", "seniority", "level"]):
                value = item.find("span", class_="job-criteria-text")
                if value:
                    experience = value.get_text(strip=True)
                    break
        job_post["experience"] = experience
        
        # Job Nature (Workplace Type)
        job_nature = None
        for item in criteria_items:
            label = item.find("h3", class_="job-criteria-subheader")
            if label and any(keyword in label.get_text(strip=True).lower() for keyword in ["workplace", "work", "type", "location"]):
                value = item.find("span", class_="job-criteria-text")
                if value:
                    nature_text = value.get_text(strip=True).lower()
                    if "remote" in nature_text:
                        job_nature = "remote"
                    elif "hybrid" in nature_text:
                        job_nature = "hybrid"
                    else:
                        job_nature = "onsite"
                    break
        job_post["jobNature"] = job_nature
        
        # Location
        loc = job_soup.find("span", class_="topcard__flavor--bullet")
        job_post["location"] = loc.get_text(strip=True) if loc else None
        
        # Salary
        sal = job_soup.find("div", class_="salary compensation__salary")
        job_post["salary"] = sal.get_text(strip=True) if sal else None
        
        # Apply Link
        job_post["apply_link"] = f"https://www.linkedin.com/jobs/view/{job_id}"
        
        # Description
        desc = job_soup.find("div", class_="show-more-less-html__markup")
        job_post["description"] = desc.get_text(strip=True) if desc else None
        
        return job_post
        
    except Exception as e:
        print(f"Error fetching job details: {e}")
        return None

def filter_jobs(job_listings, search_request):
    filtered_jobs = []
    
    for job in job_listings:
        match_score = 0
        
        if search_request.jobNature and search_request.jobNature.lower() != "any":
            if not job.get("jobNature") or job.get("jobNature") != search_request.jobNature.lower():
                continue
                
        if search_request.experience:
            req_exp = extract_years(search_request.experience)
            job_exp = extract_years(job.get("experience", "0"))
            
            if job_exp > req_exp + 2:
                continue
            
            if abs(job_exp - req_exp) <= 1:
                match_score += 1
        
        if search_request.skills:
            skills_list = [s.strip().lower() for s in search_request.skills.split(',')]
            desc = (job.get("description", "") + " " + job.get("job_title", "")).lower()
            matched = sum(1 for skill in skills_list if skill in desc)
            match_score += matched / len(skills_list) * 2
        
        if match_score > 0:
            filtered_jobs.append(job)
    
    return filtered_jobs if filtered_jobs else job_listings

def extract_years(exp_str):
    if not exp_str:
        return 0
    exp_str = exp_str.lower()
    years = re.findall(r'(\d+)[\+]?\s*(?:year|yr)', exp_str)
    if years:
        return int(years[0])
    elif "entry" in exp_str or "junior" in exp_str:
        return 0
    elif "mid" in exp_str:
        return 3
    elif "senior" in exp_str:
        return 5
    return 0



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)