"""
Job Search UI - Combined job scraping and enrichment tool
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

# Add legacy scripts to path
sys.path.insert(0, str(Path(__file__).parent / "legacy_scripts"))
from scrape_job_details import extract_job_details

# Load environment variables
load_dotenv()

# Get API credentials
API_KEY = os.getenv('GOOGLE_API_KEY')
CX = os.getenv('GOOGLE_CX')


class JobSearchUI:
    """Modern UI for job search and enrichment."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 AI Job Search & Enricher")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Job storage
        self.enriched_jobs = []
        self.is_running = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface."""
        
        # Title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 AI Job Search & Enricher",
            font=("Helvetica", 20, "bold"),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ===== Input Section =====
        input_frame = tk.LabelFrame(
            main_frame,
            text="Search Parameters",
            font=("Helvetica", 12, "bold"),
            bg='white',
            padx=20,
            pady=15
        )
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Search Keyword
        tk.Label(
            input_frame,
            text="Search Keyword:",
            font=("Helvetica", 10, "bold"),
            bg='white'
        ).grid(row=0, column=0, sticky='w', pady=5)
        
        self.keyword_entry = tk.Entry(
            input_frame,
            font=("Helvetica", 11),
            width=40
        )
        self.keyword_entry.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        self.keyword_entry.insert(0, "senior software engineer")
        
        # Job Site
        tk.Label(
            input_frame,
            text="Job Site:",
            font=("Helvetica", 10, "bold"),
            bg='white'
        ).grid(row=1, column=0, sticky='w', pady=5)
        
        self.site_entry = tk.Entry(
            input_frame,
            font=("Helvetica", 11),
            width=40
        )
        self.site_entry.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        self.site_entry.insert(0, "jobs.ashbyhq.com")
        
        # Max Results
        tk.Label(
            input_frame,
            text="Max Results:",
            font=("Helvetica", 10, "bold"),
            bg='white'
        ).grid(row=2, column=0, sticky='w', pady=5)
        
        self.max_results_var = tk.StringVar(value="20")
        max_results_spinbox = tk.Spinbox(
            input_frame,
            from_=5,
            to=100,
            increment=5,
            textvariable=self.max_results_var,
            font=("Helvetica", 11),
            width=10
        )
        max_results_spinbox.grid(row=2, column=1, padx=10, pady=5, sticky='w')
        
        # Search Button
        self.search_btn = tk.Button(
            input_frame,
            text="🔍 Search & Enrich Jobs",
            font=("Helvetica", 12, "bold"),
            bg='#27ae60',
            fg='white',
            activebackground='#229954',
            cursor='hand2',
            command=self.start_search,
            padx=20,
            pady=10
        )
        self.search_btn.grid(row=0, column=2, rowspan=3, padx=20, sticky='ns')
        
        # Configure grid weights
        input_frame.columnconfigure(1, weight=1)
        
        # ===== Progress Section =====
        progress_frame = tk.LabelFrame(
            main_frame,
            text="Progress",
            font=("Helvetica", 12, "bold"),
            bg='white',
            padx=20,
            pady=15
        )
        progress_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 15))
        
        # Progress Bar
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=400
        )
        self.progress.pack(fill=tk.X, pady=5)
        
        # Status Text
        self.status_text = scrolledtext.ScrolledText(
            progress_frame,
            height=8,
            font=("Courier", 9),
            bg='#f8f9fa',
            fg='#2c3e50',
            wrap=tk.WORD
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # ===== Results Section =====
        results_frame = tk.LabelFrame(
            main_frame,
            text="Job Results",
            font=("Helvetica", 12, "bold"),
            bg='white',
            padx=20,
            pady=15
        )
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Results List with Scrollbar
        results_container = tk.Frame(results_frame, bg='white')
        results_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(results_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(
            results_container,
            font=("Courier", 10),
            bg='#f8f9fa',
            fg='#2c3e50',
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set
        )
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)
        
        # Save Button
        self.save_btn = tk.Button(
            results_frame,
            text="💾 Save Results to JSON",
            font=("Helvetica", 11, "bold"),
            bg='#3498db',
            fg='white',
            activebackground='#2980b9',
            cursor='hand2',
            command=self.save_results,
            padx=15,
            pady=8,
            state=tk.DISABLED
        )
        self.save_btn.pack(pady=10)
    
    def log(self, message):
        """Log message to status text."""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def start_search(self):
        """Start the job search process in a separate thread."""
        if self.is_running:
            messagebox.showwarning("Already Running", "A search is already in progress!")
            return
        
        keyword = self.keyword_entry.get().strip()
        site = self.site_entry.get().strip()
        
        if not keyword or not site:
            messagebox.showerror("Missing Input", "Please enter both search keyword and job site!")
            return
        
        if not API_KEY or not CX:
            messagebox.showerror(
                "API Credentials Missing",
                "Please set GOOGLE_API_KEY and GOOGLE_CX in your .env file!"
            )
            return
        
        # Clear previous results
        self.status_text.delete(1.0, tk.END)
        self.results_text.delete(1.0, tk.END)
        self.enriched_jobs = []
        
        # Start search in background thread
        self.is_running = True
        self.search_btn.config(state=tk.DISABLED, text="⏳ Searching...")
        self.save_btn.config(state=tk.DISABLED)
        self.progress.start()
        
        thread = threading.Thread(
            target=self.run_search,
            args=(keyword, site, int(self.max_results_var.get())),
            daemon=True
        )
        thread.start()
    
    def run_search(self, keyword, site, max_results):
        """Run the complete search and enrichment workflow."""
        try:
            # Step 1: Search for job URLs
            self.log(f"{'='*70}")
            self.log(f"🔍 Step 1/3: Searching for jobs...")
            self.log(f"{'='*70}")
            self.log(f"Keyword: {keyword}")
            self.log(f"Site: {site}")
            self.log(f"Max Results: {max_results}")
            self.log("")
            
            query = f'site:{site} "{keyword}" "remote"'
            job_urls = self.search_jobs(query, max_results)
            
            if not job_urls:
                self.log("\n❌ No jobs found!")
                return
            
            self.log(f"\n✅ Found {len(job_urls)} job URLs\n")
            
            # Step 2: Extract job details
            self.log(f"{'='*70}")
            self.log(f"📄 Step 2/3: Extracting job details...")
            self.log(f"{'='*70}\n")
            
            for i, job in enumerate(job_urls, 1):
                self.log(f"[{i}/{len(job_urls)}] {job['url'][:70]}...")
                
                details = extract_job_details(job['url'])
                
                if details:
                    enriched_job = {
                        'url': job['url'],
                        'company': details['company'],
                        'job_title': details['title'],
                        'location': details['location'],
                        'job_type': details['job_type'],
                        'employment_type': details['employment_type'],
                        'salary': details['salary'],
                        'date_posted': details['date_posted'],
                        'description': details['description'],
                        'search_title': job.get('title'),
                        'search_snippet': job.get('snippet')
                    }
                    self.enriched_jobs.append(enriched_job)
                    self.log(f"  ✅ {details['company']} - {details['title']}")
                else:
                    self.log(f"  ⚠️  Failed to extract details")
                
                # Delay between requests
                if i < len(job_urls):
                    time.sleep(1.5)
            
            # Step 3: Display results
            self.log(f"\n{'='*70}")
            self.log(f"✅ Step 3/3: Displaying results...")
            self.log(f"{'='*70}\n")
            self.log(f"Successfully enriched {len(self.enriched_jobs)} jobs!")
            
            self.display_results()
            
        except Exception as e:
            self.log(f"\n❌ Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        finally:
            self.is_running = False
            self.progress.stop()
            self.search_btn.config(state=tk.NORMAL, text="🔍 Search & Enrich Jobs")
            if self.enriched_jobs:
                self.save_btn.config(state=tk.NORMAL)
    
    def search_jobs(self, query, max_results):
        """Search Google for job URLs using Custom Search API."""
        all_urls = []
        results_per_page = 10
        num_requests = min((max_results + results_per_page - 1) // results_per_page, 10)
        
        for page in range(num_requests):
            start_index = page * results_per_page + 1
            
            url = 'https://www.googleapis.com/customsearch/v1'
            params = {
                'key': API_KEY,
                'cx': CX,
                'q': query,
                'num': results_per_page,
                'start': start_index
            }
            
            self.log(f"Fetching page {page + 1}/{num_requests}...")
            
            try:
                response = requests.get(url, params=params)
                
                if response.status_code != 200:
                    self.log(f"Error: {response.status_code}")
                    break
                
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    self.log(f"No more results at page {page + 1}")
                    break
                
                for item in items:
                    all_urls.append({
                        'url': item['link'],
                        'title': item.get('title', 'N/A'),
                        'snippet': item.get('snippet', 'N/A')
                    })
                
                self.log(f"  ✓ Found {len(items)} results")
                
                # Check if we've reached the end
                search_info = data.get('searchInformation', {})
                total_results = int(search_info.get('totalResults', 0))
                
                if start_index + results_per_page > total_results:
                    break
                
            except Exception as e:
                self.log(f"Error on page {page + 1}: {e}")
                break
        
        return all_urls
    
    def display_results(self):
        """Display enriched jobs in the results area."""
        self.results_text.delete(1.0, tk.END)
        
        for i, job in enumerate(self.enriched_jobs, 1):
            result = f"\n{'='*80}\n"
            result += f"Job {i}/{len(self.enriched_jobs)}\n"
            result += f"{'='*80}\n\n"
            result += f"🏢 Company: {job['company']}\n"
            result += f"💼 Title: {job['job_title']}\n"
            result += f"📍 Location: {job['location']}\n"
            result += f"💰 Salary: {job['salary']}\n"
            result += f"📅 Posted: {job['date_posted']}\n"
            result += f"🔗 URL: {job['url']}\n"
            result += f"\n📝 Type: {job['job_type']} | {job['employment_type']}\n"
            
            if job['description']:
                desc = job['description'][:300]
                result += f"\n📄 Description:\n{desc}...\n"
            
            result += "\n"
            
            self.results_text.insert(tk.END, result)
        
        self.results_text.insert(tk.END, f"\n{'='*80}\n")
        self.results_text.insert(tk.END, f"Total: {len(self.enriched_jobs)} jobs found\n")
        self.results_text.insert(tk.END, f"{'='*80}\n")
    
    def save_results(self):
        """Save enriched jobs to JSON file."""
        if not self.enriched_jobs:
            messagebox.showwarning("No Data", "No jobs to save!")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enriched_jobs_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.enriched_jobs, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo(
                "Success",
                f"Saved {len(self.enriched_jobs)} jobs to:\n{filename}"
            )
            self.log(f"\n💾 Saved results to: {filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")


def main():
    """Launch the application."""
    root = tk.Tk()
    app = JobSearchUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
