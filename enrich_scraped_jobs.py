"""
Enrich existing scraped_jobs.json with detailed job information.
Extracts company, title, location, job type, description, and date posted.
"""

import json
import time
from scrape_job_details import extract_job_details


def load_scraped_jobs(filename='scraped_jobs.json'):
    """Load jobs from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse {filename}: {e}")
        return []


def enrich_jobs(jobs, delay=1.5):
    """
    Enrich jobs with detailed information.
    
    Args:
        jobs: List of job dictionaries with 'url' key
        delay: Delay between requests in seconds
    
    Returns:
        List of enriched job dictionaries
    """
    enriched_jobs = []
    total = len(jobs)
    
    print(f"\n{'='*70}")
    print(f"Enriching {total} jobs with detailed information...")
    print(f"{'='*70}")
    print(f"Estimated time: ~{int(total * delay / 60)} minutes ({total} jobs × {delay}s delay)\n")
    
    for i, job in enumerate(jobs, 1):
        url = job.get('url') or job.get('link')  # Handle different key names
        
        if not url:
            print(f"[{i}/{total}] ✗ No URL found, skipping")
            continue
        
        print(f"[{i}/{total}] Fetching: {url[:80]}...")
        
        # Extract detailed information
        details = extract_job_details(url)
        
        if details:
            # Merge original data with detailed information
            enriched_job = {
                'url': url,
                'company': details['company'],
                'job_title': details['title'],
                'location': details['location'],
                'job_type': details['job_type'],
                'employment_type': details['employment_type'],
                'salary': details['salary'],
                'date_posted': details['date_posted'],
                'description': details['description'],
                # Keep original search metadata if available
                'search_title': job.get('title'),
                'search_snippet': job.get('snippet')
            }
            enriched_jobs.append(enriched_job)
            
            # Print summary
            print(f"  ✓ {details['company']} - {details['title']}")
            print(f"    {details['job_type']} | {details['location']}")
            if details['date_posted']:
                print(f"    Posted: {details['date_posted']}")
        else:
            print(f"  ✗ Failed to extract details")
            # Keep original job data even if enrichment fails
            enriched_jobs.append({
                'url': url,
                'error': 'Failed to extract details',
                **job
            })
        
        # Be respectful - delay between requests
        if i < total:
            time.sleep(delay)
    
    print(f"\n{'='*70}")
    print(f"Successfully enriched {len(enriched_jobs)} jobs")
    print(f"{'='*70}\n")
    
    return enriched_jobs


def save_enriched_jobs(jobs, filename='enriched_jobs.json'):
    """Save enriched jobs to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(jobs)} enriched jobs to: {filename}")


def print_summary(jobs):
    """Print summary of enriched jobs."""
    print(f"\n{'='*70}")
    print("ENRICHED JOBS SUMMARY:")
    print(f"{'='*70}\n")
    
    # Show first 5 jobs
    for i, job in enumerate(jobs[:5], 1):
        print(f"{i}. {job.get('company', 'N/A')} - {job.get('job_title', 'N/A')}")
        print(f"   Type: {job.get('job_type', 'N/A')} | Location: {job.get('location', 'N/A')}")
        if job.get('salary'):
            print(f"   Salary: {job['salary']}")
        if job.get('date_posted'):
            print(f"   Posted: {job['date_posted']}")
        print(f"   URL: {job['url']}")
        print()
    
    if len(jobs) > 5:
        print(f"... and {len(jobs) - 5} more jobs\n")
    
    # Print statistics
    print(f"{'='*70}")
    print("STATISTICS:")
    print(f"{'='*70}")
    print(f"Total jobs: {len(jobs)}")
    
    # Job type breakdown
    job_types = {}
    for job in jobs:
        jtype = job.get('job_type') or 'Unknown'
        job_types[jtype] = job_types.get(jtype, 0) + 1
    
    print("\nJob Types:")
    for jtype, count in sorted(job_types.items(), key=lambda x: (x[0] is None, x[0])):
        print(f"  {jtype}: {count}")
    
    # Companies with most jobs
    companies = {}
    for job in jobs:
        company = job.get('company', 'Unknown')
        if company:
            companies[company] = companies.get(company, 0) + 1
    
    print("\nTop 10 Companies:")
    sorted_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]
    for company, count in sorted_companies:
        print(f"  {company}: {count} job(s)")
    
    # Jobs with salary info
    jobs_with_salary = sum(1 for job in jobs if job.get('salary'))
    print(f"\nJobs with salary info: {jobs_with_salary}/{len(jobs)} ({jobs_with_salary/len(jobs)*100:.1f}%)")
    
    # Jobs with date posted
    jobs_with_date = sum(1 for job in jobs if job.get('date_posted'))
    print(f"Jobs with date posted: {jobs_with_date}/{len(jobs)} ({jobs_with_date/len(jobs)*100:.1f}%)")


def main():
    """Main function - enrich jobs from scraped_jobs.json."""
    
    input_file = 'scraped_jobs.json'
    output_file = 'enriched_jobs.json'
    
    print("="*70)
    print("JOB ENRICHMENT SCRIPT")
    print("="*70)
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print("="*70)
    
    # Load existing jobs
    jobs = load_scraped_jobs(input_file)
    
    if not jobs:
        print(f"\nNo jobs found in {input_file}")
        return
    
    print(f"\nLoaded {len(jobs)} jobs from {input_file}")
    
    # Ask for confirmation
    print(f"\nThis will make {len(jobs)} HTTP requests to fetch detailed information.")
    print(f"Estimated time: ~{int(len(jobs) * 1.5 / 60)} minutes")
    
    response = input("\nProceed? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Cancelled.")
        return
    
    # Enrich jobs
    enriched_jobs = enrich_jobs(jobs)
    
    # Save results
    save_enriched_jobs(enriched_jobs, output_file)
    
    # Print summary
    print_summary(enriched_jobs)
    
    print(f"\n{'='*70}")
    print(f"✓ Done! Enriched jobs saved to: {output_file}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
