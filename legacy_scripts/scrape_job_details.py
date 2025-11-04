"""
Job Details Scraper - Extracts detailed information from job posting URLs
Fetches: company name, job title, location, job type (remote/hybrid/onsite), and description
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, Optional
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)


def extract_job_details(url: str) -> Optional[Dict]:
    """
    Extract job details from a job posting URL.
    
    Args:
        url: Job posting URL
        
    Returns:
        Dictionary with job details or None if extraction fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10, verify=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize job details dictionary
        job_details = {
            'url': url,
            'company': None,
            'title': None,
            'location': None,
            'job_type': None,
            'description': None,
            'salary': None,
            'employment_type': None,
            'date_posted': None
        }
        
        # Strategy 1: Extract from JSON-LD structured data (most reliable)
        json_ld_script = soup.find('script', {'type': 'application/ld+json'})
        if json_ld_script:
            try:
                structured_data = json.loads(json_ld_script.string)
                
                # Extract company name
                if 'hiringOrganization' in structured_data:
                    job_details['company'] = structured_data['hiringOrganization'].get('name')
                
                # Extract job title
                job_details['title'] = structured_data.get('title')
                
                # Extract description
                description_html = structured_data.get('description', '')
                if description_html:
                    desc_soup = BeautifulSoup(description_html, 'html.parser')
                    job_details['description'] = desc_soup.get_text(separator='\n', strip=True)
                
                # Extract location information
                if 'jobLocation' in structured_data:
                    location = structured_data['jobLocation']
                    if 'address' in location:
                        address = location['address']
                        location_parts = []
                        if 'addressLocality' in address:
                            location_parts.append(address['addressLocality'])
                        if 'addressRegion' in address:
                            location_parts.append(address['addressRegion'])
                        if 'addressCountry' in address:
                            location_parts.append(address['addressCountry'])
                        job_details['location'] = ', '.join(location_parts) if location_parts else None
                
                # Extract job type (remote/onsite/hybrid)
                job_location_type = structured_data.get('jobLocationType')
                if job_location_type == 'TELECOMMUTE':
                    job_details['job_type'] = 'Remote'
                elif 'applicantLocationRequirements' in structured_data:
                    job_details['job_type'] = 'Remote'
                else:
                    job_details['job_type'] = 'Onsite'
                
                # Extract employment type (Full-time, Part-time, etc.)
                employment_type = structured_data.get('employmentType')
                if employment_type:
                    type_mapping = {
                        'FULL_TIME': 'Full-time',
                        'PART_TIME': 'Part-time',
                        'CONTRACT': 'Contract',
                        'TEMPORARY': 'Temporary',
                        'INTERN': 'Internship'
                    }
                    job_details['employment_type'] = type_mapping.get(employment_type, employment_type)
                
                # Extract salary information
                if 'baseSalary' in structured_data:
                    salary_info = structured_data['baseSalary']
                    if 'value' in salary_info:
                        value = salary_info['value']
                        currency = salary_info.get('currency', 'USD')
                        min_val = value.get('minValue')
                        max_val = value.get('maxValue')
                        
                        if min_val and max_val:
                            job_details['salary'] = f"${min_val:,} - ${max_val:,} {currency}"
                        elif min_val:
                            job_details['salary'] = f"${min_val:,}+ {currency}"
                
                # Extract date posted
                date_posted = structured_data.get('datePosted')
                if date_posted:
                    job_details['date_posted'] = date_posted
                
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse JSON-LD data: {e}")
        
        # Strategy 2: Fallback to meta tags if JSON-LD is not available
        if not job_details['title']:
            title_meta = soup.find('meta', {'property': 'og:title'})
            if title_meta:
                job_details['title'] = title_meta.get('content')
        
        # Strategy 3: Try to find title from page title tag
        if not job_details['title']:
            title_tag = soup.find('title')
            if title_tag:
                # Format: "Job Title @ Company"
                title_text = title_tag.string
                if ' @ ' in title_text:
                    parts = title_text.split(' @ ')
                    job_details['title'] = parts[0].strip()
                    if not job_details['company']:
                        job_details['company'] = parts[1].strip()
        
        # Strategy 4: Try to extract from window.__appData (Ashby-specific)
        app_data_script = soup.find('script', string=lambda t: t and 'window.__appData' in t)
        if app_data_script and not job_details['description']:
            try:
                # Extract JSON from window.__appData = {...};
                script_content = app_data_script.string
                json_start = script_content.find('{')
                json_end = script_content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    app_data = json.loads(script_content[json_start:json_end])
                    
                    # Extract from posting object
                    if 'posting' in app_data:
                        posting = app_data['posting']
                        
                        if not job_details['title']:
                            job_details['title'] = posting.get('title')
                        
                        if not job_details['location']:
                            job_details['location'] = posting.get('locationName')
                        
                        if not job_details['description']:
                            desc_plain = posting.get('descriptionPlainText')
                            if desc_plain:
                                job_details['description'] = desc_plain
                        
                        # Check if remote from isRemote flag
                        if posting.get('isRemote'):
                            job_details['job_type'] = 'Remote'
                        elif posting.get('workplaceType') == 'Remote':
                            job_details['job_type'] = 'Remote'
                        elif posting.get('workplaceType') == 'Hybrid':
                            job_details['job_type'] = 'Hybrid'
                        elif not job_details['job_type']:
                            job_details['job_type'] = 'Onsite'
                        
                        # Get employment type
                        if not job_details['employment_type']:
                            emp_type = posting.get('employmentType')
                            if emp_type:
                                job_details['employment_type'] = emp_type.replace('_', ' ').title()
                        
                        # Extract date posted from posting
                        if not job_details['date_posted']:
                            published_date = posting.get('publishedDate')
                            if published_date:
                                job_details['date_posted'] = published_date
                    
                    # Extract organization name
                    if 'organization' in app_data and not job_details['company']:
                        job_details['company'] = app_data['organization'].get('name')
                        
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Warning: Could not parse window.__appData: {e}")
        
        return job_details
        
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error processing {url}: {e}")
        return None


