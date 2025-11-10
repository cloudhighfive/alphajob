"""
AI Service for interacting with Ollama LLM, Claude (Anthropic), and GPT-4 (OpenAI).
"""

import ollama
from typing import Dict, List, Optional, Union
import json
import re
import os

from src.config import Settings
from src.utils.logger import get_logger


logger = get_logger(__name__)


class AIService:
    """Service for AI/LLM interactions using Ollama, Claude, or GPT-4."""
    
    def __init__(self, settings: Settings):
        """
        Initialize AI Service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.model = settings.ai_settings.model
        self.temperature = settings.ai_settings.temperature
        self.tone = settings.ai_settings.tone
        self.answer_length = settings.ai_settings.answer_length
        
        # Check which AI provider to use based on model name
        self.provider = self._determine_provider(self.model)
        
        # Initialize API clients if needed
        self.anthropic_client = None
        self.openai_client = None
        
        if self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    logger.warning("⚠️ ANTHROPIC_API_KEY not found. Add it to .env file.")
                    logger.warning("   Falling back to Ollama...")
                    self.provider = "ollama"
                    self.model = "llama3.1"
                else:
                    self.anthropic_client = Anthropic(api_key=api_key)
                    logger.info(f"✅ Initialized Claude API with model: {self.model}")
            except ImportError:
                logger.warning("⚠️ anthropic package not installed. Run: pip install anthropic")
                logger.warning("   Falling back to Ollama...")
                self.provider = "ollama"
                self.model = "llama3.1"
        
        elif self.provider == "openai":
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("⚠️ OPENAI_API_KEY not found. Add it to .env file.")
                    logger.warning("   Falling back to Ollama...")
                    self.provider = "ollama"
                    self.model = "llama3.1"
                else:
                    self.openai_client = OpenAI(api_key=api_key)
                    logger.info(f"✅ Initialized OpenAI API with model: {self.model}")
            except ImportError:
                logger.warning("⚠️ openai package not installed. Run: pip install openai")
                logger.warning("   Falling back to Ollama...")
                self.provider = "ollama"
                self.model = "llama3.1"
        
        else:
            logger.info(f"✅ Initialized Ollama with model: {self.model}")
    
    def _determine_provider(self, model: str) -> str:
        """Determine which AI provider to use based on model name."""
        if model.startswith("claude"):
            return "anthropic"
        elif model.startswith("gpt-"):
            return "openai"
        else:
            return "ollama"
    
    def _extract_missing_critical_skills(self, original_skills: str, job_description: str) -> List[str]:
        """
        Extract critical skills from job description that are missing from original skills.
        
        Args:
            original_skills: Original skills text
            job_description: Job description text
            
        Returns:
            List of missing critical skills that appear frequently in JD
        """
        original_lower = original_skills.lower()
        jd_lower = job_description.lower()
        
        # Define critical tech skills to check for
        # IMPORTANT: Use word boundaries to avoid false matches (e.g., "java" matching "javascript")
        critical_skills_map = {
            # Backend languages - use regex word boundaries
            'kotlin': 'Kotlin',
            r'\bjava\b': 'Java',  # \b = word boundary, won't match "javascript"
            'spring boot': 'Spring Boot',
            'spring framework': 'Spring Framework',
            r'\bgolang\b': 'Go',
            r'\brust\b': 'Rust',
            r'\bscala\b': 'Scala',
            
            # Frontend frameworks
            r'\breact\b': 'React',  # won't match "reactive"
            r'\bvue\b': 'Vue.js',
            'angular': 'Angular',
            'svelte': 'Svelte',
            
            # Backend frameworks
            'express': 'Express.js',
            'nestjs': 'NestJS',
            'fastify': 'Fastify',
            
            # Databases
            'dynamodb': 'DynamoDB',
            'cassandra': 'Cassandra',
            'neo4j': 'Neo4j',
            
            # Cloud/DevOps
            'terraform': 'Terraform',
            'ansible': 'Ansible',
            'helm': 'Helm',
            'istio': 'Istio',
            'argocd': 'ArgoCD',
            
            # Architecture patterns
            'microservices': 'Microservices',
            'event-driven': 'Event-Driven Architecture',
            'grpc': 'gRPC',
            'websockets': 'WebSockets',
            
            # Testing
            'jest': 'Jest',
            'pytest': 'PyTest',
            'junit': 'JUnit',
            'cypress': 'Cypress',
            'selenium': 'Selenium',
            
            # Monitoring
            'datadog': 'Datadog',
            'new relic': 'New Relic',
            'splunk': 'Splunk',
        }
        
        missing_skills = []
        
        for search_term, proper_name in critical_skills_map.items():
            # Check if using regex pattern (starts with \b)
            is_regex = search_term.startswith(r'\b')
            
            # Check if skill is missing from original
            if is_regex:
                # Use regex for word boundary matching
                import re as regex_module
                pattern = regex_module.compile(search_term, regex_module.IGNORECASE)
                original_has_it = bool(pattern.search(original_lower))
                jd_matches = len(pattern.findall(jd_lower))
            else:
                # Simple substring search
                original_has_it = (search_term in original_lower or proper_name.lower() in original_lower)
                jd_matches = jd_lower.count(search_term)
            
            # If missing from original but appears 2+ times in JD, it's critical
            if not original_has_it and jd_matches >= 2:
                missing_skills.append(proper_name)
                logger.info(f"   🔍 Found missing critical skill: {proper_name} ({jd_matches}x in JD)")
        
        if missing_skills:
            logger.info(f"\n{'='*70}")
            logger.info(f"⚠️  DETECTED {len(missing_skills)} MISSING CRITICAL SKILLS")
            logger.info(f"{'='*70}")
            for skill in missing_skills:
                logger.info(f"   • {skill}")
            logger.info(f"{'='*70}\n")
        
        return missing_skills

    
    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = 4000
    ) -> str:
        """
        Generate completion using configured AI provider.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            temp = temperature or self.temperature
            
            if self.provider == "anthropic":
                return self._generate_anthropic(prompt, system_prompt, temp, max_tokens)
            elif self.provider == "openai":
                return self._generate_openai(prompt, system_prompt, temp, max_tokens)
            else:
                return self._generate_ollama(prompt, system_prompt, temp)
            
        except Exception as e:
            logger.error(f"❌ AI generation error: {str(e)}")
            raise
    
    def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Generate completion using Ollama."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={"temperature": temperature}
        )
        
        return response['message']['content'].strip()
    
    def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """Generate completion using Claude (Anthropic)."""
        if not self.anthropic_client:
            raise RuntimeError("Anthropic client not initialized")
        
        messages = [{"role": "user", "content": prompt}]
        
        response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else "You are a professional resume writer.",
            messages=messages
        )
        
        return response.content[0].text.strip()
    
    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """Generate completion using OpenAI GPT."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    def tailor_resume_summary(
        self,
        original_summary: str,
        job_description: str,
        job_title: str,
        company: str
    ) -> str:
        """
        Tailor resume summary for specific job.
        
        Args:
            original_summary: Original summary text
            job_description: Job description
            job_title: Job title
            company: Company name
            
        Returns:
            Tailored summary text
        """
        # Extract critical keywords and role type
        role_analysis = self._analyze_job_role(job_description, job_title)
        
        # Extract top keywords for headline
        top_keywords = self._extract_top_keywords(job_description, top_n=10)
        
        system_prompt = """You are an expert ATS resume optimizer and professional resume writer. 
