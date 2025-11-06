"""
Resume Tailoring Service - NEW WORKFLOW
Extracts required skills from JD and generates targeted experience bullets
"""

from typing import Dict, List, Tuple
import re
from src.utils.logger import get_logger
from src.services.ai_service import AIService
from src.config import Settings

logger = get_logger(__name__)


class ResumeTailoringService:
    """Service for tailoring resumes to specific job descriptions."""
    
    def __init__(self, settings: Settings):
        """Initialize the service."""
        self.settings = settings
        self.ai_service = AIService(settings)
    
    def extract_required_skills(self, job_description: str) -> Dict[str, List[str]]:
        """
        Extract required skills from job description, categorized by type.
        
        Args:
            job_description: Job description text
            
        Returns:
            Dict with categorized skills: {
                'languages': [...],
                'frontend': [...],
                'backend': [...],
                'databases': [...],
                'devops': [...],
                'cloud': [...],
                'other': [...]
            }
        """
        logger.info("\n" + "="*70)
        logger.info("🔍 STEP 1: EXTRACTING REQUIRED SKILLS FROM JOB DESCRIPTION")
        logger.info("="*70)
        
        jd_lower = job_description.lower()
        
        # Define skill categories with their keywords
        skill_categories = {
            'languages': {
                'keywords': [
                    r'\bjava\b', r'\bkotlin\b', r'\bpython\b', r'\bjavascript\b', 
                    r'\btypescript\b', r'\bgo\b', r'\brust\b', r'\bscala\b', 
                    r'\bc\+\+\b', r'\bc#\b', r'\bruby\b', r'\bphp\b', r'\bswift\b'
                ],
                'names': [
                    'Java', 'Kotlin', 'Python', 'JavaScript', 
                    'TypeScript', 'Go', 'Rust', 'Scala',
                    'C++', 'C#', 'Ruby', 'PHP', 'Swift'
                ]
            },
            'frontend': {
                'keywords': [
                    r'\breact\b', r'\bvue\b', r'\bangular\b', r'\bsvelte\b',
                    r'\bnext\.js\b', r'\bnuxt\b', r'\btailwind\b', r'\bbootstrap\b'
                ],
                'names': [
                    'React', 'Vue', 'Angular', 'Svelte',
                    'Next.js', 'Nuxt', 'Tailwind CSS', 'Bootstrap'
                ]
            },
            'backend': {
                'keywords': [
                    r'spring boot\b', r'\bspring\b', r'\bdjango\b', r'\bflask\b',
                    r'\bfastapi\b', r'\bexpress\b', r'\bnode\.js\b', r'\bnestjs\b',
                    r'\blaravel\b', r'\brails\b'
                ],
                'names': [
                    'Spring Boot', 'Spring', 'Django', 'Flask',
                    'FastAPI', 'Express', 'Node.js', 'NestJS',
                    'Laravel', 'Rails'
                ]
            },
            'databases': {
                'keywords': [
                    r'postgresql\b', r'\bmysql\b', r'\bmongodb\b', r'\bredis\b',
                    r'\belasticsearch\b', r'\bcassandra\b', r'\bdynamodb\b',
                    r'\bneo4j\b', r'\bsqlite\b'
                ],
                'names': [
                    'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
                    'Elasticsearch', 'Cassandra', 'DynamoDB',
                    'Neo4j', 'SQLite'
                ]
            },
            'devops': {
                'keywords': [
                    r'\bdocker\b', r'\bkubernetes\b', r'\bterraform\b', r'\bansible\b',
                    r'\bjenkins\b', r'\bgithub actions\b', r'\bgitlab ci\b',
                    r'\bci/cd\b', r'\bhelm\b', r'\bargocd\b'
                ],
                'names': [
                    'Docker', 'Kubernetes', 'Terraform', 'Ansible',
                    'Jenkins', 'GitHub Actions', 'GitLab CI',
                    'CI/CD', 'Helm', 'ArgoCD'
                ]
            },
            'cloud': {
                'keywords': [
                    r'\baws\b', r'\bazure\b', r'\bgcp\b', r'\bec2\b', r'\bs3\b',
                    r'\blambda\b', r'\beks\b', r'\baks\b', r'\bgke\b'
                ],
                'names': [
                    'AWS', 'Azure', 'GCP', 'EC2', 'S3',
                    'Lambda', 'EKS', 'AKS', 'GKE'
                ]
            },
            'other': {
                'keywords': [
                    r'microservices\b', r'\brest api\b', r'\bgraphql\b', r'\bgrpc\b',
                    r'\bkafka\b', r'\bspark\b', r'\bairflow\b', r'\bgit\b'
                ],
                'names': [
                    'Microservices', 'REST API', 'GraphQL', 'gRPC',
                    'Kafka', 'Spark', 'Airflow', 'Git'
                ]
            }
        }
        
        # Extract skills for each category
        extracted_skills = {}
        
        for category, data in skill_categories.items():
            found_skills = []
            for i, keyword_pattern in enumerate(data['keywords']):
                # Use regex to find the skill
                if re.search(keyword_pattern, jd_lower, re.IGNORECASE):
                    skill_name = data['names'][i]
                    # Count occurrences
                    matches = len(re.findall(keyword_pattern, jd_lower, re.IGNORECASE))
                    if matches >= 1:  # Appears at least once
                        found_skills.append((skill_name, matches))
            
            # Sort by frequency
            found_skills.sort(key=lambda x: x[1], reverse=True)
            extracted_skills[category] = [skill for skill, _ in found_skills]
        
        # Log results
        logger.info("\n📊 EXTRACTED SKILLS BY CATEGORY:")
        logger.info("-"*70)
        total_skills = 0
        for category, skills in extracted_skills.items():
            if skills:
                logger.info(f"\n{category.upper()}:")
                for skill in skills:
                    logger.info(f"  • {skill}")
                total_skills += len(skills)
        
        logger.info(f"\n✅ Total skills extracted: {total_skills}")
        logger.info("="*70 + "\n")
        
        return extracted_skills
    
    def generate_targeted_bullets(
        self,
        required_skills: Dict[str, List[str]],
        job_description: str,
        job_title: str,
        company_name: str,
        target_company: str,
        num_bullets: int = 2
    ) -> List[str]:
        """
        Generate targeted experience bullets using required skills.
        
        Args:
            required_skills: Dict of categorized required skills
            job_description: Job description text
            job_title: Current job title
            company_name: Current company name
            target_company: Target company name
            num_bullets: Number of bullets to generate
            
        Returns:
            List of generated bullet points
        """
        logger.info("\n" + "="*70)
        logger.info(f"🤖 GENERATING {num_bullets} TARGETED BULLETS FOR {company_name}")
        logger.info("="*70)
        
        # Flatten top skills from all categories
        top_skills = []
        for category, skills in required_skills.items():
            top_skills.extend(skills[:3])  # Top 3 from each category
        
        top_skills_str = ', '.join(top_skills[:10])  # Use top 10 overall
        
        system_prompt = """You are an expert resume writer specializing in creating impactful, ATS-optimized experience bullets."""
        
        prompt = f"""Generate {num_bullets} NEW experience bullet points for this position that incorporate the required skills.

CURRENT POSITION:
Company: {company_name}
Title: {job_title}

TARGET JOB:
Company: {target_company}
Job Description: {job_description[:2000]}

REQUIRED SKILLS TO INCORPORATE:
{top_skills_str}

CRITICAL REQUIREMENTS:

1. BULLET FORMULA (MUST FOLLOW):
   [Action Verb] + [What You Did] + [How You Did It] + [Impact/Result]
   
   Example:
   "Optimized database queries using indexing and caching strategies, reducing API response time by 45% and improving user experience for 2M+ daily active users"
   
   Components:
   ✅ Specific action: Optimized
   ✅ Technical detail: indexing and caching strategies  
   ✅ Measurable impact: 45% faster
   ✅ Scale context: 2M+ users

2. TEMPLATES TO USE:
   - "[Action Verb] [technical implementation] using [technology/tool], resulting in [quantified impact] for [scale/audience]"
   - "[Built/Developed/Designed] [feature/system] that [solved problem/improved metric], achieving [X% improvement/$ saved/users impacted]"
   - "[Optimized/Refactored/Migrated] [system/codebase] from [old tech] to [new tech], [reducing/improving] [metric] by [X%]"

3. ACTION VERBS:
   Architected, Engineered, Optimized, Deployed, Automated, Built, Designed, 
   Implemented, Scaled, Migrated, Developed, Led, Collaborated

4. REQUIRED SKILLS INTEGRATION:
   - Each bullet MUST include 2-3 skills from: {top_skills_str}
   - Use them naturally in the "How You Did It" part
   - Example: "using Kotlin, Spring Boot, and PostgreSQL"

5. QUANTIFIED IMPACT:
   - Every bullet needs metrics: percentages, numbers, scale
   - Examples: "45% faster", "2M+ users", "99.9% uptime", "$500K saved"

6. OUTPUT FORMAT:
   - Output EXACTLY {num_bullets} bullets
   - Plain text only, one bullet per line
   - NO bullet symbols (•, -, *), NO numbers (1., 2., 3.)
   - Start each with action verb

OUTPUT {num_bullets} BULLETS:"""
        
        response = self.ai_service.generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4
        )
        
        # Parse bullets
        bullets = []
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet markers and numbers
            line = re.sub(r'^[\•\-\*\d\.]+\s*', '', line)
            line = line.strip()
            
            if len(line) > 30:  # Valid bullet
                bullets.append(line)
        
        # Ensure we have exactly num_bullets
        bullets = bullets[:num_bullets]
        
        logger.info(f"\n✅ GENERATED {len(bullets)} BULLETS:")
        logger.info("-"*70)
        for i, bullet in enumerate(bullets, 1):
            logger.info(f"{i}. {bullet}\n")
        logger.info("="*70 + "\n")
        
        return bullets
    
    def insert_bullets_into_experience(
        self,
        original_bullets: List[str],
        new_bullets: List[str]
    ) -> List[str]:
        """
        Insert new bullets at the top of existing experience bullets.
        
        Args:
            original_bullets: Original experience bullets
            new_bullets: New bullets to insert
            
        Returns:
            Combined list with new bullets at top
        """
        return new_bullets + original_bullets
    
    def merge_skills_into_categories(
        self,
        original_skills: str,
        required_skills: Dict[str, List[str]]
    ) -> str:
        """
        Merge required skills into original skills categories.
        
        Args:
            original_skills: Original skills text
            required_skills: Dict of categorized required skills
            
        Returns:
            Updated skills text
        """
        logger.info("\n" + "="*70)
        logger.info("🔧 MERGING REQUIRED SKILLS INTO ORIGINAL CATEGORIES")
        logger.info("="*70)
        
        # Parse original skills
        skill_lines = {}
        for line in original_skills.split('\n'):
            line = line.strip()
            if ':' in line:
                category, skills = line.split(':', 1)
                category = category.strip()
                skills = [s.strip() for s in skills.split(',')]
                skill_lines[category.lower()] = {
                    'category_name': category,
                    'skills': skills
                }
        
        # Map required skills to categories
        category_mapping = {
            'languages': ['Programming & Frameworks', 'Languages'],
            'frontend': ['Programming & Frameworks', 'Frameworks'],
            'backend': ['Programming & Frameworks', 'Frameworks'],
            'databases': ['Databases & APIs', 'Databases'],
            'devops': ['Cloud & DevOps', 'DevOps'],
            'cloud': ['Cloud & DevOps', 'Cloud/Tools'],
            'other': ['Cloud & DevOps', 'Other']
        }
        
        # Add required skills to appropriate categories
        for req_category, req_skills in required_skills.items():
            if not req_skills:
                continue
            
            # Find matching original category
            possible_categories = category_mapping.get(req_category, [])
            matched_category = None
            
            for orig_cat_key, orig_cat_data in skill_lines.items():
                for possible_cat in possible_categories:
                    if possible_cat.lower() in orig_cat_key:
                        matched_category = orig_cat_key
                        break
                if matched_category:
                    break
            
            if matched_category:
                # Add skills at the front if not already present
                existing_skills = [s.lower() for s in skill_lines[matched_category]['skills']]
                new_skills = []
                
                for req_skill in req_skills:
                    if req_skill.lower() not in existing_skills:
                        new_skills.append(req_skill)
                        logger.info(f"  ✅ Adding '{req_skill}' to {skill_lines[matched_category]['category_name']}")
                
                # Insert new skills at front
                skill_lines[matched_category]['skills'] = new_skills + skill_lines[matched_category]['skills']
        
        # Rebuild skills text
        result_lines = []
        for cat_data in skill_lines.values():
            category_name = cat_data['category_name']
            skills_str = ', '.join(cat_data['skills'])
            result_lines.append(f"{category_name}: {skills_str}")
        
        result = '\n'.join(result_lines)
        
        logger.info(f"\n✅ UPDATED SKILLS:")
        logger.info("-"*70)
        logger.info(result)
        logger.info("="*70 + "\n")
        
        return result
