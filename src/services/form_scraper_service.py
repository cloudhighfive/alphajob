"""
Job application form scraping service.
"""

from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
import json

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FormScraperService:
    """Scrape job application forms from job posting URLs."""
    
    def __init__(self):
        """Initialize form scraper service."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        logger.info("Form scraper service initialized")
    
    def extract_application_form(self, job_url: str) -> Optional[Dict]:
        """
        Extract application form structure from job posting URL.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Dictionary containing form fields and job details
        """
        try:
            logger.info("="*70)
            logger.info(f"Extracting application form from: {job_url}")
            logger.info("="*70)
            
            response = requests.get(job_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract from window.__appData
            script = soup.find('script', string=lambda t: t and 'window.__appData' in t)
            if not script:
                logger.error("❌ Could not find application form data")
                return None
            
            # Parse the JSON (handle extra data at the end)
            content = script.string
            json_start = content.find('{')
            # Find the end of the JSON object by matching braces
            brace_count = 0
            json_end = json_start
            for i in range(json_start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            data = json.loads(content[json_start:json_end])
            
            # Extract job posting details
            posting = data.get('posting', {})
            form_data = posting.get('applicationForm', {})
            
            form_fields = []
            for entry in form_data.get('fieldEntries', []):
                field = entry.get('field', {})
                
                # Extract description
                desc_html = entry.get('descriptionHtml', '')
                description = ""
                if desc_html:
                    desc_soup = BeautifulSoup(desc_html, 'html.parser')
                    description = desc_soup.get_text(strip=True)
                
                # Extract options for select fields
                options = []
                if field.get('type') in ['ValueSelect', 'MultiValueSelect']:
                    select_options = field.get('selectableValues', [])
                    for opt in select_options:
                        if isinstance(opt, dict):
                            options.append(opt.get('label', opt.get('value', '')))
                        else:
                            options.append(str(opt))
                
                form_fields.append({
                    'title': field.get('title'),
                    'path': field.get('path'),
                    'type': field.get('type'),
                    'required': entry.get('isRequired', False),
                    'description': description,
                    'options': options if options else None
                })
            
            result = {
                'job_url': job_url,
                'company': data.get('organization', {}).get('name'),
                'job_title': posting.get('title'),
                'job_description': posting.get('descriptionPlainText', ''),
                'location': posting.get('locationName'),
                'form_fields': form_fields,
                'organization_id': posting.get('organizationId'),
                'posting_id': posting.get('id')
            }
            
            logger.info(f"✅ Found {len(form_fields)} form fields")
            logger.info(f"   Company: {result['company']}")
            logger.info(f"   Position: {result['job_title']}")
            logger.info(f"   Location: {result['location']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error extracting form: {e}")
            return None
