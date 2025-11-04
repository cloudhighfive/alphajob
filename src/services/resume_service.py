"""
Resume management service for loading, tailoring, and saving resumes.
"""

from typing import Dict, Tuple, Optional, List
from pathlib import Path
from docx import Document
import copy
import re

from src.config.settings import Settings
from src.services.ai_service import AIService
from src.utils.logger import get_logger
from legacy_scripts.tailor_docx_resume import extract_resume_content, update_resume_sections

logger = get_logger(__name__)


class ResumeService:
    """Handle resume loading, tailoring, and saving operations."""
    
    def __init__(self, settings: Settings, ai_service: AIService):
        """
        Initialize resume service.
        
        Args:
            settings: Application settings
            ai_service: AI service for resume tailoring
        """
        self.settings = settings
        self.ai_service = ai_service
        self.resumes_dir = Path("resumes")
        self.original_resume_dir = self.resumes_dir / "original"
        self.tailored_resume_dir = self.resumes_dir / "tailored"
        
        # Ensure directories exist
        self.tailored_resume_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Resume service initialized")
    
    def load_original_resume(self) -> Tuple[str, Optional[Document]]:
        """
        Load the original resume from file.
        
        Returns:
            Tuple of (resume_text, document_object or None)
            - If DOCX: (text_content, Document object)
            - If TXT: (text_content, None)
        """
        resume_path = self.settings.user_info.files.original_resume_path
        try:
            if resume_path.endswith('.docx'):
                doc = Document(resume_path)
                text = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
                logger.info(f"Loaded DOCX resume: {resume_path}")
                return text, doc
            else:
                with open(resume_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                logger.info(f"Loaded TXT resume: {resume_path}")
                return text, None
        except FileNotFoundError:
            logger.error(f"❌ Resume file not found: {resume_path}")
            raise
    
    def tailor_resume(
        self,
        original_resume_text: str,
        job_description: str,
        job_title: str,
        company: str,
        original_doc: Optional[Document] = None
    ):
        """
        Use AI to tailor resume for specific job.
        
        Args:
            original_resume_text: Original resume content
            job_description: Full job description
            job_title: Job title
            company: Company name
            original_doc: Optional Document object for section-based tailoring
            
        Returns:
            Tailored resume (Document object if DOCX, string if TXT)
        """
        logger.info("="*70)
        logger.info("🤖 AI is tailoring your resume...")
        logger.info("="*70)
        
        # If we have a Document object, do section-by-section tailoring
        if original_doc:
            return self._tailor_docx_resume(original_doc, job_description, job_title, company)
        
        # Otherwise, do full text tailoring (legacy)
        return self._tailor_text_resume(original_resume_text, job_description, job_title, company)
    
    def _tailor_text_resume(
        self,
        resume_text: str,
        job_description: str,
        job_title: str,
        company: str
    ) -> str:
        """Tailor plain text resume."""
        prompt = f"""You are a professional resume writer. Rewrite the following resume to perfectly match this job posting.

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description[:2000]}

ORIGINAL RESUME:
{resume_text}

Instructions:
1. Keep all factual information accurate (don't make up experience)
2. Emphasize skills and experiences that match the job requirements
3. Use keywords from the job description
4. Make it ATS-friendly
5. Keep it concise and professional
6. Format as plain text

Provide ONLY the tailored resume text, no additional commentary."""

        try:
            tailored_resume = self.ai_service.generate_text(prompt)
            logger.info(f"✅ Resume tailored successfully ({len(tailored_resume)} characters)")
            return tailored_resume
        except Exception as e:
            logger.error(f"❌ Error tailoring resume: {e}")
            logger.warning("   Using original resume as fallback")
            return resume_text
    
    def _tailor_docx_resume(
        self,
        doc: Document,
        job_description: str,
        job_title: str,
        company: str
    ) -> Document:
        """
        Tailor DOCX resume by updating specific sections while preserving formatting.
        
        Args:
            doc: Original Document object
            job_description: Full job description
            job_title: Job title
            company: Company name
            
        Returns:
            Document object with tailored content
        """
        logger.info("🔍 Extracting resume sections...")
        content = extract_resume_content(doc)
        
        # Tailor Summary section
        tailored_summary = ""
        if content['summary']['paras']:
            logger.info("\n📝 Tailoring SUMMARY section...")
            original_summary = '\n'.join([p['text'] for p in content['summary']['paras']])
            tailored_summary = self.ai_service.tailor_resume_summary(
                original_summary,
                job_description,
                job_title,
                company
            )
            logger.info("   ✅ Summary updated")
        
        # Tailor Skills section
        tailored_skills = ""
        if content['skills']['paras']:
            logger.info("\n🛠️  Tailoring TECHNICAL SKILLS section...")
            original_skills = '\n'.join([p['text'] for p in content['skills']['paras']])
            tailored_skills = self.ai_service.tailor_skills_section(
                original_skills,
                job_description,
                job_title,
                company
            )
            logger.info("   ✅ Skills updated")
        
        # Tailor Experience section (each job)
        tailored_jobs = []
        if content['experience_jobs']:
            logger.info(f"\n💼 Tailoring WORK EXPERIENCE ({len(content['experience_jobs'])} jobs)...")
            for idx, job in enumerate(content['experience_jobs'], 1):
                logger.info(f"\n   Job {idx}/{len(content['experience_jobs'])}: {job.get('company', 'Unknown')}")
                original_bullets = [p['text'] for p in job['paras']]
                tailored_bullets = self.ai_service.tailor_work_experience(
                    {
                        'company': job['company'],
                        'title': job['title'],
                        'dates': job['dates'],
                        'bullets': original_bullets
                    },
                    job_description,
                    job_title,
                    company
                )
                tailored_jobs.append({'bullets': tailored_bullets})
                logger.info(f"      ✅ Updated {len(tailored_bullets)} bullet points")
        
        # Update the document
        logger.info(f"\n📝 Applying changes to document...")
        doc = update_resume_sections(doc, content, tailored_summary, tailored_skills, tailored_jobs)
        
        # Validate and enhance resume
        logger.info(f"\n🔍 Validating tailored resume...")
        doc = self._validate_and_enhance_resume(
            doc, content, tailored_summary, tailored_skills,
            tailored_jobs, job_description, job_title, company
        )
        
        logger.info(f"\n✅ Resume tailoring complete!")
        return doc
    
    def _validate_and_enhance_resume(
        self,
        doc: Document,
        content: Dict,
        tailored_summary: str,
        tailored_skills: str,
        tailored_jobs: List[Dict],
        job_description: str,
        job_title: str,
        company: str
    ) -> Document:
        """
        Validate tailored resume and enhance if sections are missing or incomplete.
        """
        issues_found = []
        
        # Check Summary section
        if not tailored_summary or len(tailored_summary.strip()) < 50:
            issues_found.append("Summary too short or missing")
            logger.warning("   ⚠️  Summary section incomplete")
        
        # Check Skills section
        if not tailored_skills or len(tailored_skills.strip()) < 20:
            issues_found.append("Skills section incomplete")
            logger.warning("   ⚠️  Skills section incomplete")
        else:
            # Check if all 4 categories are present
            required_categories = ['Programming & Frameworks:', 'Data & AI/ML Tools:', 
                                   'Cloud & DevOps:', 'Databases & APIs:']
            missing_categories = [cat for cat in required_categories if cat not in tailored_skills]
            if missing_categories:
                issues_found.append(f"Missing skill categories: {missing_categories}")
                logger.warning(f"   ⚠️  Missing categories: {', '.join(missing_categories)}")
        
        # Check Experience section
        if not tailored_jobs or len(tailored_jobs) == 0:
            issues_found.append("Experience section missing")
            logger.warning("   ⚠️  Experience section incomplete")
        else:
            for idx, job in enumerate(tailored_jobs, 1):
                if not job.get('bullets') or len(job.get('bullets', [])) == 0:
                    issues_found.append(f"Job {idx} has no bullets")
                    logger.warning(f"   ⚠️  Job {idx} missing bullet points")
        
        # If issues found, attempt to re-enhance
        if issues_found:
            logger.info(f"\n🔧 Enhancing incomplete sections...")
            
            # Re-enhance summary if needed
            if any('Summary' in issue for issue in issues_found):
                logger.info("   🔄 Re-generating summary...")
                original_summary = '\n'.join([p['text'] for p in content['summary']['paras']])
                tailored_summary = self.ai_service.tailor_resume_summary(
                    original_summary, job_description, job_title, company
                )
                content_updated = extract_resume_content(doc)
                doc = update_resume_sections(doc, content_updated, tailored_summary, tailored_skills, tailored_jobs)
            
            # Re-enhance skills if needed
            if any('Skills' in issue or 'categories' in issue for issue in issues_found):
                logger.info("   🔄 Re-generating skills...")
                original_skills = '\n'.join([p['text'] for p in content['skills']['paras']])
                tailored_skills = self.ai_service.tailor_skills_section(
                    original_skills, job_description, job_title, company
                )
                content_updated = extract_resume_content(doc)
                doc = update_resume_sections(doc, content_updated, tailored_summary, tailored_skills, tailored_jobs)
            
            logger.info("   ✅ Enhancement complete")
        else:
            logger.info("   ✅ All sections validated successfully")
        
        return doc
    
    def save_tailored_resume(
        self,
        company: str,
        job_title: str,
        tailored_content,
        original_doc: Optional[Document] = None
    ) -> str:
        """
        Save tailored resume to file in organized directory structure.
        Structure: tailored/{company}_{job_title}/{original_resume_name}.docx
        
        Args:
            company: Company name
            job_title: Job title
            tailored_content: Tailored resume (Document object or text string)
            original_doc: Original Document object (for text-based tailoring)
            
        Returns:
            Path to saved resume file
        """
        # Create safe folder name from company and job title
        safe_company = re.sub(r'[^\w\s-]', '', company).strip().replace(' ', '_')
        safe_title = re.sub(r'[^\w\s-]', '', job_title).strip().replace(' ', '_')
        folder_name = f"{safe_company}_{safe_title}"
        
        # Create company/job folder inside tailored directory
        job_folder = self.tailored_resume_dir / folder_name
        job_folder.mkdir(parents=True, exist_ok=True)
        
        # Get original resume filename (without path)
        original_resume_path = Path(self.settings.user_info.files.original_resume_path)
        original_filename = original_resume_path.name
        
        # Check if it's a Document object
        if hasattr(tailored_content, 'save') and hasattr(tailored_content, 'paragraphs'):
            # Save as DOCX using original filename
            filepath = job_folder / original_filename
            tailored_content.save(str(filepath))
        else:
            # Text content
            if original_doc:
                # Save as DOCX (legacy simple approach)
                filepath = job_folder / original_filename
                
                new_doc = copy.deepcopy(original_doc)
                resume_lines = tailored_content.split('\n')
                
                # Clear and rebuild
                while len(new_doc.paragraphs) > 0:
                    p = new_doc.paragraphs[0]
                    p._element.getparent().remove(p._element)
                
                for line in resume_lines:
                    if line.strip():
                        new_doc.add_paragraph(line)
                
                new_doc.save(str(filepath))
            else:
                # Save as TXT using original filename
                txt_filename = original_filename.replace('.docx', '.txt')
                filepath = job_folder / txt_filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(tailored_content)
        
        logger.info(f"💾 Saved tailored resume: {filepath}")
        return str(filepath)
