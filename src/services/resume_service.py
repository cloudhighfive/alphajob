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
                
                job_info = {
                    'company': job.get('company', ''),
                    'title': job.get('title', ''),
                    'dates': job.get('dates', ''),
                    'bullets': original_bullets
                }
                
                tailored_bullets = self.ai_service.tailor_work_experience(
                    job_info,
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
    
    def generate_resume_from_template(
        self,
        job_description: str,
        job_title: str,
        company: str
    ) -> str:
        """
        Generate a complete resume from template by analyzing job description.
        
        Args:
            job_description: Job description text
            job_title: Job title
            company: Company name
            
        Returns:
            Path to generated resume file
        """
        logger.info(f"\n🎯 Generating resume from template for {job_title} at {company}")
        
        # Load template
        template_path = self.original_resume_dir / "Resume.docx"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        doc = Document(str(template_path))
        
        # Get personal info from config (build from user_info if resume_personal_info not set)
        if self.settings.user_info.resume_personal_info:
            personal_info = self.settings.user_info.resume_personal_info.model_dump()
        else:
            # Build from existing user_info
            personal_info = {
                'full_name': self.settings.user_info.personal_info.name,
                'location': f"{self.settings.user_info.personal_info.city}, {self.settings.user_info.personal_info.state_abbr}",
                'phone': self.settings.user_info.personal_info.phone,
                'email': self.settings.user_info.personal_info.email,
                'linkedin': self.settings.user_info.links.linkedin.replace('https://www.linkedin.com/in/', ''),
                'github': self.settings.user_info.links.github.replace('https://github.com/', ''),
                'title': self.settings.user_info.background.current_title,
                'years_experience': self.settings.user_info.background.years_of_experience,
                'core_stack': 'Python, React, AWS, MLOps',
                'value_statement': self.settings.user_info.background.elevator_pitch[:100]
            }
        
        # Generate each section using AI
        logger.info("📝 Generating header...")
        header = self._generate_header(personal_info, job_description, job_title, company)
        
        logger.info("🔧 Generating skills...")
        skills = self._generate_skills(job_description, job_title, company)
        
        logger.info("💼 Generating work experience...")
        # Use real work experience from config and generate bullets for each
        if self.settings.user_info.work_experience:
            experience = self._generate_experience_with_config(
                job_description, job_title, company, self.settings.user_info.work_experience
            )
        else:
            experience = self._generate_experience(job_description, job_title, company)
        
        logger.info("🎓 Using education from config...")
        # Use real education from config
        if self.settings.user_info.education:
            education = {
                'degree': self.settings.user_info.education.degree,
                'graduated': self.settings.user_info.education.graduated,
                'gpa': self.settings.user_info.education.gpa or '',
                'university': self.settings.user_info.education.university,
                'location': self.settings.user_info.education.location,
                'coursework': self.settings.user_info.education.coursework or 'Data Structures, Algorithms, Database Systems, Operating Systems, Computer Networks, Machine Learning'
            }
        else:
            education = self._generate_education()
        
        # Replace template placeholders
        self._fill_template(doc, header, skills, experience, education)
        
        # Save generated resume
        safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        
        output_dir = self.tailored_resume_dir / f"{safe_company}_{safe_title}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename: FirstName_LastName_CompanyName_Resume.docx
        first_name = personal_info['full_name'].split()[0] if personal_info['full_name'] else 'Resume'
        last_name = personal_info['full_name'].split()[-1] if len(personal_info['full_name'].split()) > 1 else ''
        filename = f"{first_name}_{last_name}_{safe_company}_Resume.docx" if last_name else f"{first_name}_{safe_company}_Resume.docx"
        
        output_file = output_dir / filename
        doc.save(str(output_file))
        
        logger.info(f"✅ Generated resume: {output_file}")
        return str(output_file)
    
    def _generate_header(self, personal_info: dict, job_description: str, job_title: str, company: str) -> dict:
        """Generate professional header matching job requirements."""
        
        # Calculate years of experience from work history
        years_experience = 10  # Default fallback
        if self.settings.user_info.work_experience:
            # Calculate from first job start date to current
            try:
                first_job = self.settings.user_info.work_experience[-1]  # Oldest job (last in list)
                # Extract start year from dates like "Feb 2015 – Jan 2019"
                start_date = first_job.dates.split('–')[0].strip()
                start_year = int(start_date.split()[-1])
                current_year = 2025
                years_experience = current_year - start_year
            except:
                pass
        
        # Analyze job to determine professional title and core stack
        prompt = f"""Based on this job description for {job_title} at {company}, generate a professional resume header.

Job Description:
{job_description[:1500]}

Generate ONLY the following, one per line:
1. Professional title (e.g., "Backend Engineer", "Full Stack Developer", "ML Engineer")
2. Years of experience (just a number like "10+" or "8+")
3. Core tech stack (3-5 key technologies from job description, comma-separated)
4. Value statement (one impressive achievement, 10-15 words max)

Format:
[Professional Title]
[Years like "10+"]
[Tech1, Tech2, Tech3, Tech4]
[Value statement with quantified impact]"""

        response = self.ai_service.generate_completion(prompt).strip()
        
        # Clean AI response - remove markdown and extra text
        response = response.replace('**', '')  # Remove bold markers
        response = response.replace('*', '')   # Remove italic markers
        # Remove common AI prefixes
        for prefix in ['Here are the requested sections:', 'Here is:', 'Here are:', 'Response:', '|']:
            response = response.replace(prefix, '')
        response = response.strip()
        
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        
        # Extract and clean title - make uppercase
        title = lines[0] if len(lines) > 0 else job_title
        title = title.replace('**', '').replace('*', '').strip()
        title = title.upper()  # Make all caps
        
        return {
            'full_name': personal_info['full_name'],
            'location': personal_info['location'],
            'phone': personal_info['phone'],
            'email': personal_info['email'],
            'linkedin': personal_info['linkedin'],
            'github': personal_info['github'],
            'title': title,
            'years': lines[1] if len(lines) > 1 else f"{years_experience}+",
            'core_stack': lines[2] if len(lines) > 2 else "Full Stack Development",
            'value_statement': lines[3] if len(lines) > 3 else "Proven track record of delivering high-impact solutions"
        }
    
    def _generate_skills(self, job_description: str, job_title: str, company: str) -> dict:
        """Generate skills section based on job requirements."""
        
        prompt = f"""Analyze this job description for {job_title} at {company} and generate a comprehensive Technical Skills section.

Job Description:
{job_description[:2000]}

Generate skills in these exact categories (one line per category):
1. Languages: [programming languages]
2. AI/ML: [if relevant - ML frameworks, tools]
3. Frontend: [frontend frameworks and tools]
4. Backend: [backend frameworks, APIs, architectures]
5. Databases: [databases used]
6. Cloud & DevOps: [cloud platforms, DevOps tools]
7. Other: [other relevant technologies]

Rules:
- Include ONLY skills explicitly mentioned or strongly implied in the job description
- Prioritize required skills over nice-to-have
- Be specific (e.g., "React, Next.js" not just "React")
- If a category isn't relevant, write "N/A"
- Output format: "Category: skill1, skill2, skill3"

Output the 7 lines:"""

        response = self.ai_service.generate_completion(prompt).strip()
        # Remove empty lines to avoid spacing issues
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        
        skills_dict = {}
        for line in lines:
            if ':' in line:
                category, items = line.split(':', 1)
                skills_dict[category.strip()] = items.strip()
        
        return skills_dict
    
    def _generate_experience(self, job_description: str, job_title: str, company: str) -> list:
        """Generate work experience bullets for past jobs."""
        
        # Get work history from config
        prompt = f"""Generate impressive work experience bullets for a resume targeting {job_title} at {company}.

Job Description (what they want):
{job_description[:2000]}

Generate 4 past job experiences, each with:
- Job Title | Company Name | Location | Dates (e.g., "Dec 2024 — Current")
- 4-5 bullet points following this formula:
  [Action Verb] [what you did] using [technology from job description], resulting in [quantified impact with metrics]

Rules:
1. Use technologies and skills from the job description
2. Every bullet MUST have quantified metrics (%, $, time saved, users, etc.)
3. Start with strong action verbs: Architected, Engineered, Optimized, Built, Deployed, Reduced, Increased
4. Show progression: most recent job is most impressive
5. Each bullet should be 1-2 lines max
6. Make dates realistic (work backwards from current date)

Format each job as:
JOB_TITLE | COMPANY | LOCATION | DATES
• Bullet point 1
• Bullet point 2
• Bullet point 3
• Bullet point 4

Generate all 4 jobs now:"""

        response = self.ai_service.generate_completion(prompt, temperature=0.8).strip()
        
        # Parse the response into structured format
        jobs = []
        current_job = None
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a job header (contains |)
            if '|' in line and not line.startswith('•'):
                if current_job:
                    jobs.append(current_job)
                
                parts = [p.strip() for p in line.split('|')]
                current_job = {
                    'title': parts[0] if len(parts) > 0 else '',
                    'company': parts[1] if len(parts) > 1 else '',
                    'location': parts[2] if len(parts) > 2 else '',
                    'dates': parts[3] if len(parts) > 3 else '',
                    'bullets': []
                }
            elif line.startswith('•') and current_job:
                bullet = line.lstrip('•').strip()
                current_job['bullets'].append(bullet)
        
        if current_job:
            jobs.append(current_job)
        
        return jobs[:4]  # Return max 4 jobs
    
    def _generate_experience_with_config(self, job_description: str, job_title: str, company: str, work_history: list) -> list:
        """Generate work experience bullets using real work history from config."""
        
        jobs = []
        for work in work_history:
            # Generate bullets for this specific job
            prompt = f"""Generate 4-5 impressive work experience bullets for this role, tailored to the target job.

Target Job: {job_title} at {company}
Target Job Description (what they want):
{job_description[:2000]}

Your Role:
Title: {work.title}
Company: {work.company}
Location: {work.location}
Dates: {work.dates}

Generate 4-5 bullet points following this formula:
[Action Verb] [what you did] using [technology from job description], resulting in [quantified impact with metrics]

Rules:
1. Use technologies and skills from the TARGET job description
2. Every bullet MUST have quantified metrics (%, $, time saved, users, etc.)
3. Start with strong action verbs: Architected, Engineered, Optimized, Built, Deployed, Reduced, Increased
4. Each bullet should be 1-2 lines max
5. Make it relevant to the TARGET job

Output ONLY the bullets, one per line, starting with •"""

            response = self.ai_service.generate_completion(prompt, temperature=0.8).strip()
            
            # Parse bullets
            bullets = []
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('•'):
                    bullet = line.lstrip('•').strip()
                    bullets.append(bullet)
            
            if bullets:
                jobs.append({
                    'title': work.title,
                    'company': work.company,
                    'location': work.location,
                    'dates': work.dates,
                    'bullets': bullets[:5]  # Max 5 bullets
                })
        
        return jobs
    
    def _generate_education(self) -> dict:
        """Generate education section."""
        # For now, use a template - can be enhanced later
        return {
            'degree': 'Bachelor of Science in Computer Science',
            'graduated': 'May 2015',
            'gpa': '3.8/4.0',
            'university': 'University of Technology',
            'location': 'Boston, MA',
            'coursework': 'Data Structures, Algorithms, Database Systems, Operating Systems, Computer Networks, Machine Learning'
        }
    
    def _fill_template(self, doc: Document, header: dict, skills: dict, experience: list, education: dict):
        """Fill the template with generated content while preserving formatting."""
        
        for paragraph in doc.paragraphs:
            text = paragraph.text
            
            # Replace header placeholders while preserving formatting
            if '[Full Name]' in text:
                self._replace_text_in_paragraph(paragraph, '[Full Name]', header['full_name'])
            elif '[Location]' in text and 'xxx' in text:
                self._replace_text_in_paragraph(paragraph, text, f"{header['location']} | {header['phone']} | {header['email']}")
            elif 'LinkedIn:' in text and 'xxxxx' in text:
                self._replace_text_in_paragraph(paragraph, text, f"LinkedIn: {header['linkedin']} | GitHub: {header['github']}")
            elif 'PROFESSIONAL TITLE' in text:
                self._replace_text_in_paragraph(paragraph, text, f"{header['title']} | {header['years']}+ YEARS | {header['core_stack']} | {header['value_statement']}")
            
            # Replace skills placeholders
            elif text.startswith('Languages:') and '[List' in text:
                self._replace_text_in_paragraph(paragraph, text, f"Languages: {skills.get('Languages', 'Python, JavaScript, TypeScript')}")
            elif text.startswith('AI/ML') and '[List' in text:
                ai_ml = skills.get('AI/ML', skills.get('AI/ML (if applicable)', ''))
                if ai_ml and ai_ml != 'N/A':
                    self._replace_text_in_paragraph(paragraph, text, f"AI/ML: {ai_ml}")
                else:
                    paragraph.clear()
            elif text.startswith('Frontend:') and '[List' in text:
                self._replace_text_in_paragraph(paragraph, text, f"Frontend: {skills.get('Frontend', 'React, Next.js')}")
            elif text.startswith('Backend:') and '[List' in text:
                self._replace_text_in_paragraph(paragraph, text, f"Backend: {skills.get('Backend', 'Node.js, Flask, REST APIs')}")
            elif text.startswith('Databases:') and '[List' in text:
                self._replace_text_in_paragraph(paragraph, text, f"Databases: {skills.get('Databases', 'PostgreSQL, MongoDB, Redis')}")
            elif text.startswith('Cloud & DevOps:') and '[List' in text:
                self._replace_text_in_paragraph(paragraph, text, f"Cloud & DevOps: {skills.get('Cloud & DevOps', 'AWS, Docker, Kubernetes')}")
            elif text.startswith('Other:') and '[List' in text:
                other = skills.get('Other', '')
                if other and other != 'N/A':
                    self._replace_text_in_paragraph(paragraph, text, f"Other: {other}")
                else:
                    paragraph.clear()
        
        # Replace experience section - track which job/bullet we're filling
        current_job_idx = -1
        current_bullet_idx = -1
        
        for paragraph in doc.paragraphs:
            text = paragraph.text
            
            # Job headers with pipe separator
            if '|' in text and '[' in text and ']' in text:
                # This is a job header line
                if '[Job Title]' in text or 'Job Title' in text.replace('[', '').replace(']', ''):
                    current_job_idx = 0
                    current_bullet_idx = -1
                elif '[Previous Job Title]' in text or 'Previous Job' in text.replace('[', '').replace(']', ''):
                    current_job_idx = 1
                    current_bullet_idx = -1
                elif '[Another Role' in text or '[Third' in text or '[Job 3' in text:
                    current_job_idx = 2
                    current_bullet_idx = -1
                elif '[Fourth' in text or '[Job 4' in text:
                    current_job_idx = 3
                    current_bullet_idx = -1
                
                # Replace with actual job data
                if 0 <= current_job_idx < len(experience):
                    job = experience[current_job_idx]
                    self._replace_text_in_paragraph(paragraph, text, f"{job['title']} | {job['company']} | {job['location']} | {job['dates']}")
                else:
                    paragraph.clear()
            
            # Bullet points
            elif text.startswith('•') and '[' in text:
                current_bullet_idx += 1
                if 0 <= current_job_idx < len(experience):
                    if current_bullet_idx < len(experience[current_job_idx]['bullets']):
                        bullet = experience[current_job_idx]['bullets'][current_bullet_idx]
                        self._replace_text_in_paragraph(paragraph, text, f"• {bullet}")
                    else:
                        paragraph.clear()
                else:
                    paragraph.clear()
            
            # Clear template instructions
            elif '[Focus on impact' in text or '[Include collaboration' in text or '[Always quantify' in text:
                paragraph.clear()
            elif '[Each bullet' in text or '[Remember' in text or '[Template' in text:
                paragraph.clear()
            
            # Replace education placeholders
            elif '[Degree Name]' in text:
                self._replace_text_in_paragraph(paragraph, '[Degree Name]', education['degree'])
            elif 'Graduated:' in text and '[Month Year]' in text:
                if education.get('gpa'):
                    self._replace_text_in_paragraph(paragraph, text, f"Graduated: {education['graduated']} GPA: {education['gpa']}")
                else:
                    self._replace_text_in_paragraph(paragraph, text, f"Graduated: {education['graduated']}")
            elif '[University Name]' in text:
                self._replace_text_in_paragraph(paragraph, '[University Name]', education['university'])
            elif text == '[City, State]':
                self._replace_text_in_paragraph(paragraph, '[City, State]', education['location'])
            elif 'Relevant Coursework:' in text and 'Data Structures' in text:
                self._replace_text_in_paragraph(paragraph, text, f"Relevant Coursework: {education['coursework']}")
    
    def _replace_text_in_paragraph(self, paragraph, old_text: str, new_text: str):
        """Replace text in paragraph while preserving formatting."""
        if old_text in paragraph.text:
            # Store original formatting
            if paragraph.runs:
                original_font = paragraph.runs[0].font
                paragraph.clear()
                run = paragraph.add_run(new_text)
                # Apply original formatting
                run.font.name = original_font.name
                run.font.size = original_font.size
                run.font.bold = original_font.bold
                run.font.italic = original_font.italic
            else:
                paragraph.text = new_text