def scrape_multiple_jobs(urls: list, delay: float = 1.0) -> list:
    """
    Scrape details from multiple job URLs.
    
    Args:
        urls: List of job posting URLs
        delay: Delay between requests in seconds (be respectful)
        
    Returns:
        List of job detail dictionaries
    """
    jobs = []
    total = len(urls)
    
    print(f"\nScraping details for {total} jobs...")
    print("=" * 60)
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{total}] Fetching: {url}")
        
        job_details = extract_job_details(url)
        
        if job_details:
            jobs.append(job_details)
            print(f"✓ {job_details['company']} - {job_details['title']}")
            print(f"  Location: {job_details['location']}")
            print(f"  Type: {job_details['job_type']} | {job_details['employment_type']}")
            if job_details['salary']:
                print(f"  Salary: {job_details['salary']}")
        else:
            print(f"✗ Failed to extract details")
        
        # Be respectful - add delay between requests
        if i < total:
            time.sleep(delay)
    
    print("\n" + "=" * 60)
    print(f"Successfully scraped {len(jobs)} out of {total} jobs")
    
    return jobs


def main():
    """Main function - test with a single URL."""
    
    # Test URL
    test_url = "https://jobs.ashbyhq.com/quora/4a1c3621-229a-41dc-bf7d-282b0365a85b"
    
    print("Testing job details scraper...")
    print(f"URL: {test_url}\n")
    
    job_details = extract_job_details(test_url)
    
    if job_details:
        print("\n" + "=" * 60)
        print("EXTRACTED JOB DETAILS:")
        print("=" * 60)
        print(f"Company:         {job_details['company']}")
        print(f"Title:           {job_details['title']}")
        print(f"Location:        {job_details['location']}")
        print(f"Job Type:        {job_details['job_type']}")
        print(f"Employment Type: {job_details['employment_type']}")
        if job_details['salary']:
            print(f"Salary:          {job_details['salary']}")
        if job_details['date_posted']:
            print(f"Date Posted:     {job_details['date_posted']}")
        print(f"\nDescription Preview:")
        print("-" * 60)
        if job_details['description']:
            # Print first 500 characters of description
            desc_preview = job_details['description'][:500]
            print(desc_preview)
            if len(job_details['description']) > 500:
                print(f"\n... ({len(job_details['description']) - 500} more characters)")
        print("=" * 60)
        
        # Save to JSON file
        output_file = "job_details_test.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(job_details, f, indent=2, ensure_ascii=False)
        print(f"\nSaved detailed results to: {output_file}")
    else:
        print("Failed to extract job details")


if __name__ == "__main__":
    main()