Your task is to rewrite resume sections to maximize ATS scores while maintaining authenticity."""
        
        role_focus_instruction = f"""

ROLE FOCUS ANALYSIS:
This job is: {role_analysis['primary_role']}
Emphasis should be: {role_analysis['emphasis_areas']}
De-emphasize: {role_analysis['de_emphasize']}

TOP KEYWORDS FROM JOB (use these):
{', '.join(top_keywords)}
"""
        
        prompt = f"""Rewrite this resume summary using professional best practices for ATS and recruiter scanning.

TARGET JOB:
Title: {job_title}
Company: {company}
{role_focus_instruction}

JOB DESCRIPTION:
{job_description[:3000]}

ORIGINAL SUMMARY:
{original_summary}

PROFESSIONAL BEST PRACTICES (CRITICAL):

1. HEADLINE FORMAT (First Line - MUST BE UNDER 10 WORDS):
   Create a concise headline that acts like an elaborate LinkedIn headline.
   STRICT WORD LIMIT: Maximum 9 words total (count carefully!)
   
   Bad (too generic): "Passionate software engineer seeking opportunities to grow"
   Good (9 words): "Backend Engineer | 9 Years | Kotlin/Java/Spring | 10M+ Users"
   
   The headline MUST include (in order):
   - Your role matching job (2-3 words): "Backend Engineer" or "Full-Stack Developer"
   - Separator: |
   - Years (2 words): "9 Years Experience" or "9 Years"
   - Separator: |
   - Top 2-3 technologies (2-3 words): "Kotlin/Java/Spring Boot" or "React/Node.js"
   - Separator: |
   - Scale metric (1-2 words): "10M+ Users" or "Scaled 10M+"
   
   Total: Should be 8-9 words maximum
   
   Examples of good 9-word headlines:
   - "Backend Engineer | 9 Years | Kotlin/Spring Boot | 10M+ Users"
   - "Full-Stack Developer | 8 Years | React/Node.js | Scaled Apps"
   - "Software Engineer | 9 Years | Java/Microservices | 100K+ Requests"

