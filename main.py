"""
Main entry point for the job application system using the new modular architecture.
"""

from src.config.settings import Settings
from src.services.job_application_service import JobApplicationService
from src.utils.logger import setup_logging, get_logger

# Initialize logging first
setup_logging(level="INFO")
logger = get_logger(__name__)


def main():
    """
    Main application entry point.
    Runs the complete job application workflow.
    """
    logger.info("="*70)
    logger.info("🤖 AI JOB BIDDER - AUTO APPLICATION SYSTEM")
    logger.info("="*70)
    
    # Load configuration
    settings = Settings.from_json("config.json")
    
    # Initialize job application service
    job_service = JobApplicationService(settings, headless=False)
    
    # Job URL to apply to
    job_url = "https://jobs.ashbyhq.com/rula/1850600a-6c12-413a-b008-ee442f01a592"
    
    logger.info(f"\nTarget: {job_url}\n")
    
    # Run complete application workflow
    result = job_service.apply_to_job(job_url)
    
    # Display result
    if result['success']:
        logger.info("\n✅ Application completed successfully!")
    else:
        logger.error(f"\n❌ Application failed: {result.get('message', 'Unknown error')}")


if __name__ == "__main__":
    main()
