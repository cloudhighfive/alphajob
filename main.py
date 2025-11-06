"""
Main entry point for the job application system with web UI.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template_string, request, jsonify
import threading

from src.config.settings import Settings
from src.services.job_application_service import JobApplicationService
from src.services.ai_service import AIService
from src.services.resume_service import ResumeService
from src.utils.logger import setup_logging, get_logger

# Add legacy scripts to path
sys.path.insert(0, str(Path(__file__).parent / "legacy_scripts"))
from scrape_job_details import extract_job_details
from tailor_docx_resume import extract_resume_content, update_resume_sections

# Import for resume tailoring
from docx import Document

# Load environment variables
load_dotenv()

# Initialize logging
setup_logging(level="INFO")
logger = get_logger(__name__)

# Get API credentials for job search
API_KEY = os.getenv('GOOGLE_API_KEY')
CX = os.getenv('GOOGLE_CX')

# Flask app
app = Flask(__name__)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🤖 AI Job Search & Auto-Apply</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 { color: #667eea; font-size: 28px; margin-bottom: 5px; }
        .subtitle { color: #666; font-size: 14px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h2 { color: #333; font-size: 20px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: 600; margin-bottom: 8px; color: #333; font-size: 14px; }
        input[type="text"], input[type="number"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        input:focus { outline: none; border-color: #667eea; }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .results {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            max-height: 600px;
            overflow-y: auto;
        }
        .job-card {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 12px;
        }
        .job-card:hover { border-color: #667eea; }
        .job-title { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 5px; }
        .job-company { color: #667eea; font-size: 14px; margin-bottom: 8px; }
        .job-meta { font-size: 13px; color: #666; }
        .status { padding: 15px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; }
        .status.loading { background: #fff3cd; color: #856404; }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; display: inline-block; margin-right: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Job Search & Auto-Apply System</h1>
            <p class="subtitle">Search for remote jobs and apply automatically</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>🔍 Search & Enrich Jobs</h2>
                <form id="searchForm">
                    <div class="form-group">
                        <label>Search Keyword</label>
                        <input type="text" id="keyword" value="senior software engineer" required>
                    </div>
                    <div class="form-group">
                        <label>Location</label>
                        <input type="text" id="location" value="United States" required>
                    </div>
                    <div class="form-group">
                        <label>Job Site</label>
                        <input type="text" id="site" value="jobs.ashbyhq.com" required>
                    </div>
                    <div class="form-group">
                        <label>Max Results</label>
                        <input type="number" id="maxResults" value="20" min="5" max="50" required>
                    </div>
                    <button type="submit">🔍 Search Jobs</button>
                </form>
            </div>
            
            <div class="card">
                <h2>📋 Job Actions</h2>
                <form id="jobForm">
                    <div class="form-group">
                        <label>AI Model</label>
                        <select id="aiModel" style="width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px;">
                            <option value="llama3.1">llama3.1 - Best overall (Recommended)</option>
                            <option value="deepseek-r1">deepseek-r1 - Slower but more thoughtful</option>
                            <option value="codellama">codellama - Good for technical content</option>
                            <option value="mistral">mistral - Fast and concise</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Job URL</label>
                        <input type="text" id="jobUrl" value="https://jobs.ashbyhq.com/rillet/f5d21c85-4fd2-461b-b5aa-3ece7d9f6bac" placeholder="https://jobs.ashbyhq.com/..." required>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <button type="button" id="buildResumeBtn">📝 Build Resume</button>
                        <button type="button" id="applyBtn">📤 Apply</button>
                    </div>
                </form>
            </div>
        </div>
        
        <div id="status"></div>
        <div id="results"></div>
    </div>
    
    <script>
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const keyword = document.getElementById('keyword').value;
            const location = document.getElementById('location').value;
            const site = document.getElementById('site').value;
            const maxResults = document.getElementById('maxResults').value;
            
            document.getElementById('status').innerHTML = 
                '<div class="status loading"><div class="spinner"></div>Searching and enriching jobs... This may take a few minutes.</div>';
            document.getElementById('results').innerHTML = '';
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keyword, location, site, max_results: parseInt(maxResults) })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('status').innerHTML = 
                        `<div class="status success">✅ Found ${data.count} jobs! Saved to: ${data.filename}</div>`;
                    displayJobs(data.jobs);
                } else {
                    document.getElementById('status').innerHTML = 
                        `<div class="status error">❌ Error: ${data.error}</div>`;
                }
            } catch (error) {
                document.getElementById('status').innerHTML = 
                    `<div class="status error">❌ Error: ${error.message}</div>`;
            }
        });
        
        document.getElementById('buildResumeBtn').addEventListener('click', async () => {
            const jobUrl = document.getElementById('jobUrl').value;
            const aiModel = document.getElementById('aiModel').value;
            if (!jobUrl) {
                alert('Please enter a job URL');
                return;
            }
            
            document.getElementById('status').innerHTML = 
                `<div class="status loading"><div class="spinner"></div>Building tailored resume with ${aiModel}... This may take a minute.</div>`;
            
            try {
                const response = await fetch('/build_resume', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ job_url: jobUrl, ai_model: aiModel })
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    let timingHtml = '';
                    if (data.timing) {
                        timingHtml = `<br><br>⏱️ <strong>Timing Breakdown:</strong>
                            <br>• Summary: ${data.timing.summary}s
                            <br>• Skills: ${data.timing.skills}s
                            <br>• Experience: ${data.timing.experience}s
                            <br>• Document update: ${data.timing.document_update}s
                            <br>• Total: ${data.total_time}s (${(data.total_time/60).toFixed(2)} minutes)`;
                    }
                    document.getElementById('status').innerHTML = 
                        `<div class="status success">✅ Resume built successfully in ${data.total_time}s using ${aiModel}!<br>📄 Saved to: ${data.resume_path}${timingHtml}</div>`;
                } else {
                    document.getElementById('status').innerHTML = 
                        `<div class="status error">❌ ${data.error || 'Resume building failed'}</div>`;
                }
            } catch (error) {
                document.getElementById('status').innerHTML = 
                    `<div class="status error">❌ Error: ${error.message}</div>`;
            }
        });
        
        document.getElementById('applyBtn').addEventListener('click', async () => {
            const jobUrl = document.getElementById('jobUrl').value;
            const aiModel = document.getElementById('aiModel').value;
            if (!jobUrl) {
                alert('Please enter a job URL');
                return;
            }
            
            document.getElementById('status').innerHTML = 
                `<div class="status loading"><div class="spinner"></div>Applying to job with ${aiModel}... This may take a few minutes.</div>`;
            
            try {
                const response = await fetch('/apply', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ job_url: jobUrl, ai_model: aiModel })
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    document.getElementById('status').innerHTML = 
                        '<div class="status success">✅ Application submitted successfully!</div>';
                } else {
                    document.getElementById('status').innerHTML = 
                        `<div class="status error">❌ ${data.message || 'Application failed'}</div>`;
                }
            } catch (error) {
                document.getElementById('status').innerHTML = 
                    `<div class="status error">❌ Error: ${error.message}</div>`;
            }
        });
        
        function displayJobs(jobs) {
            let html = '<div class="results"><h2>📊 Search Results</h2>';
            jobs.forEach((job, i) => {
                html += `
                    <div class="job-card">
                        <div class="job-title">${job.job_title || 'Unknown'}</div>
                        <div class="job-company">🏢 ${job.company || 'Unknown'}</div>
                        <div class="job-meta">
                            📍 ${job.location || 'N/A'} | 💼 ${job.job_type || 'N/A'} | 💰 ${job.salary || 'N/A'}
                        </div>
                        <div style="margin-top: 8px; display: flex; gap: 10px; align-items: center;">
                            <a href="${job.url}" target="_blank" style="color: #667eea; text-decoration: none;">🔗 View Job</a>
                            <button onclick="buildResumeForJob('${job.url}')" style="width: auto; padding: 6px 15px; font-size: 13px;">
                                📄 Build Resume
                            </button>
                            <button onclick="applyToJob('${job.url}')" style="width: auto; padding: 6px 15px; font-size: 13px;">
                                📤 Apply
                            </button>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            document.getElementById('results').innerHTML = html;
        }
        
        function buildResumeForJob(url) {
            document.getElementById('jobUrl').value = url;
            document.getElementById('buildResumeBtn').click();
        }
        
        function applyToJob(url) {
            document.getElementById('jobUrl').value = url;
            document.getElementById('applyBtn').click();
        }
    </script>
</body>
</html>
'''


def search_jobs(query, max_results=20):
    """Search Google for job URLs."""
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
        except Exception as e:
            logger.error(f"Search error: {e}")
            break
    
    return all_urls


def enrich_jobs(job_urls):
    """Extract detailed information for each job URL."""
    enriched_jobs = []
    
    for i, job in enumerate(job_urls, 1):
        logger.info(f"[{i}/{len(job_urls)}] Extracting: {job['url']}")
        
        details = extract_job_details(job['url'])
        
        if details:
            enriched_jobs.append({
                'url': job['url'],
                'company': details['company'],
                'job_title': details['title'],
                'location': details['location'],
                'job_type': details['job_type'],
                'employment_type': details['employment_type'],
                'salary': details['salary'],
                'date_posted': details['date_posted'],
                'description': details['description']
            })
        else:
            enriched_jobs.append({
                'url': job['url'],
                'error': 'Failed to extract',
                **job
            })
        
        if i < len(job_urls):
            time.sleep(1.5)
    
    return enriched_jobs


@app.route('/')
def index():
    """Render the main page."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/search', methods=['POST'])