2. BODY PARAGRAPHS (After Headline):
   - 2-3 concise sentences maximum
   - Front-load with TOP keywords from job description
   - Show breadth of relevant experience
   - Include quantified achievements
   - Match the role type (Backend, Frontend, Full-Stack, ML, etc.)

3. KEYWORD INTEGRATION:
   - Extract TOP 10-15 keywords from job description (technologies, skills, concepts)
   - Naturally integrate them - don't just list
   - Use EXACT terminology from job description
   - Aim for 12-16% keyword density

4. ROLE POSITIONING (CRITICAL):
   - If backend job: Lead with "Backend Engineer" NOT "ML Engineer"
   - If requires Kotlin/Java: Mention in FIRST line
   - If emphasizes scale: Include "Scaled to X users/systems"
   - Match seniority: Use "Senior" if job requires 5+ years

5. OUTPUT FORMAT:
   Line 1: [Headline under 10 words]
   [Blank line]
   Lines 2-3: [Body paragraph with achievements]
   
   Do NOT use bullet points, symbols, or "Summary of Qualifications" headers
   Just output the text directly

EXAMPLE FOR BACKEND ROLE:
Backend Engineer | 9 Years | Kotlin, Java, Spring Boot | Built Systems Serving 10M+ Users

Senior software engineer specializing in microservices architecture, distributed systems, and cloud infrastructure. Proven track record architecting scalable backend services using Kotlin, Java, and Spring Boot frameworks across AWS and Kubernetes environments. Led teams in building high-performance APIs serving 10M+ users with 99.9% uptime, reducing latency by 45% through database optimization and caching strategies.

