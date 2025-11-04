"""
AI Service for interacting with Ollama LLM.
"""

import ollama
from typing import Dict, List, Optional, Union
import json
import re

from src.config import Settings
from src.utils.logger import get_logger


logger = get_logger(__name__)


class AIService:
    """Service for AI/LLM interactions using Ollama."""
    
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
        logger.info(f"Initialized AIService with model: {self.model}")
    
    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate completion using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            
        Returns:
            Generated text response
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={"temperature": temperature or self.temperature}
            )
            
            return response['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"AI generation error: {str(e)}")
            raise
    
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
        prompt = f"""
Tailor this professional summary for a {job_title} position at {company}.

Original Summary:
{original_summary}

Job Description:
{job_description}

Requirements:
- Emphasize relevant skills and experience that match the job description
- Keep it concise (2-3 sentences)
- Maintain professional tone
- Don't add skills not in the original summary
- Return ONLY the tailored summary, no explanations

Tailored Summary:"""
        
        logger.info(f"Tailoring summary for {job_title} at {company}")
        return self.generate_completion(prompt)
    
    def tailor_skills_section(
        self,
        original_skills: str,
        job_description: str,
        job_title: str
    ) -> str:
        """
        Tailor skills section for specific job.
        
        Args:
            original_skills: Original skills text
            job_description: Job description
            job_title: Job title
            
        Returns:
            Tailored skills text
        """
        prompt = f"""
Reorder and emphasize skills from the original list that best match this {job_title} position.

Original Skills:
{original_skills}

Job Description:
{job_description}

Requirements:
- Prioritize skills mentioned in the job description
- Keep ALL skills from the original list
- Only reorder, don't add new skills
- Return in the same format as the original
- No explanations, just the reordered skills

Tailored Skills:"""
        
        logger.info(f"Tailoring skills for {job_title}")
        return self.generate_completion(prompt)
    
    def tailor_work_experience(
        self,
        job_title: str,
        company: str,
        bullets: List[str],
        target_job_description: str,
        target_job_title: str
    ) -> List[str]:
        """
        Tailor work experience bullets for specific job.
        
        Args:
            job_title: Original job title
            company: Company name
            bullets: Original bullet points
            target_job_description: Target job description
            target_job_title: Target job title
            
        Returns:
            List of tailored bullet points
        """
        bullets_text = "\n".join(f"• {bullet}" for bullet in bullets)
        
        prompt = f"""
Tailor these work experience bullets for a {target_job_title} application.

Position: {job_title} at {company}
Original Bullets:
{bullets_text}

Target Job Description:
{target_job_description}

Requirements:
- Emphasize achievements relevant to the target job
- Keep the same number of bullets
- Maintain factual accuracy
- Use strong action verbs
- Include metrics where possible
- Return as a simple list, one bullet per line, starting with "•"
- No explanations

Tailored Bullets:"""
        
        logger.info(f"Tailoring experience bullets for {job_title} at {company}")
        response = self.generate_completion(prompt)
        
        # Parse bullets from response
        tailored_bullets = []
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('•') or line.startswith('-'):
                bullet = line.lstrip('•-').strip()
                if bullet:
                    tailored_bullets.append(bullet)
        
        return tailored_bullets if tailored_bullets else bullets
    
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
- Return only the answer, no additional commentary

Answer:"""
        
        answer = self.generate_completion(prompt)
        logger.info(f"         🤖 AI generated answer ({len(answer)} chars)")
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
        
        # Get user background from settings
        user_background = self.settings.user_info.background.elevator_pitch
        
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