def search():
    """Handle job search request."""
    try:
        data = request.json
        keyword = data.get('keyword', '').strip()
        location = data.get('location', 'United States').strip()
        site = data.get('site', '').strip()
        max_results = int(data.get('max_results', 20))
        
        if not keyword or not site:
            return jsonify({'error': 'Missing keyword or site'}), 400
        
        if not API_KEY or not CX:
            return jsonify({'error': 'API credentials not configured'}), 500
        
        # Search with location
        query = f'site:{site} "{keyword}" "{location}" "remote"'
        logger.info(f"Searching: {query}")
        job_urls = search_jobs(query, max_results)
        
        if not job_urls:
            return jsonify({'error': 'No jobs found', 'jobs': []}), 404
        
        logger.info(f"Found {len(job_urls)} URLs, enriching...")
        
        # Enrich
        enriched_jobs = enrich_jobs(job_urls)
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enriched_jobs_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(enriched_jobs, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved to: {filename}")
        
        return jsonify({
            'success': True,
            'count': len(enriched_jobs),
            'jobs': enriched_jobs,
            'filename': filename
        })
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/apply', methods=['POST'])
def apply_job():
    """Handle job application request."""
    try:
        data = request.json
        job_url = data.get('job_url', '').strip()
        ai_model = data.get('ai_model', 'llama3.1')  # Get model from request, default to llama3.1
        
        if not job_url:
            return jsonify({'error': 'Job URL required'}), 400
        
        logger.info(f"Applying to: {job_url}")
        logger.info(f"Using AI model: {ai_model}")
        
        # Extract job details to find matching tailored resume
        job_details = extract_job_details(job_url)
        tailored_resume_path = None
        
        if job_details:
            company = job_details.get('company', 'Unknown')
            job_title = job_details.get('title', 'Unknown')
            
            # Look for matching tailored resume
            safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
            safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
            
            resume_dir = Path(f"resumes/tailored/{safe_company}_{safe_title}")
            if resume_dir.exists():
                # Look for any .docx file (will use original filename)
                resume_files = list(resume_dir.glob("*.docx"))
                if resume_files:
                    tailored_resume_path = str(resume_files[0])
                    logger.info(f"✅ Found tailored resume: {tailored_resume_path}")
                else:
                    logger.warning(f"⚠️  No tailored resume found in {resume_dir}, will use original")
            else:
                logger.warning(f"⚠️  No tailored resume directory found, will use original")
        
        # Load settings and apply
        settings = Settings.from_json("config.json")
        
        # If tailored resume exists, temporarily update settings to use it
        if tailored_resume_path:
            # Copy settings and update resume path
            import copy
            settings_dict = json.loads(settings.to_json())
            settings_dict['resume']['path'] = tailored_resume_path
            
            # Save temp config
            with open('.temp_config.json', 'w') as f:
                json.dump(settings_dict, f, indent=2)
            
            settings = Settings.from_json('.temp_config.json')
            logger.info(f"📄 Using tailored resume for application")
        
        # Override AI model in settings
        settings.ai_settings.model = ai_model
        
        job_service = JobApplicationService(settings, headless=False)
        
        # Run in background thread to avoid blocking
        def apply_in_background():
            result = job_service.apply_to_job(job_url)
            logger.info(f"Application result: {result}")
            # Clean up temp config
            if tailored_resume_path and Path('.temp_config.json').exists():
                Path('.temp_config.json').unlink()
        
        thread = threading.Thread(target=apply_in_background, daemon=True)
        thread.start()
        
        message = 'Application started! Check browser window.'
        if tailored_resume_path:
            message += f' Using tailored resume: {Path(tailored_resume_path).name}'
        
        return jsonify({
            'success': True,
            'message': message
        })
    
    except Exception as e:
        logger.error(f"Apply error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/build_resume', methods=['POST'])
def build_resume():
    """Handle resume building request using template-based generation."""
    import time
    start_time = time.time()
    
    try:
        data = request.json
        job_url = data.get('job_url', '').strip()
        ai_model = data.get('ai_model', 'llama3.1')
        
        if not job_url:
            return jsonify({'error': 'Job URL required'}), 400
        
        logger.info("\n" + "="*70)
        logger.info("⏱️  RESUME GENERATION STARTED (TEMPLATE-BASED)")
        logger.info("="*70)
        logger.info(f"🔗 Job URL: {job_url}")
        logger.info(f"🤖 AI Model: {ai_model}")
        logger.info(f"🕐 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)
        
        # Extract job details
        step_start = time.time()
        logger.info("\n📡 Extracting job details...")
        job_details = extract_job_details(job_url)
        if not job_details:
            return jsonify({'error': 'Failed to extract job details'}), 500
        
        company = job_details.get('company', 'Unknown')
        job_title = job_details.get('title', 'Unknown')
        description = job_details.get('description', '')
        
        if not description:
            return jsonify({'error': 'No job description found'}), 500
        
        logger.info(f"✅ Job details extracted in {time.time() - step_start:.2f}s")
        logger.info(f"   Company: {company}")
        logger.info(f"   Title: {job_title}")
        
        # Extract detailed info from job description using AI
        step_start = time.time()
        logger.info("\n🤖 Initializing AI service...")
        settings = Settings.from_json("config.json")
        settings.ai_settings.model = ai_model
        ai_service = AIService(settings)
        logger.info(f"✅ AI service ready in {time.time() - step_start:.2f}s")

        # Prompt AI for detailed extraction
        detail_prompt = f"""
Analyze the following job description and extract the following details:
- Required skills (list)
- Programming languages (list)
- Tools (list)
- Frameworks (list)
- Main responsibilities (list)
- What kind of role is this (e.g. backend, frontend, full stack, ML, DevOps, etc)
- Any other important requirements or signals

Job Description:
{description}

Output in clear sections, each starting with a label (e.g. 'Required Skills:', 'Programming Languages:', etc). No commentary, no formatting, just the extracted info.
"""
        logger.info("\n🤖 Sending job description to AI for detailed extraction...")
        ai_response = ai_service.generate_completion(detail_prompt)
        logger.info("\n🧠 AI Response (Detailed Extraction):\n" + ai_response.strip())

        return jsonify({
            'success': True,
            'details': ai_response.strip(),
            'company': company,
            'job_title': job_title
        })
    
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Resume generation error after {total_time:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


def main():
    """
    Main application entry point with web UI.
    """
    # Default job URL
    default_job_url = "https://jobs.ashbyhq.com/rillet/f5d21c85-4fd2-461b-b5aa-3ece7d9f6bac"

    print("\n" + "="*70)
    print("🤖 AI JOB SEARCH & AUTO-APPLY - WEB UI")
    print("="*70)
    print(f"\n🔗 Extracting job info from default URL:")
    print(f"   {default_job_url}\n")

    # Extract job details and log them
    from legacy_scripts.scrape_job_details import extract_job_details
    job_details = extract_job_details(default_job_url)
    if job_details:
        print(f"Company: {job_details.get('company', 'Unknown')}")
        print(f"Title: {job_details.get('title', 'Unknown')}")
        print(f"Location: {job_details.get('location', 'Unknown')}")
        print(f"Type: {job_details.get('job_type', 'Unknown')}")
        print(f"Description: {job_details.get('description', '')[:300]}...\n")
    else:
        print("❌ Failed to extract job details from default URL.\n")

    print(f"🌐 Opening web UI at http://localhost:5001")
    print(f"   Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)


if __name__ == "__main__":
    # Print all content of template resume
    from docx import Document
    resume_path = "resumes/original/Resume.docx"
    if os.path.exists(resume_path):
        doc = Document(resume_path)
        print("\n===== FULL CONTENT OF TEMPLATE RESUME =====")
        for para in doc.paragraphs:
            print(para.text)
        print("==========================================\n")
    else:
        print(f"Resume template not found at {resume_path}")

    # Fetch and print required personal info from config.json
    import json
    with open("config.json", "r") as f:
        config = json.load(f)
    personal_info = config.get("user_info", {}).get("resume_personal_info", {})
    print("\n===== PERSONAL INFO FROM CONFIG =====")
    for key in ["full_name", "location", "phone", "email", "linkedin", "github"]:
        print(f"{key}: {personal_info.get(key, '')}")
    print("====================================\n")
    main()