OUTPUT ONLY THE REWRITTEN SUMMARY (headline + body, no commentary):"""
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🤖 AI PROMPT - TAILOR SUMMARY ({self.provider}/{self.model})")
        logger.info(f"{'='*70}")
        logger.info(f"Target: {job_title} at {company}")
        logger.info(f"Role Type: {role_analysis['primary_role']}")
        logger.info(f"Top Keywords: {', '.join(top_keywords[:5])}")
        logger.info(f"{'='*70}\n")
        
        response = self.generate_completion(prompt, system_prompt, temperature=0.3)
        
        # Clean up any remaining AI commentary
        response = self._clean_ai_commentary(response)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ AI RESPONSE - TAILORED SUMMARY ({len(response)} chars)")
        logger.info(f"{'='*70}")
        logger.info(response[:500] + "..." if len(response) > 500 else response)
        logger.info(f"{'='*70}\n")
        
        return response
    
    def _analyze_job_role(self, job_description: str, job_title: str) -> Dict[str, str]:
        """
        Analyze job description to determine primary role type and what to emphasize.
        
        Args:
            job_description: Job description text
            job_title: Job title
            
        Returns:
            Dict with role analysis
        """
        jd_lower = job_description.lower()
        title_lower = job_title.lower()
        
        # Check for role indicators
        role_indicators = {
            'backend': ['backend', 'kotlin', 'java', 'spring boot', 'jvm', 'microservices', 'api development'],
            'frontend': ['frontend', 'react', 'vue', 'angular', 'ui/ux', 'web development'],
            'fullstack': ['full-stack', 'full stack', 'fullstack', 'end-to-end'],
            'ml_ai': ['machine learning', 'ml engineer', 'ai engineer', 'deep learning', 'mlops'],
            'devops': ['devops', 'sre', 'site reliability', 'infrastructure', 'platform engineer'],
            'data': ['data engineer', 'data pipeline', 'etl', 'data warehouse']
        }
        
        # Count indicators
        role_scores = {}
        for role, indicators in role_indicators.items():
            score = sum(jd_lower.count(indicator) for indicator in indicators)
            role_scores[role] = score
        
        # Determine primary role
        primary_role = max(role_scores, key=role_scores.get)
        
        # Generate emphasis areas based on role
        emphasis_map = {
            'backend': 'Backend development, API design, microservices architecture, scalability, database optimization',
            'frontend': 'Frontend development, UI/UX, component architecture, performance optimization, accessibility',
            'fullstack': 'Full-stack development, both frontend and backend technologies, end-to-end ownership',
            'ml_ai': 'Machine learning, model development, MLOps, data pipelines, AI/ML frameworks',
            'devops': 'Infrastructure automation, CI/CD, monitoring, reliability, cloud platforms',
            'data': 'Data engineering, ETL pipelines, data warehousing, analytics, big data technologies'
        }
        
        de_emphasize_map = {
            'backend': 'ML/AI model training, deep learning frameworks (keep relevant parts like MLOps/data pipelines)',
            'frontend': 'Backend APIs, database optimization, infrastructure (keep relevant parts like API integration)',
            'fullstack': 'Heavy ML/AI specialization (keep if job mentions it)',
            'ml_ai': 'General web development (unless job is ML product)',
            'devops': 'Application development, ML model training (focus on infrastructure)',
            'data': 'Application development, frontend work (focus on data engineering)'
        }
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 JOB ROLE ANALYSIS")
        logger.info(f"{'='*70}")
        logger.info(f"Role Scores: {role_scores}")
        logger.info(f"Primary Role: {primary_role.upper()} (score: {role_scores[primary_role]})")
        logger.info(f"Emphasis: {emphasis_map[primary_role]}")
        logger.info(f"De-emphasize: {de_emphasize_map[primary_role]}")
        logger.info(f"{'='*70}\n")
        
        return {
            'primary_role': primary_role.upper().replace('_', '/'),
            'emphasis_areas': emphasis_map[primary_role],
            'de_emphasize': de_emphasize_map[primary_role]
        }
    
    def _extract_top_keywords(self, job_description: str, top_n: int = 15) -> List[str]:
        """
        Extract top keywords from job description.
        
        Args:
            job_description: Job description text
            top_n: Number of top keywords to extract
            
        Returns:
            List of top keywords
        """
        jd_lower = job_description.lower()
        
        # Common tech keywords to look for
        tech_keywords = [
            # Languages
            'python', 'javascript', 'typescript', 'java', 'kotlin', 'go', 'rust', 'c++', 'scala',
            # Frontend
            'react', 'vue', 'angular', 'next.js', 'svelte',
            # Backend
            'spring boot', 'django', 'flask', 'fastapi', 'express', 'node.js',
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            # Cloud
            'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'terraform',
            # Concepts
            'microservices', 'rest api', 'graphql', 'ci/cd', 'devops', 'agile',
            # Tools
            'git', 'jenkins', 'kafka', 'spark', 'airflow'
        ]
        
        # Count occurrences
        keyword_counts = []
        for keyword in tech_keywords:
            count = jd_lower.count(keyword)
            if count > 0:
                keyword_counts.append((keyword, count))
        
        # Sort by frequency
        keyword_counts.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N keywords
        top_keywords = [kw for kw, _ in keyword_counts[:top_n]]
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔑 TOP {top_n} KEYWORDS FROM JOB DESCRIPTION")
        logger.info(f"{'='*70}")
        for kw, count in keyword_counts[:top_n]:
            logger.info(f"   {kw}: {count}x")
        logger.info(f"{'='*70}\n")
        
        return top_keywords

    
    def tailor_skills_section(
        self,
        original_skills: str,
        job_description: str,
        job_title: str,
        company: str
    ) -> str:
        """
        Tailor skills section for specific job.
        
        Args:
            original_skills: Original skills text
            job_description: Job description
            job_title: Job title
            company: Company name
            
        Returns:
            Tailored skills text
        """
        # STEP 1: Extract critical missing skills from job description
        missing_critical_skills = self._extract_missing_critical_skills(original_skills, job_description)
        
        system_prompt = """You are an expert ATS resume optimizer specializing in technical skills sections.
Your goal is to maximize keyword matching while preserving all original skills."""
        
        missing_skills_instruction = ""
        if missing_critical_skills:
            missing_skills_instruction = f"""

CRITICAL MISSING SKILLS TO ADD:
The following skills appear FREQUENTLY in the job description but are MISSING from original skills.
YOU MUST ADD THESE to the appropriate categories:
{', '.join(missing_critical_skills)}

