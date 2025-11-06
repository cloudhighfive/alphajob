"""
Job Search Web UI - Combined job scraping and enrichment tool
Run with: python job_search_web_ui.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

# Add legacy scripts to path
sys.path.insert(0, str(Path(__file__).parent / "legacy_scripts"))
from scrape_job_details import extract_job_details

# Load environment variables
load_dotenv()

# Get API credentials
API_KEY = os.getenv('GOOGLE_API_KEY')
CX = os.getenv('GOOGLE_CX')

app = Flask(__name__)


def search_jobs(query, max_results=20):
    """Search Google for job URLs using Custom Search API."""
    all_urls = []
    results_per_page = 10
    num_requests = min((max_results + results_per_page - 1) // results_per_page, 10)
    
    for page in range(num_requests):
        start_index = page * results_per_page + 1
        
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'key': API_KEY,
            'cx': CX,
            'q': query,
            'num': results_per_page,
            'start': start_index
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                break
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break
            
            for item in items:
                all_urls.append({
                    'url': item['link'],
                    'title': item.get('title', 'N/A'),
                    'snippet': item.get('snippet', 'N/A')
                })
            
            # Check if we've reached the end
            search_info = data.get('searchInformation', {})
            total_results = int(search_info.get('totalResults', 0))
            
            if start_index + results_per_page > total_results:
                break
            
        except Exception as e:
            print(f"Error on page {page + 1}: {e}")
            break
    
    return all_urls


def enrich_jobs(job_urls):
    """Extract detailed information for each job URL."""
    enriched_jobs = []
    
    for i, job in enumerate(job_urls, 1):
        print(f"[{i}/{len(job_urls)}] Extracting: {job['url'][:70]}...")
        
        details = extract_job_details(job['url'])
        
        if details:
            enriched_job = {
                'url': job['url'],
                'company': details['company'],
                'job_title': details['title'],
                'location': details['location'],
                'job_type': details['job_type'],
                'employment_type': details['employment_type'],
                'salary': details['salary'],
                'date_posted': details['date_posted'],
                'description': details['description'],
                'search_title': job.get('title'),
                'search_snippet': job.get('snippet')
            }
            enriched_jobs.append(enriched_job)
            print(f"  ✓ {details['company']} - {details['title']}")
        else:
            print(f"  ✗ Failed to extract details")
            # Keep original job data even if enrichment fails
            enriched_jobs.append({
                'url': job['url'],
                'error': 'Failed to extract details',
                **job
            })
        
        # Delay between requests
        if i < len(job_urls):
            time.sleep(1.5)
    
    return enriched_jobs


@app.route('/')
def index():
    """Render the main page."""
    return render_template('job_search.html')


@app.route('/search', methods=['POST'])
def search():
    """Handle job search request."""
    try:
        data = request.json
        keyword = data.get('keyword', '').strip()
        site = data.get('site', '').strip()
        max_results = int(data.get('max_results', 20))
        
        if not keyword or not site:
            return jsonify({'error': 'Please provide both keyword and site'}), 400
        
        if not API_KEY or not CX:
            return jsonify({'error': 'API credentials not configured'}), 500
        
        # Step 1: Search for jobs
        query = f'site:{site} "{keyword}" "remote"'
        print(f"\n🔍 Searching: {query}")
        job_urls = search_jobs(query, max_results)
        
        if not job_urls:
            return jsonify({'error': 'No jobs found', 'jobs': []}), 404
        
        print(f"✅ Found {len(job_urls)} job URLs")
        
        # Step 2: Enrich jobs with details
        print(f"\n📄 Enriching {len(job_urls)} jobs...")
        enriched_jobs = enrich_jobs(job_urls)
        
        print(f"\n✅ Successfully enriched {len(enriched_jobs)} jobs")
        
        # Step 3: Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enriched_jobs_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(enriched_jobs, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved to: {filename}")
        
        return jsonify({
            'success': True,
            'count': len(enriched_jobs),
            'jobs': enriched_jobs,
            'filename': filename
        })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Check for API credentials
    if not API_KEY or not CX:
        print("\n❌ Error: API credentials not found!")
        print("Please set GOOGLE_API_KEY and GOOGLE_CX in your .env file\n")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("🤖 AI Job Search & Enricher - Web UI")
    print("="*70)
    print(f"\n✅ API credentials loaded")
    print(f"\n🌐 Starting server at http://localhost:5000")
    print(f"   Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
