import requests
from dotenv import load_dotenv
import os
import json
import urllib3
from scrape_job_details import extract_job_details
import time

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

# Load environment variables from .env file
load_dotenv()

# Get API key and CX from environment variables
API_KEY = os.getenv('GOOGLE_API_KEY')
CX = os.getenv('GOOGLE_CX')

def search_jobs(query, max_results=100):
    """
    Search Google for job-related URLs using Custom Search API with pagination.
    Google Custom Search API allows max 10 results per request and up to 100 total.
    """
    all_urls = []
    
    # Google CSE allows max 10 results per request
    results_per_page = 10
    # Calculate number of requests needed (max 100 results total due to API limit)
    num_requests = min((max_results + results_per_page - 1) // results_per_page, 10)
    
    print(f"Fetching up to {num_requests * results_per_page} results ({num_requests} requests)...")
    
    for page in range(num_requests):
        start_index = page * results_per_page + 1
        
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'key': API_KEY,
            'cx': CX,
            'q': query,
            'num': results_per_page,
            'start': start_index  # Pagination parameter
        }
        
        print(f"  Request {page + 1}/{num_requests} (starting at result {start_index})...")
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"  Error: {response.status_code} - {response.text}")
                break
            
            data = response.json()
            
            # Check if there are results
            items = data.get('items', [])
            if not items:
                print(f"  No more results found at page {page + 1}")
                break
            
            # Extract URLs
            for item in items:
                all_urls.append({
                    'url': item['link'],
                    'title': item.get('title', 'N/A'),
                    'snippet': item.get('snippet', 'N/A')
                })
            
            print(f"  Found {len(items)} results on page {page + 1}")
            
            # Check if we've reached the end
            search_info = data.get('searchInformation', {})
            total_results = int(search_info.get('totalResults', 0))
            
            if start_index + results_per_page > total_results:
                print(f"  Reached end of results (total: {total_results})")
                break
                
        except Exception as e:
            print(f"  Error on page {page + 1}: {e}")
            break
    
    return all_urls

def save_jobs(jobs, filename='scraped_jobs.json'):
    """Save job URLs and metadata to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(jobs)} jobs to {filename}")

def enrich_jobs_with_details(jobs, delay=1.5):
    """
    Fetch detailed information for each job URL.
    
    Args:
        jobs: List of job dictionaries with 'url' key
        delay: Delay between requests in seconds (be respectful to servers)
    
    Returns:
        List of enriched job dictionaries with detailed information
    """
    enriched_jobs = []
    total = len(jobs)
    
    print(f"\n{'='*60}")
    print(f"Fetching detailed information for {total} jobs...")
    print(f"{'='*60}")
    
    for i, job in enumerate(jobs, 1):
        url = job.get('url')
        print(f"\n[{i}/{total}] Processing: {url}")
        
        # Get detailed information
        details = extract_job_details(url)
        
        if details:
            # Merge original data with detailed information
            enriched_job = {
                **job,  # Keep original title, snippet from Google
                'company': details['company'],
                'job_title': details['title'],  # More accurate title from job page
                'location': details['location'],
                'job_type': details['job_type'],  # Remote/Onsite/Hybrid
                'employment_type': details['employment_type'],  # Full-time/Part-time
                'salary': details['salary'],
                'description': details['description']
            }
            enriched_jobs.append(enriched_job)
            
            print(f"✓ {details['company']} - {details['title']}")
            print(f"  {details['job_type']} | {details['location']}")
        else:
            # If detail extraction fails, keep original job data
            print(f"✗ Could not fetch details, keeping original data")
            enriched_jobs.append(job)
        
        # Be respectful - delay between requests
        if i < total:
            time.sleep(delay)
    
    print(f"\n{'='*60}")
    print(f"Successfully enriched {len(enriched_jobs)} jobs")
    print(f"{'='*60}\n")
    
    return enriched_jobs

if __name__ == '__main__':
    # Example query: Search for software engineer remote jobs on Ashby
    query = 'site:jobs.ashbyhq.com "software engineer" "remote"'
    
    print("STEP 1: Searching for job URLs via Google Custom Search API")
    print("=" * 60)
    
    # Fetch up to 100 results (Google CSE limit)
    jobs = search_jobs(query, max_results=100)
    
    print(f"\n{'='*60}")
    print(f"Total job URLs found: {len(jobs)}")
    print(f"{'='*60}\n")
    
    # Save basic results
    save_jobs(jobs, 'scraped_jobs_urls_only.json')
    
    # Ask user if they want to fetch detailed information
    print("\n" + "=" * 60)
    print("STEP 2: Fetch detailed job information (company, location, description, etc.)")
    print("=" * 60)
    print(f"\nThis will make {len(jobs)} additional HTTP requests.")
    print("Estimated time: ~{:.0f} seconds ({} jobs × 1.5 sec delay)".format(len(jobs) * 1.5, len(jobs)))
    
    fetch_details = input("\nFetch detailed information? (y/n): ").strip().lower()
    
    if fetch_details == 'y':
        # Enrich jobs with detailed information
        enriched_jobs = enrich_jobs_with_details(jobs)
        
        # Save enriched results
        save_jobs(enriched_jobs, 'scraped_jobs.json')
        
        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY OF ENRICHED JOBS:")
        print("=" * 60)
        for i, job in enumerate(enriched_jobs[:5], 1):  # Show first 5
            print(f"\n{i}. {job.get('company', 'N/A')} - {job.get('job_title', job.get('title', 'N/A'))}")
            print(f"   Type: {job.get('job_type', 'N/A')} | Location: {job.get('location', 'N/A')}")
            if job.get('salary'):
                print(f"   Salary: {job['salary']}")
            print(f"   URL: {job['url']}")
        
        if len(enriched_jobs) > 5:
            print(f"\n... and {len(enriched_jobs) - 5} more jobs")
        
        print(f"\n{'='*60}")
        print(f"✓ All {len(enriched_jobs)} enriched jobs saved to: scraped_jobs.json")
        print(f"{'='*60}")
    else:
        print("\nSkipped detailed fetching. Basic URLs saved to: scraped_jobs_urls_only.json")