IMPORTANT: Add these skills at the FRONT of their respective categories for maximum ATS impact!"""
        
        prompt = f"""Optimize this TECHNICAL SKILLS section using professional best practices for ATS and recruiter scanning.

TARGET JOB:
Title: {job_title}
Company: {company}

JOB DESCRIPTION:
{job_description[:3000]}

ORIGINAL TECHNICAL SKILLS:
{original_skills}
{missing_skills_instruction}

PROFESSIONAL BEST PRACTICES (CRITICAL):

1. RECRUITER SCANNING OPTIMIZATION:
   55% of recruiters search for job title + specific technologies in initial screenings.
   This section MUST be:
   - Near the top of resume (it already is)
   - Organized by clear categories
   - Keyword-rich but honest
   - Scannable by both humans and ATS

2. PROFESSIONAL FORMAT:
   Use this EXACT format (categories on single lines):
   
   Languages: Python, JavaScript, Java, SQL, HTML/CSS
   Frameworks: React, Node.js, Django, Express, Spring Boot
   Databases: PostgreSQL, MongoDB, Redis, MySQL
   Cloud/Tools: AWS (EC2, S3, Lambda), Docker, Kubernetes, Git, CI/CD
   
   Why this works:
   - Scannable by humans in 2 seconds
   - ATS can easily extract keywords
   - Categories are clear and professional
   - Shows breadth and depth

3. KEYWORD OPTIMIZATION:
   - Extract TOP 10-15 technologies from job description
   - Place them FIRST in their categories
   - Use EXACT terminology from job description
   - If JD says "PostgreSQL", use "PostgreSQL" not "Postgres"
   - If JD says "Spring Boot", use "Spring Boot" not just "Spring"

4. ADDING MISSING CRITICAL SKILLS:
   - If critical skills are listed above, ADD them at FRONT of categories
   - Example: For Kotlin job, add "Kotlin, Java, Spring Boot" as FIRST items in Languages/Frameworks
   - Keep ALL original skills after the added ones

5. CATEGORIES TO USE (map your categories to these standard names):
   - Languages: (programming languages like Python, Java, Kotlin, JavaScript)
   - Frameworks: (React, Spring Boot, Django, Flask, etc.)
   - Databases: (PostgreSQL, MongoDB, Redis, etc.)
   - Cloud/Tools: (AWS, Docker, Kubernetes, Git, CI/CD, etc.)
   
   OR keep your original 4 categories if they're similar:
   - Programming & Frameworks:
   - Data & AI/ML Tools:
   - Cloud & DevOps:
   - Databases & APIs:

6. REORDERING RULES:
   - Within each category: Job-required skills FIRST, then supporting skills
   - NEVER delete original skills
   - Add missing critical skills at the FRONT
   - Comma-separated, single line per category

OUTPUT FORMAT:
- CRITICAL: Output ONLY the 4 category lines, nothing else
- No explanations, headers, or commentary
- Each category on ONE line
- Format: "Category: skill1, skill2, skill3, ..."

