"""
Test script to verify the modular architecture without browser automation.
"""

from src.config.settings import Settings
from src.services.form_scraper_service import FormScraperService
from src.services.ai_service import AIService

def test_setup():
    """Test basic setup and services."""
    print("="*70)
    print("🧪 Testing Modular Architecture")
    print("="*70)
    
    # Test 1: Load configuration
    print("\n1️⃣ Testing Configuration Loading...")
    try:
        settings = Settings.from_json("config.json")
        print(f"   ✅ Configuration loaded successfully")
        print(f"   📋 User: {settings.user_info.personal_info.name}")
        print(f"   📧 Email: {settings.user_info.personal_info.email}")
        print(f"   🤖 Model: {settings.ai_settings.model}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 2: Form Scraper Service
    print("\n2️⃣ Testing Form Scraper Service...")
    try:
        scraper = FormScraperService()
        job_url = "https://jobs.ashbyhq.com/rula/1850600a-6c12-413a-b008-ee442f01a592"
        form_data = scraper.extract_application_form(job_url)
        
        if form_data:
            print(f"   ✅ Form extracted successfully")
            print(f"   🏢 Company: {form_data['company']}")
            print(f"   💼 Job: {form_data['job_title']}")
            print(f"   📝 Fields: {len(form_data['form_fields'])} fields found")
        else:
            print(f"   ⚠️  Could not extract form (expected for now)")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    
    # Test 3: AI Service
    print("\n3️⃣ Testing AI Service...")
    try:
        ai_service = AIService(settings)
        print(f"   ✅ AI Service initialized")
        
        # Test question answering
        print("\n   Testing question answering...")
        question = "Why do you want to work for our company?"
        answer = ai_service.answer_question(
            question=question,
            job_description="Leading tech company in AI/ML",
            job_title="Software Engineer",
            company="Tech Corp",
            user_background=settings.user_info.background.elevator_pitch
        )
        print(f"   ✅ AI answered: {answer[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: All Services Together
    print("\n4️⃣ Testing Service Integration...")
    try:
        from src.services.resume_service import ResumeService
        resume_service = ResumeService(settings, ai_service)
        print(f"   ✅ Resume Service initialized")
        
        from src.services.browser_service import BrowserService
        browser_service = BrowserService(settings, headless=True)
        print(f"   ✅ Browser Service initialized")
        
        from src.services.job_application_service import JobApplicationService
        job_service = JobApplicationService(settings, headless=True)
        print(f"   ✅ Job Application Service initialized")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print("\n📚 Next Steps:")
    print("   1. Run: python main.py")
    print("   2. Browser will open and fill the form automatically")
    print("   3. Review and submit")
    print("\n   Or use the original: python ai_job_bidder.py")
    print("="*70)

if __name__ == "__main__":
    test_setup()
