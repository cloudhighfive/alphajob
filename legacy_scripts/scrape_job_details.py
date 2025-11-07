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

        print(f"\n[extract_job_details] Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=10, verify=True)
        print(f"[extract_job_details] HTTP status: {response.status_code}")
        print(f"[extract_job_details] Response length: {len(response.text)} characters")
        response.raise_for_status()

        # Save raw HTML for debugging
        with open("debug_raw_html.txt", "w", encoding="utf-8") as f:
            f.write(response.text)

        soup = BeautifulSoup(response.text, 'html.parser')
        print(f"[extract_job_details] Parsed HTML with BeautifulSoup.")
        print(f"[extract_job_details] Soup text length: {len(soup.get_text())}")

        # Save soup text for debugging
        with open("debug_soup_text.txt", "w", encoding="utf-8") as f:
            f.write(soup.get_text(separator='\n', strip=True))

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
            print("[extract_job_details] Found JSON-LD script.")
            try:
                structured_data = json.loads(json_ld_script.string)
                print(f"[extract_job_details] Parsed JSON-LD: keys={list(structured_data.keys())}")

                # Extract company name
                if 'hiringOrganization' in structured_data:
                    job_details['company'] = structured_data['hiringOrganization'].get('name')
                    print(f"[extract_job_details] Company: {job_details['company']}")

                # Extract job title
                job_details['title'] = structured_data.get('title')
                print(f"[extract_job_details] Title: {job_details['title']}")

                # Extract description
                description_html = structured_data.get('description', '')
                if description_html:
                    desc_soup = BeautifulSoup(description_html, 'html.parser')
                    job_details['description'] = desc_soup.get_text(separator='\n', strip=True)
                    print(f"[extract_job_details] Description length: {len(job_details['description']) if job_details['description'] else 0}")

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
                        print(f"[extract_job_details] Location: {job_details['location']}")

                # Extract job type (remote/onsite/hybrid)
                job_location_type = structured_data.get('jobLocationType')
                if job_location_type == 'TELECOMMUTE':
                    job_details['job_type'] = 'Remote'
                elif 'applicantLocationRequirements' in structured_data:
                    job_details['job_type'] = 'Remote'
                else:
                    job_details['job_type'] = 'Onsite'
                print(f"[extract_job_details] Job type: {job_details['job_type']}")

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
                    print(f"[extract_job_details] Employment type: {job_details['employment_type']}")

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
                        print(f"[extract_job_details] Salary: {job_details['salary']}")

                # Extract date posted
                date_posted = structured_data.get('datePosted')
                if date_posted:
                    job_details['date_posted'] = date_posted
                    print(f"[extract_job_details] Date posted: {job_details['date_posted']}")

            except json.JSONDecodeError as e:
                print(f"[extract_job_details] Warning: Could not parse JSON-LD data: {e}")
        
        # Strategy 2: Fallback to meta tags if JSON-LD is not available
        if not job_details['title']:
            title_meta = soup.find('meta', {'property': 'og:title'})
            if title_meta:
                job_details['title'] = title_meta.get('content')
                print(f"[extract_job_details] Fallback og:title: {job_details['title']}")

        # Strategy 3: Try to find title from page title tag
        if not job_details['title']:
            title_tag = soup.find('title')
            if title_tag:
                # Format: "Job Title @ Company"
                title_text = title_tag.string
                print(f"[extract_job_details] Fallback <title>: {title_text}")
                if ' @ ' in title_text:
                    parts = title_text.split(' @ ')
                    job_details['title'] = parts[0].strip()
                    if not job_details['company']:
                        job_details['company'] = parts[1].strip()

        # Strategy 4: Try to extract from window.__appData (Ashby-specific)
        app_data_script = soup.find('script', string=lambda t: t and 'window.__appData' in t)
        if app_data_script and not job_details['description']:
            print("[extract_job_details] Found window.__appData script.")
            try:
                # Extract JSON from window.__appData = {...};
                script_content = app_data_script.string
                json_start = script_content.find('{')
                json_end = script_content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    app_data = json.loads(script_content[json_start:json_end])
                    print(f"[extract_job_details] Parsed window.__appData: keys={list(app_data.keys())}")

                    # Extract from posting object
                    if 'posting' in app_data:
                        posting = app_data['posting']

                        if not job_details['title']:
                            job_details['title'] = posting.get('title')
                            print(f"[extract_job_details] Ashby title: {job_details['title']}")

                        if not job_details['location']:
                            job_details['location'] = posting.get('locationName')
                            print(f"[extract_job_details] Ashby location: {job_details['location']}")

                        if not job_details['description']:
                            desc_plain = posting.get('descriptionPlainText')
                            if desc_plain:
                                job_details['description'] = desc_plain
                                print(f"[extract_job_details] Ashby description length: {len(desc_plain)}")

                        # Check if remote from isRemote flag
                        if posting.get('isRemote'):
                            job_details['job_type'] = 'Remote'
                        elif posting.get('workplaceType') == 'Remote':
                            job_details['job_type'] = 'Remote'
                        elif posting.get('workplaceType') == 'Hybrid':
                            job_details['job_type'] = 'Hybrid'
                        elif not job_details['job_type']:
                            job_details['job_type'] = 'Onsite'
                        print(f"[extract_job_details] Ashby job_type: {job_details['job_type']}")

                        # Get employment type
                        if not job_details['employment_type']:
                            emp_type = posting.get('employmentType')
                            if emp_type:
                                job_details['employment_type'] = emp_type.replace('_', ' ').title()
                                print(f"[extract_job_details] Ashby employment_type: {job_details['employment_type']}")

                        # Extract date posted from posting
                        if not job_details['date_posted']:
                            published_date = posting.get('publishedDate')
                            if published_date:
                                job_details['date_posted'] = published_date
                                print(f"[extract_job_details] Ashby date_posted: {job_details['date_posted']}")

                    # Extract organization name
                    if 'organization' in app_data and not job_details['company']:
                        job_details['company'] = app_data['organization'].get('name')
                        print(f"[extract_job_details] Ashby company: {job_details['company']}")

            except (json.JSONDecodeError, ValueError) as e:
                print(f"[extract_job_details] Warning: Could not parse window.__appData: {e}")
        
        # Strategy 5: Fallback to HTML content scraping if still missing description
        if not job_details['description']:
            print("[extract_job_details] Fallback: Trying HTML content scraping...")
            # Create a copy of soup to avoid modifying the original
            soup_copy = BeautifulSoup(response.text, 'html.parser')
            # Remove script/style/meta/link/svg/img
            for script in soup_copy(["script", "style", "noscript", "meta", "link", "svg", "img"]):
                script.decompose()
            # Try common containers
            job_content = None
            for selector in [
                {'class': 'job-description'},
                {'class': 'job-content'},
                {'id': 'job-description'},
                {'role': 'main'},
                {'class': 'posting-content'},
                {'class': 'description'},
            ]:
                job_content = soup_copy.find(['div', 'section', 'article'], selector)
                print(f"[extract_job_details] Trying selector: {selector} -> {'FOUND' if job_content else 'not found'}")
                if job_content:
                    print(f"[extract_job_details] Found job content container: {selector}")
                    break
            if not job_content:
                job_content = soup_copy.find('body') or soup_copy
                print(f"[extract_job_details] Using full body content")
            plain_text = job_content.get_text(separator='\n', strip=True)
            if plain_text and len(plain_text) > 100:
                job_details['description'] = plain_text
                if len(plain_text) > 500:
                    with open("debug_htmlscrape_description.txt", "w", encoding="utf-8") as f:
                        f.write(plain_text)
                    print(f"[extract_job_details] Saved HTML scrape description to debug_htmlscrape_description.txt ({len(plain_text)} chars)")
                else:
                    print(f"[extract_job_details] HTML scrape description: {plain_text[:100]}...")
        
        # Strategy 6: Last resort - Use AI if still missing critical fields
        if not job_details['description'] or not job_details['title']:
            print("[extract_job_details] Last resort: Using AI for extraction...")
            try:
                from src.services.ai_service import AIService
                from src.config.settings import Settings
                settings = Settings()
                ai_service = AIService(settings)
                
                # Get text for AI
                ai_text = soup.get_text(separator='\n', strip=True)
                
                prompt = f"""You are a job data extraction expert. Extract ALL information from this job posting.

JOB POSTING TEXT:
{ai_text}

SOURCE URL: {url}

Extract and return a valid JSON object with these EXACT fields:

{{
  "company": "Company name (required)",
  "title": "Full job title (required)",
  "location": "City, State/Country or 'Remote'",
  "job_type": "Remote" OR "Hybrid" OR "Onsite",
  "description": "COMPLETE job description - include EVERYTHING",
  "salary": "Salary/compensation if mentioned, otherwise null",
  "employment_type": "Full-time" OR "Part-time" OR "Contract" OR "Temporary" OR "Internship",
  "date_posted": "Date if mentioned, otherwise null"
}}

Return ONLY valid JSON - no explanation, no markdown, no commentary.

JSON:"""
                
                if len(prompt) > 1000:
                    with open("debug_ai_prompt.txt", "w", encoding="utf-8") as f:
                        f.write(prompt)
                    print(f"[extract_job_details] Saved AI prompt to debug_ai_prompt.txt ({len(prompt)} chars)")
                
                ai_response = ai_service.generate_completion(prompt)
                
                if len(ai_response) > 1000:
                    with open("debug_ai_response.txt", "w", encoding="utf-8") as f:
                        f.write(ai_response)
                    print(f"[extract_job_details] Saved AI response to debug_ai_response.txt ({len(ai_response)} chars)")
                
                # Clean up AI response
                ai_response = ai_response.strip()
                if ai_response.startswith('```json'):
                    ai_response = ai_response[7:]
                elif ai_response.startswith('```'):
                    ai_response = ai_response[3:]
                if ai_response.endswith('```'):
                    ai_response = ai_response[:-3]
                ai_response = ai_response.strip()
                
                # Try to find JSON object
                if not ai_response.startswith('{'):
                    json_start = ai_response.find('{')
                    if json_start != -1:
                        ai_response = ai_response[json_start:]
                if not ai_response.endswith('}'):
                    json_end = ai_response.rfind('}')
                    if json_end != -1:
                        ai_response = ai_response[:json_end + 1]
                
                # Parse and merge AI results
                ai_json = json.loads(ai_response)
                for k, v in ai_json.items():
                    if v and not job_details.get(k):
                        job_details[k] = v
                        print(f"[extract_job_details] AI extracted {k}: {str(v)[:100]}{'...' if len(str(v)) > 100 else ''}")
            except Exception as e:
                print(f"[extract_job_details] AI fallback failed: {e}")
        
        return job_details
        
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error processing {url}: {e}")
        import traceback
        traceback.print_exc()
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