OUTPUT ONLY THE 4 CATEGORY LINES:"""
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🤖 AI PROMPT - TAILOR SKILLS ({self.provider}/{self.model})")
        logger.info(f"{'='*70}")
        logger.info(f"Target: {job_title} at {company}")
        logger.info(f"{'='*70}\n")
        
        response = self.generate_completion(prompt, system_prompt, temperature=0.2)
        
        # Clean up the response
        cleaned_response = self._format_skills_single_line(response)
        cleaned_response = self._clean_ai_commentary(cleaned_response)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ AI RESPONSE - TAILORED SKILLS")
        logger.info(f"{'='*70}")
        logger.info(cleaned_response)
        logger.info(f"{'='*70}\n")
        
        return cleaned_response
    
    def _clean_ai_commentary(self, text: str) -> str:
        """Remove common AI commentary patterns from responses."""
        # Remove common AI prefixes
        patterns = [
            r'^Here is the (rewritten|updated|tailored).*?:\s*',
            r'^Here are the (rewritten|updated|tailored).*?:\s*',
            r"^Here's the (rewritten|updated|tailored).*?:\s*",
            r'^I have (rewritten|updated|tailored).*?:\s*',
            r"^I've (rewritten|updated|tailored).*?:\s*",
            r'^(Rewritten|Updated|Tailored).*?:\s*',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        return text.strip()
    
    def _format_skills_single_line(self, skills_text: str) -> str:
        """
        Format skills to ensure category and skills are on the same line.
        Remove duplicates and ensure clean formatting.
        
        Args:
            skills_text: Raw skills text from AI
            
        Returns:
            Formatted skills with each category on a single line
        """
        lines = skills_text.strip().split('\n')
        formatted_lines = []
        seen_categories = set()  # Track categories we've already added
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a category line (has colon)
            if ':' in line:
                parts = line.split(':', 1)
                category = parts[0].strip()
                skills = parts[1].strip() if len(parts) > 1 else ''
                
                # Skip if we've already seen this category
                if category in seen_categories:
                    logger.debug(f"   ⚠️  Skipping duplicate category: {category}")
                    continue
                
                if skills:
                    # Complete line with category and skills
                    formatted_lines.append(line)
                    seen_categories.add(category)
                    current_category = None
                else:
                    # Category without skills (will be on next line)
                    current_category = category
            elif current_category:
                # This line has the skills for the previous category
                if current_category not in seen_categories:
                    formatted_lines.append(f"{current_category}: {line}")
                    seen_categories.add(current_category)
                current_category = None
            else:
                # Standalone line, keep as-is if not empty
                if line:
                    formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def tailor_work_experience(
        self,
        job_info: Dict[str, any],
        target_job_description: str,
        target_job_title: str,
        target_company: str
    ) -> List[str]:
        """
        Tailor work experience bullets for specific job.
        
        Args:
            job_info: Dict with 'company', 'title', 'dates', 'bullets'
            target_job_description: Target job description
            target_job_title: Target job title
            target_company: Target company name
            
        Returns:
            List of tailored bullet points
        """
        job_title = job_info.get('title', '')
        company = job_info.get('company', '')
        bullets = job_info.get('bullets', [])
        dates = job_info.get('dates', '')
        
        bullets_text = "\n".join(f"{i+1}. {bullet}" for i, bullet in enumerate(bullets))
        num_bullets = len(bullets)
        
        # CRITICAL: Extract missing skills to inject into bullets
        combined_original = bullets_text
        missing_critical_skills = self._extract_missing_critical_skills(combined_original, target_job_description)
        
        missing_skills_instruction = ""
        if missing_critical_skills:
            missing_skills_instruction = f"""

🚨 CRITICAL MISSING SKILLS THAT MUST BE INJECTED:
The following skills appear FREQUENTLY in the job description but are MISSING from your bullets:
{', '.join(missing_critical_skills)}

YOU MUST INCORPORATE THESE SKILLS INTO THE BULLETS!
- Add them naturally to 2-3 bullets each
- Use them in realistic contexts (e.g., "using Kotlin and Java", "with Spring Boot framework")
- Front-load them in the bullet (within first 10 words)
- Make it believable - don't just list them

Example transformations:
BEFORE: "Architected microservices platform, reducing deployment time by 45%"
AFTER: "Architected microservices platform using Kotlin, Spring Boot, and PostgreSQL, reducing deployment time by 45% and improving system reliability to 99.9%"

BEFORE: "Built scalable APIs for data processing workloads"
AFTER: "Built scalable REST APIs using Java and Spring Boot framework for data processing workloads, supporting 100K+ requests/day"
"""
        
        system_prompt = """You are an expert ATS resume optimizer specializing in quantifiable, achievement-focused work experience bullets.
Your goal is to maximize keyword density and ATS matching while maintaining authenticity."""
        
        prompt = f"""Rewrite these work experience bullets using professional best practices for ATS and recruiter impact.

YOUR EXPERIENCE:
Position: {job_title} at {company}
Dates: {dates}

CURRENT BULLETS:
{bullets_text}

TARGET JOB:
Title: {target_job_title}
Company: {target_company}

JOB DESCRIPTION:
{target_job_description[:3000]}
{missing_skills_instruction}

PROFESSIONAL BEST PRACTICES (CRITICAL):

1. THE WINNING BULLET FORMULA:
   Every bullet MUST follow this structure:
   [Action Verb] + [What You Did] + [How You Did It] + [Impact/Result]
   
   Bad: "Worked on backend team to improve system performance"
   Good: "Optimized database queries using indexing and caching strategies, reducing API response time by 45% and improving user experience for 2M+ daily active users"
   
   The good example has:
   ✅ Specific action (Optimized)
   ✅ Technical detail (indexing and caching)
   ✅ Measurable impact (45% faster)
   ✅ Scale context (2M+ users)

