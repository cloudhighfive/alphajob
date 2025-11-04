"""
Job application orchestrator service.

Coordinates all services to process job applications end-to-end.
"""

from typing import Dict, Optional
from datetime import datetime
import json
from pathlib import Path

from src.config.settings import Settings
from src.services.ai_service import AIService
from src.services.resume_service import ResumeService
from src.services.form_scraper_service import FormScraperService
from src.services.browser_service import BrowserService
from src.utils.logger import get_logger
from src.utils.paths import get_application_data_path

logger = get_logger(__name__)


class JobApplicationService:
    """Orchestrate the complete job application workflow."""
    
    def __init__(self, settings: Settings, headless: bool = False):
        """
        Initialize job application service.
        
        Args:
            settings: Application settings
            headless: If True, run browser in headless mode
        """
        self.settings = settings
        
        # Initialize all services
        self.ai_service = AIService(settings)
        self.resume_service = ResumeService(settings, self.ai_service)
        self.form_scraper = FormScraperService()
        self.browser_service = BrowserService(settings, headless=headless)
        
        logger.info("="*70)
        logger.info("🤖 Job Application Service Initialized")
        logger.info("="*70)
        logger.info(f"  Model: {settings.ai_settings.model}")
        logger.info(f"  User: {settings.user_info.personal_info.name}")
        logger.info(f"  Email: {settings.user_info.personal_info.email}")
        logger.info("="*70)
    
    def apply_to_job(self, job_url: str) -> Dict:
        """
        Complete end-to-end job application workflow.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Dict with application result
        """
        logger.info("\n" + "="*70)
        logger.info("🚀 STARTING JOB APPLICATION WORKFLOW")
        logger.info("="*70)
        logger.info(f"Target: {job_url}")
        logger.info(f"User: {self.settings.user_info.personal_info.name}")
        logger.info(f"Email: {self.settings.user_info.personal_info.email}\n")
        
        # Step 1: Extract application form
        logger.info("Step 1/4: Extracting application form...")
        logger.info("   📡 Fetching job posting page...")
        form_data = self.form_scraper.extract_application_form(job_url)
        
        if not form_data:
            logger.error("❌ Failed to extract application form")
            return {
                'success': False,
                'error': 'Could not extract application form'
            }
        
        company = form_data.get('company', 'Unknown Company')
        title = form_data.get('title', 'Unknown Position')
        logger.info(f"   ✅ Found position: {title} at {company}")
        logger.info(f"   ✅ Extracted {len(form_data.get('form_fields', []))} form fields")
        
        # Log field types for visibility
        fields = form_data.get('form_fields', [])
        field_types = {}
        for field in fields:
            field_type = field.get('type', 'unknown')
            field_types[field_type] = field_types.get(field_type, 0) + 1
        logger.info(f"   📋 Field breakdown: {dict(field_types)}")
        
        # Step 2: Fill application with AI assistance
        logger.info("\nStep 2/4: Filling application with AI...")
        logger.info(f"   🤖 Analyzing {len(fields)} form fields...")
        filled_data = self._fill_application_form(form_data)
        logger.info(f"   ✅ Generated responses for all fields")
        
        # Step 3: Submit application with browser automation
        logger.info("\nStep 3/4: Submitting application with browser...")
        logger.info("   🌐 Launching browser with stealth mode...")
        submission_result = self.browser_service.submit_application(
            job_url=job_url,
            filled_data=filled_data['fields'],
            form_fields=form_data['form_fields'],
            resume_path=filled_data.get('tailored_resume_path')
        )
        
        # Step 4: Save application data
        logger.info("\nStep 4/4: Saving application data...")
        filled_data['submission_result'] = submission_result
        self._save_application_data(filled_data)
        
        # Generate preview
        preview = self._generate_application_preview(filled_data)
        logger.info(f"\n{preview}")
        
        # Final summary
        logger.info("\n" + "="*70)
        logger.info("📊 SUBMISSION SUMMARY")
        logger.info("="*70)
        logger.info(f"Status: {submission_result['status'].upper()}")
        logger.info(f"Success: {'✅ Yes' if submission_result['success'] else '❌ No'}")
        logger.info(f"Message: {submission_result['message']}")
        logger.info("\n✅ AI-powered application complete!")
        logger.info("="*70)
        
        return {
            'success': submission_result['success'],
            'status': submission_result['status'],
            'message': submission_result['message'],
            'filled_data': filled_data
        }
    
    def _fill_application_form(self, form_data: Dict) -> Dict:
        """
        Fill application form with AI-generated content.
        
        Args:
            form_data: Form structure from extract_application_form()
            
        Returns:
            Dictionary with filled form data
        """
        logger.info("="*70)
        logger.info("📝 Filling application form with AI assistance...")
        logger.info("="*70)
        
        job_description = form_data['job_description']
        job_title = form_data['job_title']
        company = form_data['company']
        
        # Load original resume
        original_resume_text, original_doc = self.resume_service.load_original_resume()
        
        # Get user config shortcuts
        personal_info = self.settings.user_info.personal_info
        links = self.settings.user_info.links
        work_auth = self.settings.user_info.work_authorization
        demographics = self.settings.user_info.demographics
        background = self.settings.user_info.background
        
        filled_data = {
            'company': company,
            'job_title': job_title,
            'job_url': form_data['job_url'],
            'timestamp': datetime.now().isoformat(),
            'fields': {}
        }
        
        for field in form_data['form_fields']:
            field_title = field['title']
            field_type = field['type']
            field_path = field['path']
            required = field['required']
            
            logger.info(f"   🔹 {field_title} ({field_type}){' *REQUIRED*' if required else ''}")
            
            # Handle specific fields first
            if 'middle' in field_title.lower() and 'name' in field_title.lower():
                filled_data['fields'][field_path] = personal_info.middle_name or ''
                logger.info(f"   ✅ Set to: {filled_data['fields'][field_path]}")
            
            elif 'pronoun' in field_title.lower():
                filled_data['fields'][field_path] = personal_info.pronouns
                logger.info(f"   ✅ Set to: {filled_data['fields'][field_path]}")
            
            elif field_path == '_systemfield_name' or ('name' in field_title.lower() and 'middle' not in field_title.lower()):
                filled_data['fields'][field_path] = personal_info.name
                logger.info(f"   ✅ Set to: {filled_data['fields'][field_path]}")
                
            elif field_path == '_systemfield_email' or 'email' in field_title.lower():
                filled_data['fields'][field_path] = personal_info.email
                logger.info(f"   ✅ Set to: {filled_data['fields'][field_path]}")
                
            elif 'phone' in field_title.lower():
                filled_data['fields'][field_path] = personal_info.phone or ''
                logger.info(f"   ✅ Set to: {filled_data['fields'][field_path]}")
                
            elif field_path == '_systemfield_resume' or 'resume' in field_title.lower():
                # Use original resume path directly (tailoring commented out for speed)
                resume_path = self.settings.user_info.files.original_resume_path
                filled_data['fields'][field_path] = original_resume_text
                filled_data['tailored_resume_path'] = resume_path
                logger.info(f"   ✅ Using original resume: {resume_path}")
                
            elif field_path == '_systemfield_location' or 'location' in field_title.lower():
                filled_data['fields'][field_path] = personal_info.location
                logger.info(f"   ✅ Set to: {filled_data['fields'][field_path]}")
                
            elif 'linkedin' in field_title.lower():
                filled_data['fields'][field_path] = links.linkedin or ''
                logger.info(f"   ✅ Set to: {filled_data['fields'][field_path]}")
                
            elif 'github' in field_title.lower():
                filled_data['fields'][field_path] = links.github or ''
                logger.info(f"   ✅ Set to: {filled_data['fields'][field_path]}")
                
            elif 'website' in field_title.lower() or 'portfolio' in field_title.lower():
                filled_data['fields'][field_path] = links.website or ''
                logger.info(f"   ✅ Set to: {filled_data['fields'][field_path]}")
            
            elif 'state' in field_title.lower() and 'residency' in field_title.lower():
                # Use state from config for residency questions
                filled_data['fields'][field_path] = personal_info.state
                logger.info(f"   ✅ Set to: {filled_data['fields'][field_path]}")
                
            elif field_type == 'Boolean':
                # For yes/no questions, use config values
                if 'authorized' in field_title.lower() and 'united states' in field_title.lower():
                    filled_data['fields'][field_path] = work_auth.authorized_to_work_us
                    logger.info(f"   ✅ Set to: {'Yes' if work_auth.authorized_to_work_us else 'No'}")
                elif 'authorized' in field_title.lower() and 'canada' in field_title.lower():
                    filled_data['fields'][field_path] = work_auth.authorized_to_work_canada
                    logger.info(f"   ✅ Set to: {'Yes' if work_auth.authorized_to_work_canada else 'No'}")
                elif 'visa' in field_title.lower() or 'sponsorship' in field_title.lower():
                    filled_data['fields'][field_path] = work_auth.needs_visa_sponsorship
                    logger.info(f"   ✅ Set to: {'Yes' if work_auth.needs_visa_sponsorship else 'No'}")
                else:
                    filled_data['fields'][field_path] = True
                    logger.info(f"   ✅ Set to: Yes")
                    
            elif field_type in ['LongText', 'String']:
                # Use AI to answer custom questions
                question = f"{field_title}: {field['description']}" if field['description'] else field_title
                
                answer = self.ai_service.answer_question(
                    question,
                    job_description,
                    job_title,
                    company,
                    background.elevator_pitch
                )
                filled_data['fields'][field_path] = answer
            
            elif field_type in ['ValueSelect', 'MultiValueSelect']:
                options = field.get('options', [])
                
                # Handle specific demographics fields
                if 'pronoun' in field_title.lower():
                    pronoun_input = personal_info.pronouns
                    pronoun_mapping = {
                        'he/him/his': 'He/him/his',
                        'she/her/hers': 'She/her/hers',
                        'they/them/theirs': 'They/them/theirs'
                    }
                    pronoun_value = pronoun_mapping.get(pronoun_input.lower(), pronoun_input)
                    
                    if options:
                        for opt in options:
                            if pronoun_input.lower() in opt.lower() or opt.lower() in pronoun_input.lower():
                                pronoun_value = opt
                                break
                    
                    filled_data['fields'][field_path] = pronoun_value
                    logger.info(f"   ✅ Selected: {pronoun_value}")
                    
                elif 'gender' in field_title.lower():
                    gender_value = demographics.gender
                    
                    if options:
                        for opt in options:
                            if gender_value.lower() in opt.lower() or opt.lower() in gender_value.lower():
                                gender_value = opt
                                break
                    
                    filled_data['fields'][field_path] = gender_value
                    logger.info(f"   ✅ Selected: {gender_value}")
                    
                elif 'race' in field_title.lower():
                    filled_data['fields'][field_path] = demographics.race
                    logger.info(f"   ✅ Selected: {demographics.race}")
                    
                elif 'veteran' in field_title.lower():
                    filled_data['fields'][field_path] = demographics.veteran_status
                    logger.info(f"   ✅ Selected: {demographics.veteran_status}")
                    
                elif 'disability' in field_title.lower():
                    filled_data['fields'][field_path] = demographics.disability_status
                    logger.info(f"   ✅ Selected: {demographics.disability_status}")
                    
                else:
                    # Use AI to select best option
                    if field['description']:
                        question = f"{field_title}: {field['description']}"
                    else:
                        question = field_title
                    
                    multi_select = field_type == 'MultiValueSelect'
                    selected = self.ai_service.select_best_option(
                        question,
                        options,
                        job_description,
                        job_title,
                        company,
                        multi_select=multi_select
                    )
                    filled_data['fields'][field_path] = selected
                    if multi_select:
                        logger.info(f"   ✅ Selected: {', '.join(selected)}")
                    else:
                        logger.info(f"   ✅ Selected: {selected}")
        
        return filled_data
    
    def _save_application_data(self, filled_data: Dict):
        """Save filled application data to JSON file."""
        output_path = get_application_data_path()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filled_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"   💾 Application saved to: {output_path}")
    
    def _generate_application_preview(self, filled_data: Dict) -> str:
        """Generate human-readable preview of application."""
        lines = []
        lines.append("\n" + "="*70)
        lines.append("📋 APPLICATION PREVIEW")
        lines.append("="*70)
        
        lines.append(f"\n🏢 Company: {filled_data['company']}")
        lines.append(f"💼 Position: {filled_data['job_title']}")
        lines.append(f"🔗 URL: {filled_data['job_url']}")
        lines.append(f"📅 Timestamp: {filled_data['timestamp']}")
        
        if filled_data.get('tailored_resume_path'):
            lines.append(f"\n📄 Resume: {filled_data['tailored_resume_path']}")
        
        lines.append(f"\n📝 Form Fields ({len(filled_data['fields'])}):")
        for path, value in filled_data['fields'].items():
            if path == '_systemfield_resume':
                lines.append(f"  • {path}: [Resume content - {len(str(value))} chars]")
            elif isinstance(value, list):
                lines.append(f"  • {path}: {', '.join(value)}")
            else:
                value_str = str(value)
                if len(value_str) > 100:
                    lines.append(f"  • {path}: {value_str[:100]}...")
                else:
                    lines.append(f"  • {path}: {value_str}")
        
        lines.append("="*70)
        return '\n'.join(lines)
