"""
Free Job Scraper - No APIs needed
Scrapes job listings from Ashby by searching Google with advanced bot detection avoidance
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import json
import re
import urllib.parse
import random

class JobScraper:
    def __init__(self):
        self.jobs = []
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
    
    def random_delay(self, min_sec=1, max_sec=3):
        """Add random human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def human_like_mouse_movement(self, page):
        """Simulate human-like mouse movements"""
        try:
            # Random mouse movements
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))
        except:
            pass
    
    def search_google_for_jobs(self, query, max_results=50):
        """Search Google with advanced bot detection avoidance techniques"""
        print(f"Searching Google for: {query}")
        
        with sync_playwright() as p:
            # Launch with stealth options
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                ]
            )
            
            # Random user agent
            user_agent = random.choice(self.user_agents)
            
            # Create context with non-standard viewport (avoid 800x600 detection)
            context = browser.new_context(
                viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                user_agent=user_agent,
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            )
            
            page = context.new_page()
            
            # Advanced stealth scripts
            page.add_init_script("""
                // Overwrite the `navigator.webdriver` property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                            description: "Portable Document Format", 
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        }
                    ]
                });
                
                // Chrome runtime
                window.navigator.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // WebGL vendor
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter.apply(this, [parameter]);
                };
            """)
            
            try:
                # Step 1: Visit Google homepage naturally
                print("  Step 1: Loading Google homepage naturally...")
                page.goto("https://www.google.com", wait_until='networkidle')
                self.random_delay(2, 4)
                
                # Simulate human behavior - move mouse
                self.human_like_mouse_movement(page)
                
                # Accept cookies if present
                try:
                    cookie_buttons = [
                        'button:has-text("Accept all")',
                        'button:has-text("I agree")',
                        'button:has-text("Accept")',
                        '#L2AGLb',  # Google's cookie accept button
                    ]
                    for selector in cookie_buttons:
                        if page.locator(selector).count() > 0:
                            page.locator(selector).first.click()
                            self.random_delay(1, 2)
                            break
                except:
                    pass
                
                # Step 2: Type the search query slowly (human-like)
                print("  Step 2: Typing search query naturally...")
                search_box = page.locator('textarea[name="q"], input[name="q"]').first
                
                # Type character by character with random delays
                for char in query:
                    search_box.type(char, delay=random.randint(50, 150))
                    if random.random() < 0.1:  # 10% chance of small pause
                        time.sleep(random.uniform(0.2, 0.5))
                
                self.random_delay(0.5, 1)
                
                # Press Enter with random delay
                search_box.press('Enter')
                print("  Step 3: Waiting for search results...")
                
                # Wait for results with timeout
                try:
                    page.wait_for_selector('div#search, div.g', timeout=15000)
                except:
                    pass
                
                self.random_delay(2, 3)
                
                # Check for CAPTCHA
                content_text = page.content().lower()
                if 'recaptcha' in content_text or 'unusual traffic' in content_text:
                    print("\n  ⚠️  CAPTCHA detected!")
                    print("  Trying alternative approach: Using DuckDuckGo instead...")
                    browser.close()
                    return self.search_duckduckgo_for_jobs(query)
                
                # Scroll naturally
                print("  Step 4: Scrolling through results...")
                for _ in range(3):
                    scroll_amount = random.randint(300, 600)
                    page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                    self.random_delay(0.8, 1.5)
                    self.human_like_mouse_movement(page)
                
                # Extract content
                content = page.content()
                with open('debug_google.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Debug: Saved HTML to debug_google.html")
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find all links
                all_links = soup.find_all('a', href=True)
                print(f"  Found {len(all_links)} total links")
                
                # Extract Ashby job links
                uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                
                for link in all_links:
                    href = link.get('href', '')
                    
                    # Extract actual URL from Google's redirect
                    actual_url = href
                    if '/url?q=' in href:
                        match = re.search(r'/url\?q=([^&]+)', href)
                        if match:
                            actual_url = urllib.parse.unquote(match.group(1))
                    
                    # Check for Ashby job link
                    if 'jobs.ashbyhq.com' in actual_url and re.search(uuid_pattern, actual_url):
                        job_url = actual_url.split('&')[0]
                        
                        company_match = re.search(r'jobs\.ashbyhq\.com/([^/]+)', job_url)
                        company_name = company_match.group(1).replace('-', ' ').title() if company_match else 'Unknown'
                        
                        title_text = link.get_text(strip=True)
                        if len(title_text) < 5:
                            parent = link.find_parent(['div', 'h3', 'h2'])
                            if parent:
                                h3 = parent.find('h3')
                                title_text = h3.get_text(strip=True) if h3 else parent.get_text(strip=True)
                        
                        title_text = (title_text.split(' - ')[0] if ' - ' in title_text else title_text)[:200]
                        
                        if not title_text or len(title_text) < 5:
                            title_text = f"Position at {company_name}"
                        
                        job_data = {
                            'title': title_text,
                            'company': company_name,
                            'location': 'Remote',
                            'url': job_url,
                            'source': 'Ashby (via Google)'
                        }
                        
                        if not any(j['url'] == job_url for j in self.jobs):
                            self.jobs.append(job_data)
                            print(f"  ✓ {job_data['title']} at {job_data['company']}")
                
                print(f"\n  Found {len(self.jobs)} unique job postings")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
            finally:
                self.random_delay(1, 2)
                browser.close()
        
        return self.jobs
    
    def search_duckduckgo_for_jobs(self, query):
        """Fallback: Search DuckDuckGo (no CAPTCHA)"""
        print(f"\n  === Using DuckDuckGo (CAPTCHA-free alternative) ===")
        print(f"  Searching for: {query}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                user_agent=random.choice(self.user_agents)
            )
            page = context.new_page()
            
            try:
                # DuckDuckGo doesn't use CAPTCHA aggressively
                encoded_query = urllib.parse.quote(query)
                ddg_url = f"https://duckduckgo.com/?q={encoded_query}"
                
                print(f"  URL: {ddg_url}")
                page.goto(ddg_url, wait_until='networkidle')
                time.sleep(3)
                
                # Scroll to load results
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 500)")
                    time.sleep(1)
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find Ashby links
                uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href', '')
                    
                    # DuckDuckGo uses //duckduckgo.com/l/?uddg= redirects
                    if 'uddg=' in href:
                        match = re.search(r'uddg=([^&]+)', href)
                        if match:
                            href = urllib.parse.unquote(match.group(1))
                    
                    if 'jobs.ashbyhq.com' in href and re.search(uuid_pattern, href):
                        job_url = href.split('&')[0]
                        
                        company_match = re.search(r'jobs\.ashbyhq\.com/([^/]+)', job_url)
                        company_name = company_match.group(1).replace('-', ' ').title() if company_match else 'Unknown'
                        
                        title_text = link.get_text(strip=True)[:200]
                        if not title_text or len(title_text) < 5:
                            title_text = f"Position at {company_name}"
                        
                        job_data = {
                            'title': title_text,
                            'company': company_name,
                            'location': 'Remote',
                            'url': job_url,
                            'source': 'Ashby (via DuckDuckGo)'
                        }
                        
                        if not any(j['url'] == job_url for j in self.jobs):
                            self.jobs.append(job_data)
                            print(f"  ✓ {job_data['title']} at {job_data['company']}")
                
                print(f"\n  Found {len(self.jobs)} total jobs via DuckDuckGo")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
            finally:
                time.sleep(2)
                browser.close()
        
        return self.jobs
        """Search Google with a query and extract Ashby job links from results"""
        print(f"Searching Google for: {query}")
        
        with sync_playwright() as p:
            # Use a real browser profile to avoid detection
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            # Hide automation indicators
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.navigator.chrome = {
                    runtime: {}
                };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            try:
                # Go to Google first to set cookies
                print("  Loading Google homepage...")
                page.goto("https://www.google.com", timeout=30000)
                time.sleep(2)
                
                # Accept cookies if prompted
                try:
                    accept_button = page.locator('button:has-text("Accept all"), button:has-text("I agree")')
                    if accept_button.count() > 0:
                        accept_button.first.click()
                        time.sleep(1)
                except:
                    pass
                
                # Now perform the search
                encoded_query = urllib.parse.quote(query)
                google_url = f"https://www.google.com/search?q={encoded_query}&num=50"
                
                print(f"  Searching: {google_url}")
                page.goto(google_url, timeout=30000)
                time.sleep(3)
                
                # Check for CAPTCHA
                content = page.content().lower()
                if 'recaptcha' in content or 'captcha' in content or 'unusual traffic' in content:
                    print("\n  ⚠️  CAPTCHA detected! Please solve it manually in the browser...")
                    print("  Waiting for you to solve the CAPTCHA...")
                    
                    # Wait for user to solve CAPTCHA (wait for search results to appear)
                    try:
                        page.wait_for_selector('div#search, div.g', timeout=120000)  # Wait up to 2 minutes
                        print("  ✓ CAPTCHA solved! Continuing...")
                        time.sleep(2)
                    except:
                        print("  ✗ Timeout waiting for CAPTCHA. Exiting...")
                        return self.jobs
                
                # Save HTML for debugging
                content = page.content()
                with open('debug_google.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Debug: Saved HTML to debug_google.html")
                
                # Scroll to load more results
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find all links in search results
                all_links = soup.find_all('a', href=True)
                print(f"  Total links found: {len(all_links)}")
                
                # Extract Ashby job links
                uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                ashby_links_found = 0
                
                for link in all_links:
                    href = link.get('href', '')
                    
                    # Check for ashbyhq in the raw href first
                    if 'ashbyhq' in href:
                        ashby_links_found += 1
                    
                    # Google wraps URLs in /url?q=... format, extract actual URL
                    actual_url = href
                    if '/url?q=' in href:
                        match = re.search(r'/url\?q=([^&]+)', href)
                        if match:
                            actual_url = urllib.parse.unquote(match.group(1))
                    
                    # Check if this is an Ashby job link
                    if 'jobs.ashbyhq.com' in actual_url and re.search(uuid_pattern, actual_url):
                        # Clean up URL
                        job_url = actual_url.split('&')[0]
                        
                        # Extract company name from URL
                        company_match = re.search(r'jobs\.ashbyhq\.com/([^/]+)', job_url)
                        company_name = company_match.group(1).replace('-', ' ').title() if company_match else 'Unknown'
                        
                        # Try to get job title from the link text or nearby text
                        title_text = link.get_text(strip=True)
                        
                        if len(title_text) < 5:
                            parent = link.find_parent(['div', 'h3', 'h2'])
                            if parent:
                                h3 = parent.find('h3')
                                if h3:
                                    title_text = h3.get_text(strip=True)
                                else:
                                    title_text = parent.get_text(strip=True)
                        
                        title_text = title_text.split(' - ')[0] if ' - ' in title_text else title_text
                        title_text = title_text[:200]
                        
                        if not title_text or len(title_text) < 5:
                            title_text = "Position at " + company_name
                        
                        job_data = {
                            'title': title_text,
                            'company': company_name,
                            'location': 'Remote',
                            'url': job_url,
                            'source': 'Ashby (via Google)'
                        }
                        
                        if not any(j['url'] == job_url for j in self.jobs):
                            self.jobs.append(job_data)
                            print(f"  ✓ {job_data['title']} at {job_data['company']}")
                
                print(f"\n  Debug: Total ashby links in HTML: {ashby_links_found}")
                print(f"  Found {len(self.jobs)} unique job postings")
                
            except Exception as e:
                print(f"  ✗ Error searching Google: {e}")
                import traceback
                traceback.print_exc()
            finally:
                if len(self.jobs) > 0:
                    print("\n  Jobs found! Closing browser in 3 seconds...")
                    time.sleep(3)
                else:
                    input("\n  Press Enter to close browser...")
                browser.close()
        
        return self.jobs
    
    def scrape_ashby_company_page(self, company_url):
        """Scrape a specific company's Ashby job board"""
        print(f"Scraping Ashby page: {company_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Show browser for debugging
            page = browser.new_page()
            
            try:
                page.goto(company_url, timeout=30000)
                time.sleep(5)  # Wait for dynamic content to load
                
                # Scroll to load all jobs
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Save HTML for debugging
                with open('debug_ashby.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Debug: Saved HTML to debug_ashby.html")
                
                # Extract company name from URL or page
                company_name = 'Unknown Company'
                match = re.search(r'jobs\.ashbyhq\.com/([^/]+)', company_url)
                if match:
                    company_name = match.group(1).replace('-', ' ').title()
                
                # Try multiple strategies to find jobs
                # Strategy 1: Look for any links with Ashby job UUID pattern
                all_links = soup.find_all('a', href=True)
                print(f"  Total links found: {len(all_links)}")
                
                uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                
                for link in all_links:
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True)
                    
                    # Check if this looks like a job posting link
                    if re.search(uuid_pattern, href):
                        full_url = href if href.startswith('http') else f'https://jobs.ashbyhq.com{href}'
                        
                        # Skip if it's a navigation or action link
                        if any(skip in link_text.lower() for skip in ['apply', 'back', 'home', 'share']):
                            continue
                        
                        # Get job title
                        title_text = link_text or link.get('aria-label', '') or 'Untitled Position'
                        
                        if len(title_text) > 3 and len(title_text) < 200:
                            job_data = {
                                'title': title_text,
                                'company': company_name,
                                'location': 'Remote',  # Default, will be updated if found
                                'department': 'N/A',
                                'url': full_url,
                                'source': 'Ashby'
                            }
                            
                            # Avoid duplicates
                            if not any(j['url'] == job_data['url'] for j in self.jobs):
                                self.jobs.append(job_data)
                                print(f"  ✓ {job_data['title']}")
                
                jobs_count = len([j for j in self.jobs if j['company'] == company_name])
                print(f"\n  Found {jobs_count} jobs from {company_name}")
                
            except Exception as e:
                print(f"  ✗ Error scraping Ashby: {e}")
                import traceback
                traceback.print_exc()
            finally:
                browser.close()
        
        return self.jobs
    
    def scrape_multiple_ashby_companies(self, company_urls):
        """Scrape multiple Ashby company job boards"""
        print(f"Scraping {len(company_urls)} Ashby company pages...")
        
        for url in company_urls:
            self.scrape_ashby_company_page(url)
            time.sleep(2)  # Be respectful with rate limiting
        
        return self.jobs
    
    def save_jobs(self, filename='jobs.json'):
        """Save scraped jobs to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.jobs, f, indent=2)
        print(f"\nSaved {len(self.jobs)} jobs to {filename}")
    
    def get_jobs(self):
        """Return list of scraped jobs"""
        return self.jobs


if __name__ == '__main__':
    scraper = JobScraper()
    
    # Search Google for Ashby job postings
    print("=== Searching Google for Ashby Job Postings ===\n")
    
    query = 'site:jobs.ashbyhq.com "software engineer" "remote"'
    scraper.search_google_for_jobs(query)
    
    # Save results
    scraper.save_jobs('scraped_jobs.json')
    
    # Print summary
    print(f"\n=== Summary ===")
    print(f"Total jobs found: {len(scraper.get_jobs())}")
    if scraper.get_jobs():
        print("\nAll jobs:")
        for i, job in enumerate(scraper.get_jobs(), 1):
            print(f"{i}. {job['title']} at {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   URL: {job['url']}\n")
    else:
        print("No jobs found. Google might be blocking automated requests.")
        print("Try adding delays or using a proxy.")