2. ACTION VERBS (Start Every Bullet):
   Use strong, specific action verbs:
   - Architected, Engineered, Optimized, Deployed, Automated
   - Accelerated, Reduced, Increased, Built, Designed
   - Implemented, Scaled, Migrated, Transformed, Led

3. KEYWORD INTEGRATION (MOST IMPORTANT):
   - Identify TOP 10-15 keywords from job description (technologies appearing 3+ times)
   - Naturally integrate them into bullets
   - Use EXACT terminology from job description
   
   Example: JD mentions "microservices architecture, Kubernetes, CI/CD pipelines"
   Your bullet: "Migrated monolithic application to microservices architecture using Kubernetes, implementing CI/CD pipelines that reduced deployment time by 60%"
   
   ✅ Used all 3 keywords naturally while describing real work

4. QUANTIFY EVERYTHING:
   Every bullet needs measurable impact:
   - Percentages: "45% faster", "30% reduction", "60% improvement"
   - Scale: "2M+ users", "10K+ requests/day", "serving 100K+ customers"
   - Time: "from hours to minutes", "2x faster deployment"
   - Money: "$100K saved", "generated $500K revenue"
   - Team: "led team of 5", "collaborated with 20+ engineers"

5. TECHNICAL DEPTH:
   Include specific technologies and methods:
   - Don't say: "Improved database performance"
   - Do say: "Optimized PostgreSQL queries with indexing and Redis caching"
   
   - Don't say: "Built APIs for users"
   - Do say: "Engineered REST APIs using Spring Boot and Java, handling 50K requests/minute"

6. MISSING SKILLS INJECTION (CRITICAL):
   If critical missing skills are listed above:
   - MUST incorporate them into 2-3 bullets
   - Add naturally: "using Kotlin and Spring Boot" or "with Java framework"
   - Front-load in first 10 words
   
   Example transformation:
   Before: "Built scalable backend services"
   After: "Engineered scalable backend microservices using Kotlin, Spring Boot, and PostgreSQL, supporting 100K+ daily API requests with 99.9% uptime"

7. OUTPUT FORMAT:
   - Output EXACTLY {num_bullets} bullets (same as original count)
   - NO bullet symbols (•, -, *), NO numbers (1., 2.)
   - Just plain text, one bullet per line
   - Start each with action verb
   - Include technology + metric + scale

OUTPUT EXACTLY {num_bullets} BULLETS (plain text, one per line):"""
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🤖 AI PROMPT - TAILOR EXPERIENCE ({self.provider}/{self.model})")
        logger.info(f"{'='*70}")
        logger.info(f"Position: {job_title} at {company}")
        logger.info(f"Target: {target_job_title} at {target_company}")
        logger.info(f"Bullets to generate: {num_bullets}")
        logger.info(f"{'='*70}\n")
        
        response = self.generate_completion(prompt, system_prompt, temperature=0.4)
        
        # Clean and parse bullets
        response = self._clean_ai_commentary(response)
        tailored_bullets = self._parse_bullets(response, num_bullets)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ AI RESPONSE - {len(tailored_bullets)} BULLETS GENERATED")
        logger.info(f"{'='*70}")
        for i, bullet in enumerate(tailored_bullets, 1):
            logger.info(f"{i}. {bullet[:100]}..." if len(bullet) > 100 else f"{i}. {bullet}")
        logger.info(f"{'='*70}\n")
        
        # Analyze keyword density
        self._analyze_keyword_density(tailored_bullets, target_job_description)
        
        return tailored_bullets if tailored_bullets else bullets
    
    def _parse_bullets(self, text: str, expected_count: int) -> List[str]:
        """Parse bullet points from AI response."""
        bullets = []
        seen = set()
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet markers and numbers
            line = re.sub(r'^[\•\-\*\d\.]+\s*', '', line)
            line = line.strip()
            
            # Skip if duplicate or too short
            if line and line not in seen and len(line) > 20:
                bullets.append(line)
                seen.add(line)
        
        # If we got fewer bullets than expected, log warning
        if len(bullets) < expected_count:
            logger.warning(f"⚠️  Generated {len(bullets)} bullets, expected {expected_count}")
        
        return bullets[:expected_count] if bullets else []
    
    def _analyze_keyword_density(self, bullets: List[str], job_description: str):
        """Analyze and log keyword density for quality validation."""
        combined_text = ' '.join(bullets).lower()
        
        # Extract potential keywords from job description
        jd_lower = job_description.lower()
        
        # Common tech keywords to check
        tech_keywords = [
            'python', 'java', 'javascript', 'typescript', 'kotlin', 'go', 'rust',
            'react', 'vue', 'angular', 'node', 'express', 'django', 'flask', 'spring',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins',
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'microservices', 'api', 'rest', 'graphql', 'grpc',
            'ci/cd', 'devops', 'agile', 'scrum'
        ]
        
        keyword_stats = []
        for keyword in tech_keywords:
            jd_count = jd_lower.count(keyword)
            bullet_count = combined_text.count(keyword)
            if jd_count > 0 and bullet_count > 0:
                keyword_stats.append((keyword, jd_count, bullet_count))
        
        # Sort by JD frequency
        keyword_stats.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 KEYWORD DENSITY ANALYSIS (Top Matches)")
        logger.info(f"{'='*70}")
        for keyword, jd_count, bullet_count in keyword_stats[:15]:
            match_rate = (bullet_count / jd_count) * 100 if jd_count > 0 else 0
            status = "✅" if match_rate >= 40 else "⚠️" if match_rate >= 20 else "❌"
            logger.info(f"{status} '{keyword}': JD={jd_count}x, Bullets={bullet_count}x ({match_rate:.0f}% coverage)")
        logger.info(f"{'='*70}\n")
    
    def answer_question(
        self,
        question: str,
        job_description: str,
        job_title: str,
        company: str,
        user_background: str
    ) -> str:
        """
        Generate answer to application question.
        
        Args:
            question: Application question
            job_description: Job description
            job_title: Job title
            company: Company name
            user_background: User background/elevator pitch
            
        Returns:
            Generated answer
        """
        logger.info(f"         🤖 Generating AI answer...")
        
        # Check if this is a numeric question
        is_numeric = any(keyword in question.lower() for keyword in ['how many', 'years of', 'number of', 'salary', 'compensation'])
        
        prompt = f"""
