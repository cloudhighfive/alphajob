"""
Process Remote Jobs and Generate Applications
Filters enriched_jobs.json for Remote positions and generates tailored applications.
"""

import json
from ai_job_bidder import AIJobBidder
from pathlib import Path
import time

def load_enriched_jobs(filepath="enriched_jobs.json"):
    """Load enriched jobs from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def filter_remote_jobs(jobs):
    """Filter for Remote jobs only."""
    return [job for job in jobs if job.get('job_type') == 'Remote']

def get_applied_companies(tailored_dir="resumes/tailored"):
    """
    Get list of companies we've already applied to by checking folder names.
    Returns set of company names (normalized - lowercase, no special chars).
    """
    import re
    tailored_path = Path(tailored_dir)
    if not tailored_path.exists():
        return set()
    
    applied_companies = set()
    for folder in tailored_path.iterdir():
        if folder.is_dir() and folder.name != '.DS_Store':
            # Folder name format: Company_Name_Job_Title
            # Extract company by finding common job title keywords
            folder_name = folder.name
            
            # Job title keywords that indicate where job title starts
            job_keywords = ['Software', 'Engineer', 'Developer', 'Manager', 'Director', 
                           'Senior', 'Junior', 'Lead', 'Principal', 'Staff', 'Intern',
                           'Architect', 'Analyst', 'Consultant', 'Specialist']
            
            # Find where job title starts
            company_parts = []
            parts = folder_name.split('_')
            for part in parts:
                # Check if this part starts a job title
                if any(keyword in part for keyword in job_keywords):
                    break
                company_parts.append(part)
            
            if company_parts:
                # Reconstruct company name and normalize
                company_name = '_'.join(company_parts).lower()
                applied_companies.add(company_name)
    
    return applied_companies

def main():
    """Main processing function."""
    print("="*70)
    print("🚀 Remote Job Application Generator")
    print("="*70)
    
    # Load jobs
    print("\n📊 Loading enriched jobs...")
    all_jobs = load_enriched_jobs()
    print(f"   Total jobs: {len(all_jobs)}")
    
    # Filter for remote
    remote_jobs = filter_remote_jobs(all_jobs)
    print(f"   Remote jobs: {len(remote_jobs)}")
    
    # Get companies we've already applied to
    applied_companies = get_applied_companies()
    if applied_companies:
        print(f"   Already applied to {len(applied_companies)} companies (will skip)")
    
    # Filter out companies we've already applied to
    filtered_jobs = []
    skipped = 0
    for job in remote_jobs:
        company = job.get('company', '')
        # Normalize company name for comparison
        import re
        normalized_company = re.sub(r'[^\w\s-]', '', company).strip().replace(' ', '_').lower()
        
        if normalized_company not in applied_companies:
            filtered_jobs.append(job)
        else:
            skipped += 1
    
    print(f"   After filtering duplicates: {len(filtered_jobs)} jobs")
    if skipped > 0:
        print(f"   Skipped {skipped} jobs (already applied to company)")
    
    if not filtered_jobs:
        print("\n❌ No new jobs to apply to!")
        return
    
    remote_jobs = filtered_jobs  # Use filtered list
    
    if not remote_jobs:
        print("\n❌ No remote jobs found!")
        return
    
    # Initialize AI Job Bidder
    bidder = AIJobBidder('config.json')
    
    # Ask user how many jobs to process
    print(f"\n📝 Ready to process {len(remote_jobs)} remote jobs")
    user_input = input(f"   How many jobs to process? (1-{len(remote_jobs)}, or 'all'): ").strip()
    
    if user_input.lower() == 'all':
        num_jobs = len(remote_jobs)
    else:
        try:
            num_jobs = int(user_input)
            num_jobs = min(num_jobs, len(remote_jobs))
        except ValueError:
            print("   Invalid input, processing 1 job")
            num_jobs = 1
    
    print(f"\n🔄 Processing {num_jobs} remote job(s)...\n")
    
    # Process jobs
    successful = 0
    failed = 0
    
    for i, job in enumerate(remote_jobs[:num_jobs], 1):
        print(f"\n{'='*70}")
        print(f"Job {i}/{num_jobs}")
        print(f"{'='*70}")
        print(f"Company: {job.get('company', 'Unknown')}")
        print(f"Title: {job.get('job_title', 'Unknown')}")
        print(f"Location: {job.get('location', 'Unknown')}")
        print(f"URL: {job.get('url', 'Unknown')}")
        
        try:
            # Extract application form
            form_data = bidder.extract_application_form(job['url'])
            
            if not form_data:
                print(f"⚠️  Could not extract form, skipping...\n")
                failed += 1
                continue
            
            # Fill application
            filled_data = bidder.fill_application(form_data)
            
            # Save to file
            output_dir = Path("applications")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = filled_data['timestamp'].replace(':', '-').replace('.', '-')
            safe_company = job.get('company', 'Unknown').replace(' ', '_')
            filename = f"{safe_company}_{timestamp}.json"
            
            output_path = output_dir / filename
            with open(output_path, 'w') as f:
                json.dump(filled_data, f, indent=2)
            
            print(f"\n✅ Application saved to: {output_path}")
            successful += 1
            
            # Rate limiting - wait between jobs
            if i < num_jobs:
                print("\n⏳ Waiting 2 seconds before next job...")
                time.sleep(2)
                
        except Exception as e:
            print(f"\n❌ Error processing job: {e}")
            failed += 1
            continue
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 Processing Summary")
    print(f"{'='*70}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Applications saved to: ./applications/")
    print(f"📄 Tailored resumes saved to: ./resumes/tailored/")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