Answer this job application question for a {job_title} position at {company}.

Question: {question}

Your Background:
{user_background}

Job Description:
{job_description}

Requirements:
- Be {self.answer_length}
- Use a {self.tone} tone
- Relate your experience to the job requirements
- Be honest and authentic
{"- For numeric questions, provide ONLY the number (e.g., '5' not '5 years')" if is_numeric else ""}
- Return only the answer, no additional commentary

Answer:"""
        
        answer = self.generate_completion(prompt)
        # Remove markdown formatting (e.g., **, *, _, `, #)
        import re
        answer = re.sub(r'[\*`_#]', '', answer)
        logger.info(f"         🤖 AI generated answer ({len(answer)} chars, markdown stripped)")
        return answer
    
    def select_best_option(
        self,
        question: str,
        options: List[str],
        job_description: str,
        job_title: str,
        company: str,
        multi_select: bool = False
    ) -> Union[str, List[str]]:
        """
        Select best option(s) from multiple choice.
        
        Args:
            question: Question text
            options: Available options
            job_description: Job description
            job_title: Job title
            company: Company name
            multi_select: Whether multiple selections are allowed
            
        Returns:
            Selected option(s)
        """
        logger.info(f"         🤖 Selecting from {len(options)} options...")
        options_text = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
        
        # Get user background from settings (with safe null checking)
        background = self.settings.user_info.background
        user_background = background.elevator_pitch if background and hasattr(background, 'elevator_pitch') else "Experienced software engineer"
        
        prompt = f"""
Select the best option{'(s)' if multi_select else ''} for this job application question.

Question: {question}
Position: {job_title} at {company}

Available Options:
{options_text}

Your Background:
{user_background}

Job Requirements:
{job_description[:1500]}

Instructions:
- Select the option that best matches the job requirements and your background
{"- You can select multiple options if relevant" if multi_select else "- Select only ONE option"}
- Return ONLY the exact option text, nothing else
{"- If multiple, separate with '|||'" if multi_select else ""}

Selected Option{'(s)' if multi_select else ''}:"""
        
        logger.info(f"Selecting option for: {question[:50]}...")
        response = self.generate_completion(prompt)
        
        if multi_select and '|||' in response:
            selected = [opt.strip() for opt in response.split('|||')]
            return [s for s in selected if s in options]
        else:
            # Find best match in options
            response_lower = response.lower().strip()
            for option in options:
                if option.lower() in response_lower or response_lower in option.lower():
                    return option
            # Fallback to first option
            logger.warning(f"Could not match response '{response}' to options, using first option")
            return options[0] if options else ""
