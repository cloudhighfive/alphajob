"""
Browser automation service using Playwright.
"""

from typing import Dict, Optional, List
from pathlib import Path
import time
import random
import signal

from src.config.settings import Settings
from src.utils.logger import get_logger
from src.utils.paths import (
    get_pre_submit_screenshot_path,
    get_post_submit_screenshot_path,
    get_form_debug_screenshot_path,
    get_form_html_debug_path
)

logger = get_logger(__name__)


class BrowserService:
    """Handle browser automation for form filling using Playwright."""
    
    def __init__(self, settings: Settings, headless: bool = False):
        """
        Initialize browser service.
        
        Args:
            settings: Application settings
            headless: If True, run browser in headless mode
        """
        self.settings = settings
        self.headless = headless
        self.auto_submit = True  # Set to False to require manual submission
        
        logger.info(f"Browser service initialized (headless={headless})")
    
    def submit_application(
        self,
        job_url: str,
        filled_data: Dict,
        form_fields: List[Dict],
        resume_path: Optional[str] = None
    ) -> Dict:
        """
        Submit filled application using Playwright browser automation.
        
        Args:
            job_url: URL of the job posting
            filled_data: Filled application data (field_path -> value mapping)
            form_fields: List of form field definitions
            resume_path: Path to resume file for upload
            
        Returns:
            Dict with submission status
        """
        logger.info("="*70)
        logger.info("🤖 Submitting application with browser automation...")
        logger.info("="*70)
        
        try:
            from playwright.sync_api import sync_playwright
            
            logger.info(f"   🌐 Initializing Playwright...")
            logger.info(f"   📄 Resume file: {Path(resume_path).name if resume_path else 'None'}")
            logger.info(f"   📊 Fields to fill: {len(filled_data)}")
            
            with sync_playwright() as p:
                try:
                    logger.info(f"   🚀 Launching Chromium browser (headless={self.headless})...")
                    
                    # Use simple browser launch (not persistent context)
                    browser = p.chromium.launch(
                        headless=self.headless,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--disable-dev-shm-usage',
                            '--no-first-run',
                            '--no-default-browser-check',
                            '--disable-background-timer-throttling',
                            '--disable-backgrounding-occluded-windows',
                            '--disable-renderer-backgrounding',
                        ]
                    )
                    
                    # Create a clean context with realistic settings
                    browser_context = browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        locale='en-US',
                        timezone_id='America/New_York',
                        permissions=[],
                        geolocation=None,
                        color_scheme='light'
                    )
                    
                    page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
                    logger.info(f"   ✅ Browser ready")
                    
                    # Inject anti-detection scripts
                    logger.info(f"   🔒 Injecting stealth scripts...")
                    self._inject_stealth_scripts(page)
                    logger.info(f"   ✅ Stealth mode activated")
                    
                    # Navigate to job page
                    logger.info(f"   🌐 Navigating to job page...")
                    self._navigate_to_job(page, job_url)
                    
                    # Click Apply button if needed
                    logger.info(f"   🔍 Looking for Apply button...")
                    self._click_apply_button(page)
                    
                    # Fill form fields
                    logger.info(f"   📝 Filling form fields...")
                    self._fill_form_fields(page, filled_data, form_fields, resume_path)
                    
                    # Fill additional EEO fields
                    logger.info(f"   🏢 Filling EEO fields...")
                    self._fill_eeo_fields(page)
                    
                    # Take pre-submit screenshot
                    pre_submit_path = get_pre_submit_screenshot_path()
                    page.screenshot(path=str(pre_submit_path), full_page=True)
                    logger.info(f"   ✅ Pre-submit screenshot: {pre_submit_path}")
                    
                    # Submit or manual review
                    if not self.auto_submit:
                        result = self._manual_submit(browser_context, browser)
                    else:
                        result = self._auto_submit(page, browser_context, browser)
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"   ⚠️  Browser context error: {e}")
                    try:
                        browser_context.close()
                        browser.close()
                    except:
                        pass
                    raise
                    
        except ImportError:
            logger.error("   ❌ Playwright not installed")
            logger.error("   Run: pip install playwright && playwright install chromium")
            return {
                'status': 'error',
                'success': False,
                'message': 'Playwright not installed'
            }
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            return {
                'status': 'error',
                'success': False,
                'message': str(e)
            }
    
    def _inject_stealth_scripts(self, page):
        """Inject comprehensive anti-detection scripts."""
        page.add_init_script("""
            // Remove webdriver property completely
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
                configurable: true
            });
            
            // Delete automation flags
            delete navigator.__proto__.webdriver;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            
            // Mock chrome object with comprehensive properties
            window.chrome = {
                runtime: {
                    OnInstalledReason: {
                        INSTALL: 'install',
                        UPDATE: 'update',
                        CHROME_UPDATE: 'chrome_update',
                        SHARED_MODULE_UPDATE: 'shared_module_update'
                    },
                    OnRestartRequiredReason: {
                        APP_UPDATE: 'app_update',
                        OS_UPDATE: 'os_update',
                        PERIODIC: 'periodic'
                    },
                    PlatformArch: {
                        ARM: 'arm',
                        X86_32: 'x86-32',
                        X86_64: 'x86-64'
                    },
                    PlatformOs: {
                        ANDROID: 'android',
                        CROS: 'cros',
                        LINUX: 'linux',
                        MAC: 'mac',
                        OPENBSD: 'openbsd',
                        WIN: 'win'
                    },
                    RequestUpdateCheckStatus: {
                        THROTTLED: 'throttled',
                        NO_UPDATE: 'no_update',
                        UPDATE_AVAILABLE: 'update_available'
                    }
                },
                loadTimes: function() {},
                csi: function() {},
                app: {
                    isInstalled: false,
                    InstallState: {
                        DISABLED: 'disabled',
                        INSTALLED: 'installed',
                        NOT_INSTALLED: 'not_installed'
                    },
                    RunningState: {
                        CANNOT_RUN: 'cannot_run',
                        READY_TO_RUN: 'ready_to_run',
                        RUNNING: 'running'
                    }
                }
            };
            
            // Mock permissions with more realistic behavior
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock plugins with comprehensive list
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format'},
                        description: 'Portable Document Format',
                        filename: 'internal-pdf-viewer',
                        length: 1,
                        name: 'Chrome PDF Plugin'
                    },
                    {
                        0: {type: 'application/pdf', suffixes: 'pdf', description: ''},
                        description: '',
                        filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                        length: 1,
                        name: 'Chrome PDF Viewer'
                    },
                    {
                        0: {type: 'application/x-nacl', suffixes: '', description: 'Native Client Executable'},
                        1: {type: 'application/x-pnacl', suffixes: '', description: 'Portable Native Client Executable'},
                        description: '',
                        filename: 'internal-nacl-plugin',
                        length: 2,
                        name: 'Native Client'
                    }
                ],
                configurable: true
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true
            });
            
            // Mock hardware properties
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8,
                configurable: true
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8,
                configurable: true
            });
            
            // Override toString to hide proxies
            const originalToString = Function.prototype.toString;
            Function.prototype.toString = function() {
                if (this === navigator.permissions.query) {
                    return 'function query() { [native code] }';
                }
                return originalToString.apply(this, arguments);
            };
            
            // Mock WebGL vendor/renderer
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
            
            // Add realistic screen properties
            Object.defineProperty(screen, 'availTop', {
                get: () => 0,
                configurable: true
            });
            
            // Mock connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false,
                    onchange: null
                }),
                configurable: true
            });
            
            // Override Date.prototype.getTimezoneOffset
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {
                return -300; // EST timezone
            };
            
            // Mock battery API
            if (!navigator.getBattery) {
                navigator.getBattery = () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1,
                    addEventListener: () => {},
                    removeEventListener: () => {},
                    dispatchEvent: () => true
                });
            }
        """)
    
    def _navigate_to_job(self, page, job_url: str):
        """Navigate to job posting page with retry logic."""
        logger.info(f"   ⏳ Loading job page...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                page.goto(job_url, timeout=60000)
                page.wait_for_load_state('networkidle', timeout=30000)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"   ⚠️  Attempt {attempt + 1} failed, retrying...")
                else:
                    raise
    
    def _click_apply_button(self, page):
        """Look for and click Apply button if it exists."""
        logger.info(f"   🔍 Looking for Apply button...")
        
        apply_button_selectors = [
            'button:has-text("Apply")',
            'a:has-text("Apply")',
            '[data-testid="apply-button"]',
            '.apply-button',
            'button:has-text("Submit Application")'
        ]
        
        apply_clicked = False
        for selector in apply_button_selectors:
            try:
                if page.locator(selector).count() > 0:
                    button = page.locator(selector).first
                    button.click()
                    logger.info(f"   ✅ Clicked Apply button")
                    apply_clicked = True
                    page.wait_for_load_state('networkidle')
                    break
            except:
                continue
        
        if not apply_clicked:
            logger.info(f"   ℹ️  No Apply button found (form may already be visible)")
        
        # Wait for form to be visible
        try:
            page.wait_for_selector('input, textarea, select', timeout=5000)
        except:
            # Try to find and click Apply button again
            logger.warning(f"   ⚠️  No form fields detected, looking for Apply button...")
            
            apply_selectors = [
                'button:has-text("Apply for this job")',
                'button:has-text("Apply")',
                'a:has-text("Apply for this job")',
                'a:has-text("Apply")',
                '[data-testid*="apply"]',
                'button[type="button"]:has-text("Apply")',
                '.apply-button',
                '#apply-button'
            ]
            
            for selector in apply_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        logger.info(f"   🎯 Found Apply button with selector: {selector}")
                        page.locator(selector).first.click()
                        logger.info(f"   ✅ Clicked Apply button, waiting for form...")
                        page.wait_for_load_state('networkidle')
                        
                        try:
                            page.wait_for_selector('input, textarea, select', timeout=5000)
                            logger.info(f"   ✅ Form fields now visible!")
                        except:
                            pass
                        break
                except Exception as e:
                    continue
        
        # Take debug screenshot
        debug_path = get_form_debug_screenshot_path()
        page.screenshot(path=str(debug_path), full_page=True)
        logger.info(f"   📸 Debug screenshot saved: {debug_path}")
        
        # Save HTML for debugging
        html_path = get_form_html_debug_path()
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(page.content())
        logger.info(f"   📄 Saved page HTML for debugging: {html_path}")
    
    def _fill_form_fields(self, page, filled_data: Dict, form_fields: List[Dict], resume_path: Optional[str]):
        """Fill all form fields with advanced human-like anti-spam strategies."""
        logger.info(f"   📝 Starting to fill {len(form_fields)} form fields...")

        boolean_yes_clicks = 0
        boolean_no_clicks = 0
        filled_count = 0
        skipped_count = 0
        error_count = 0

        # Randomize field order and simulate skipping/returning
        field_indices = list(range(len(form_fields)))
        random.shuffle(field_indices)
        skip_chance = 0.15  # 15% chance to skip a field and return later
        skipped_fields = []

        def simulate_mouse_hover_and_scroll():
            """Simulate human-like mouse movement with Bezier curves for organic motion."""
            width = page.viewport_size['width'] if page.viewport_size else 1920
            height = page.viewport_size['height'] if page.viewport_size else 1080
            
            # Get current mouse position (or start from random)
            start_x = random.randint(0, width-1)
            start_y = random.randint(0, height-1)
            end_x = random.randint(0, width-1)
            end_y = random.randint(0, height-1)
            
            # Use Bezier curve for organic mouse movement
            steps = random.randint(15, 40)
            for step in range(steps):
                t = step / steps
                # Cubic Bezier curve with random control points
                control1_x = start_x + random.randint(-100, 100)
                control1_y = start_y + random.randint(-100, 100)
                control2_x = end_x + random.randint(-100, 100)
                control2_y = end_y + random.randint(-100, 100)
                
                # Bezier formula: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
                x = int((1-t)**3 * start_x + 3*(1-t)**2*t * control1_x + 3*(1-t)*t**2 * control2_x + t**3 * end_x)
                y = int((1-t)**3 * start_y + 3*(1-t)**2*t * control1_y + 3*(1-t)*t**2 * control2_y + t**3 * end_y)
                
                # Clamp to viewport
                x = max(0, min(width-1, x))
                y = max(0, min(height-1, y))
                
                page.mouse.move(x, y)
                page.wait_for_timeout(random.randint(5, 20))
            
            # Random scroll
            if random.random() < 0.5:
                scroll_y = random.randint(0, height)
                page.evaluate(f"window.scrollTo(0, {scroll_y})")
            # Random hover/click
            if random.random() < 0.2:
                page.mouse.click(end_x, end_y, delay=random.randint(20, 120))
            page.wait_for_timeout(random.randint(100, 400))

        def focus_and_blur(element):
            try:
                element.focus()
                page.wait_for_timeout(random.randint(80, 200))
                if random.random() < 0.2:
                    element.blur()
                    page.wait_for_timeout(random.randint(50, 120))
                    element.focus()
            except Exception:
                pass

        def human_type(element, text):
            """Type with realistic human behavior: random delays, typos, corrections."""
            typo_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
            text_list = list(text)
            i = 0
            
            while i < len(text_list):
                char = text_list[i]
                delay = random.randint(30, 120)
                
                # Occasionally make a typo (5% chance)
                if random.random() < 0.05 and char.lower() in typo_chars:
                    # Type wrong character
                    wrong_char = random.choice(typo_chars)
                    element.type(wrong_char, delay=delay)
                    page.wait_for_timeout(random.randint(100, 300))
                    # Backspace to correct
                    element.press('Backspace')
                    page.wait_for_timeout(random.randint(50, 150))
                    # Type correct character
                    element.type(char, delay=delay)
                else:
                    # Type normally
                    element.type(char, delay=delay)
                
                # Mid-word pause
                if i > 0 and i % random.randint(4, 8) == 0 and random.random() < 0.25:
                    page.wait_for_timeout(random.randint(200, 600))
                
                i += 1

        i = 0
        while i < len(field_indices):
            idx = field_indices[i]
            field = form_fields[idx]
            field_path = field['path']
            field_title = field['title']
            field_type = field['type']
            value = filled_data.get(field_path)

            logger.info(f"      � {field_title} ({field_type})")

            if value is None:
                logger.warning(f"         ⏭️  Skipped (no value)")
                skipped_count += 1
                i += 1
                continue

            if len(str(value)) > 80:
                logger.info(f"         � Value: {str(value)[:77]}...")
            else:
                logger.info(f"         💬 Value: {value}")

            try:
                element = self._find_form_element(page, field, field_path, field_title, field_type)
                if element and element.count() > 0:
                    simulate_mouse_hover_and_scroll()
                    focus_and_blur(element)
                    # Randomly skip and return to this field
                    if random.random() < skip_chance and idx not in skipped_fields:
                        logger.info(f"         ⏭️  Simulating human skip, will return later...")
                        skipped_fields.append(idx)
                        field_indices.append(idx)
                        i += 1
                        continue
                    if field_type == 'File':
                        self._fill_file_field(element, resume_path, field_title)
                        filled_count += 1
                    elif field_type == 'Boolean':
                        boolean_yes_clicks, boolean_no_clicks = self._fill_boolean_field(
                            page, element, value, field_title, boolean_yes_clicks, boolean_no_clicks
                        )
                        filled_count += 1
                    elif field_type == 'Location':
                        self._fill_location_field(page, element, value, field_title)
                        filled_count += 1
                    elif field_type in ['ValueSelect', 'MultiValueSelect']:
                        self._fill_select_field(page, element, value, field_type, field_title)
                        filled_count += 1
                    elif field_type in ['Text', 'Textarea', 'Input']:
                        # Use human_type for text fields
                        element.scroll_into_view_if_needed()
                        time.sleep(random.uniform(0.2, 0.5))
                        element.click()
                        time.sleep(random.uniform(0.3, 0.6))
                        element.fill('')
                        time.sleep(0.1)
                        human_type(element, str(value))
                        time.sleep(random.uniform(0.3, 0.7))
                        filled_value = element.input_value()
                        expected_length = len(str(value))
                        actual_length = len(filled_value) if filled_value else 0
                        if actual_length >= expected_length - 10:
                            logger.info(f"      ✅ Filled: {field_title} ({actual_length}/{expected_length} chars)")
                        else:
                            logger.warning(f"      ⚠️  Incomplete fill: {field_title} ({actual_length}/{expected_length} chars)")
                        filled_count += 1
                    else:
                        self._fill_text_field(element, value, field_title)
                        filled_count += 1
                    
                    # Context-aware pause: longer for complex fields, shorter for simple
                    pause_time = self._calculate_context_aware_pause(field_type, str(value), field_title)
                    page.wait_for_timeout(pause_time)
                    
                    # Occasionally scroll back up to review (simulate re-reading)
                    if random.random() < 0.15 and i > 3:
                        logger.info(f"         🔄 Simulating re-reading behavior...")
                        current_scroll = page.evaluate("window.scrollY")
                        scroll_back = random.randint(200, 600)
                        page.evaluate(f"window.scrollTo(0, {max(0, current_scroll - scroll_back)})")
                        page.wait_for_timeout(random.randint(800, 2000))
                        page.evaluate(f"window.scrollTo(0, {current_scroll})")
                        page.wait_for_timeout(random.randint(300, 700))
                else:
                    logger.warning(f"         ⚠️  Element not found")
                    error_count += 1
            except Exception as e:
                logger.error(f"         ❌ Error: {str(e)[:80]}")
                error_count += 1
            i += 1

        # Summary
        logger.info(f"\n   📊 Field filling summary:")
        logger.info(f"      ✅ Filled: {filled_count}")
        logger.info(f"      ⏭️  Skipped: {skipped_count}")
        logger.info(f"      ❌ Errors: {error_count}")
    
    def _calculate_context_aware_pause(self, field_type: str, value: str, field_title: str) -> int:
        """Calculate realistic pause time based on field complexity."""
        base_pause = 400
        
        # Complex fields need longer thinking time
        if field_type == 'Textarea':
            # Long text needs more thinking
            base_pause = 800 + len(value) * 2
        elif field_type in ['ValueSelect', 'MultiValueSelect']:
            # Dropdowns need time to read options
            base_pause = 600
        elif field_type == 'Boolean':
            # Yes/No questions are quick
            base_pause = 300
        elif field_type == 'File':
            # File upload is quick once selected
            base_pause = 500
        elif field_type == 'Location':
            # Location needs time to think about address
            base_pause = 700
        else:
            # Text fields: longer for complex questions
            if any(word in field_title.lower() for word in ['experience', 'why', 'describe', 'explain']):
                base_pause = 1000
            elif len(value) > 100:
                base_pause = 600
        
        # Add randomness to make it more human
        variance = random.randint(-200, 400)
        return max(200, base_pause + variance)
    
    
    def _find_form_element(self, page, field: Dict, field_path: str, field_title: str, field_type: str):
        """Find form element using multiple robust strategies to combat masked/randomized classes."""
        element = None
        
        # Build selectors based on field type
        if field_type == 'File':
            selectors = [
                'input[type="file"]',
                '[data-testid*="resume"]',
                '[data-testid*="upload"]',
                'button:has-text("Upload") + input[type="file"]'
            ]
        elif field_type == 'Boolean':
            selectors = [
                f'input[type="checkbox"][name="{field_path.lower()}"]',
                f'input[type="checkbox"][name="{field_path}"]',
                f'input[type="checkbox"][id*="{field_path.lower()}"]',
            ]
        elif field_type == 'Location':
            selectors = [
                'input[placeholder="Start typing..."]',
                'input[placeholder*="Start typing" i]',
                'input[placeholder*="location" i]',
                'input[placeholder*="city" i]',
                'input[aria-label*="location" i]',
                f'[id="{field_path.lower()}"]' if field_path else None,
                f'[name="{field_path.lower()}"]' if field_path else None,
            ]
            selectors = [s for s in selectors if s]
        else:
            selectors = [
                f'input[placeholder*="{field_title}" i]',
                f'textarea[placeholder*="{field_title}" i]',
                f'input[aria-label*="{field_title}" i]',
                f'textarea[aria-label*="{field_title}" i]',
            ]
            
            if field_path:
                selectors.extend([
                    f'[id="{field_path.lower()}"]',
                    f'[name="{field_path.lower()}"]',
                    f'[id="{field_path}"]',
                    f'[name="{field_path}"]',
                ])
        
        # Try each selector
        for selector in selectors:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    logger.info(f"         ✓ Found with selector: {selector} (count: {count})")
                    element = page.locator(selector).first
                    break
            except:
                continue
        
        # Enhanced fallback strategies for masked/randomized elements
        if not element:
            # Strategy 1: Label-based with nearby input
            try:
                labels = page.locator(f'text="{field_title}" >> xpath=..')
                if labels.count() > 0:
                    parent = labels.first
                    nearby_inputs = parent.locator('input, textarea, select')
                    if nearby_inputs.count() > 0:
                        element = nearby_inputs.first
                        logger.info(f"         ✓ Found via label strategy")
            except:
                pass
        
        if not element:
            # Strategy 2: Fuzzy text matching with XPath
            try:
                # Try to find label with similar text (case-insensitive, partial match)
                field_title_lower = field_title.lower()
                field_title_words = field_title_lower.split()
                for word in field_title_words:
                    if len(word) > 3:  # Only use meaningful words
                        xpath = f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}')]"
                        labels = page.locator(f'xpath={xpath}')
                        if labels.count() > 0:
                            label = labels.first
                            # Try to get associated input via 'for' attribute
                            label_for = label.get_attribute('for')
                            if label_for:
                                input_by_id = page.locator(f'#{label_for}')
                                if input_by_id.count() > 0:
                                    element = input_by_id.first
                                    logger.info(f"         ✓ Found via fuzzy label-for: '{word}'")
                                    break
                            # Or find nearby input
                            parent = label.locator('xpath=..')
                            nearby = parent.locator('input, textarea, select')
                            if nearby.count() > 0:
                                element = nearby.first
                                logger.info(f"         ✓ Found via fuzzy label nearby: '{word}'")
                                break
            except:
                pass
        
        if not element:
            # Strategy 3: XPath by input type and position
            try:
                if field_type in ['Text', 'Input']:
                    # Find all text inputs and try to match by context
                    all_inputs = page.locator('xpath=//input[@type="text" or not(@type)]').all()
                    for inp in all_inputs:
                        # Check if any nearby text contains our field title
                        try:
                            parent = inp.locator('xpath=..')
                            parent_text = parent.inner_text().lower()
                            if field_title.lower() in parent_text:
                                element = inp
                                logger.info(f"         ✓ Found via XPath context matching")
                                break
                        except:
                            continue
                elif field_type == 'Textarea':
                    all_textareas = page.locator('xpath=//textarea').all()
                    for ta in all_textareas:
                        try:
                            parent = ta.locator('xpath=..')
                            parent_text = parent.inner_text().lower()
                            if field_title.lower() in parent_text:
                                element = ta
                                logger.info(f"         ✓ Found textarea via XPath context")
                                break
                        except:
                            continue
            except:
                pass
        
        if not element:
            # Strategy 4: Visual position - find by proximity to text
            try:
                # Find text node containing field title
                text_nodes = page.locator(f'xpath=//*[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{field_title.lower()}")][not(self::script)][not(self::style)]').all()
                for text_node in text_nodes:
                    try:
                        # Find first input after this text node in DOM order
                        following_inputs = text_node.locator('xpath=following::input[1] | following::textarea[1] | following::select[1]')
                        if following_inputs.count() > 0:
                            element = following_inputs.first
                            logger.info(f"         ✓ Found via visual position (following element)")
                            break
                    except:
                        continue
            except:
                pass
        
        return element
    
    def _fill_file_field(self, element, resume_path: Optional[str], field_title: str):
        """Handle file upload."""
        if resume_path and Path(resume_path).exists():
            element.set_input_files(str(Path(resume_path).absolute()))
            logger.info(f"      ✅ Uploaded: {field_title}")
    
    def _fill_boolean_field(self, page, element, value: bool, field_title: str, yes_clicks: int, no_clicks: int):
        """Handle checkbox/boolean fields."""
        button_text = "Yes" if value else "No"
        
        try:
            # Set checkbox value via JS
            element.evaluate(f'el => el.checked = {str(value).lower()}')
            logger.info(f"      ✅ Set checkbox via JS: {field_title}")
            
            # Find and click the button
            logger.info(f"         🔘 Looking for '{button_text}' button near this field...")
            
            try:
                # Get parent container
                parent = element.locator('xpath=ancestor::div[contains(@class, "css-") or contains(@class, "field")]').first
                button = parent.locator(f'button:has-text("{button_text}")').first
                
                if button.count() > 0:
                    button.scroll_into_view_if_needed()
                    button.click(timeout=3000, force=True)
                    logger.info(f"      ✅ Clicked '{button_text}' button: {field_title}")
                else:
                    logger.warning(f"      ⚠️  '{button_text}' button not found in parent container")
            except:
                # Fallback: use global button index
                logger.warning(f"         ⚠️  Parent strategy failed, using global index")
                buttons = page.locator(f'button:has-text("{button_text}")').all()
                logger.info(f"         📍 Found {len(buttons)} '{button_text}' buttons total")
                
                if button_text == "Yes":
                    button_index = yes_clicks
                    yes_clicks += 1
                else:
                    button_index = no_clicks
                    no_clicks += 1
                
                if button_index < len(buttons):
                    btn = buttons[button_index]
                    btn.scroll_into_view_if_needed()
                    btn.click(timeout=3000, force=True)
                    logger.info(f"      ✅ Clicked '{button_text}' button #{button_index + 1}: {field_title}")
        
        except Exception as e:
            logger.error(f"      ⚠️  Boolean error: {str(e)[:80]}")
        
        return yes_clicks, no_clicks
    
    def _fill_location_field(self, page, element, value: str, field_title: str):
        """Handle location autocomplete field."""
        try:
            logger.info(f"         🔍 Location field found, preparing to type...")
            element.scroll_into_view_if_needed()
            
            element.click()
            logger.info(f"         ✓ Clicked location field")
            
            element.fill('')
            logger.info(f"         ✓ Cleared field")
            
            location_text = str(value)
            logger.info(f"         📍 Typing location: '{location_text}'")
            
            # Try multiple typing methods
            try:
                element.press_sequentially(location_text, delay=random.randint(80, 120))
                filled = element.input_value()
                logger.info(f"         ✓ After press_sequentially: '{filled}' ({len(filled) if filled else 0} chars)")
                
                if not filled or len(filled) < 3:
                    logger.warning(f"         ⚠️  press_sequentially didn't work, trying type()...")
                    element.fill('')
                    element.type(location_text, delay=100)
                    filled = element.input_value()
                    logger.info(f"         ✓ After type(): '{filled}' ({len(filled) if filled else 0} chars)")
                
                if not filled or len(filled) < 3:
                    logger.warning(f"         ⚠️  type() didn't work, trying fill()...")
                    element.fill(location_text)
                    filled = element.input_value()
                    logger.info(f"         ✓ After fill(): '{filled}' ({len(filled) if filled else 0} chars)")
            
            except Exception as type_error:
                logger.warning(f"         ⚠️  Typing error: {str(type_error)[:100]}")
                element.fill(location_text)
            
            # Wait for autocomplete dropdown
            page.wait_for_timeout(800)
            
            # Click first autocomplete option
            try:
                autocomplete_option = page.locator('[role="option"]').first
                if autocomplete_option.count() > 0:
                    autocomplete_option.click()
                    logger.info(f"      ✅ Selected from autocomplete: {field_title}")
                else:
                    filled = element.input_value()
                    if filled and len(filled) > 0:
                        logger.info(f"      ✅ Typed location: {field_title} ({len(filled)}/{len(location_text)} chars)")
                    else:
                        logger.warning(f"      ⚠️  Location field still empty after all attempts!")
            except Exception as e:
                filled = element.input_value()
                if filled:
                    logger.info(f"      ✅ Typed location: {field_title} ({len(filled)} chars)")
                else:
                    logger.warning(f"      ⚠️  Location field empty!")
        
        except Exception as e:
            logger.error(f"      ⚠️  Location field error: {str(e)[:50]}")
    
    def _fill_select_field(self, page, element, value, field_type: str, field_title: str):
        """Handle ValueSelect and MultiValueSelect fields."""
        try:
            logger.info(f"         🔍 DEBUG: Processing {field_type} field: {field_title}")
            element.scroll_into_view_if_needed()
            
            tag_name = element.evaluate('el => el.tagName')
            elem_type = element.evaluate('el => el.type') if tag_name.lower() == 'input' else None
            logger.info(f"         📄 Element: <{tag_name}> type={elem_type}")
            
            if elem_type == 'radio':
                self._handle_radio_buttons(page, element, value, field_title)
            elif elem_type == 'checkbox':
                self._handle_checkboxes(page, element, value, field_title)
            else:
                self._handle_dropdown(page, element, value, field_title)
            
            time.sleep(random.uniform(0.3, 0.6))
        except Exception as e:
            logger.error(f"      ⚠️  Dropdown error: {str(e)[:80]}")
    
    def _handle_radio_buttons(self, page, element, value: str, field_title: str):
        """Handle radio button selection."""
        logger.info(f"         🔘 This is a radio button input")
        
        field_container = element.locator('xpath=ancestor::fieldset').first
        if field_container.count() == 0:
            field_container = element.locator('xpath=ancestor::div[contains(@class, "fieldEntry")]').first
        
        if field_container.count() > 0:
            all_labels = field_container.locator('label').all()
            logger.info(f"         🎯 Available radio options ({len(all_labels)}):")
            for idx, lbl in enumerate(all_labels):
                lbl_text = lbl.inner_text()
                logger.info(f"            [{idx}] '{lbl_text}'")
            
            value_str = str(value)
            logger.info(f"         🎯 Looking for: '{value_str}'")
            
            found = False
            for lbl in all_labels:
                lbl_text = lbl.inner_text().strip()
                if lbl_text.lower() == value_str.lower():
                    logger.info(f"         ✓ Found match: '{lbl_text}' (clicking...)")
                    lbl.click()
                    logger.info(f"      ✅ Selected radio: {value_str}")
                    found = True
                    break
            
            if not found:
                logger.warning(f"      ⚠️  Could not find radio option: {value_str}")
                logger.info(f"      🔍 Available were: {[l.inner_text().strip() for l in all_labels]}")
        else:
            logger.warning(f"      ⚠️  Could not find container for radio buttons")
    
    def _handle_checkboxes(self, page, element, value, field_title: str):
        """Handle checkbox selection."""
        logger.info(f"         ☑️  This is a checkbox input")
        
        field_container = element.locator('xpath=ancestor::fieldset').first
        if field_container.count() == 0:
            field_container = element.locator('xpath=ancestor::div[contains(@class, "fieldEntry")]').first
        
        if field_container.count() > 0:
            all_labels = field_container.locator('label').all()
            logger.info(f"         📋 Available checkbox options ({len(all_labels)}):")
            for idx, lbl in enumerate(all_labels):
                lbl_text = lbl.inner_text()
                logger.info(f"            [{idx}] '{lbl_text}'")
            
            if isinstance(value, list):
                values_to_select = value
            else:
                values_to_select = [value]
            
            logger.info(f"         🎯 Need to select: {values_to_select}")
            
            # Uncheck all first
            all_checkboxes = field_container.locator('input[type="checkbox"]').all()
            logger.info(f"         🔄 Unchecking all {len(all_checkboxes)} checkboxes...")
            for idx, cb in enumerate(all_checkboxes):
                if cb.is_checked():
                    logger.info(f"            [{idx}] Unchecking...")
                    cb.uncheck()
            
            # Check selected ones
            for v in values_to_select:
                logger.info(f"         🔍 Looking for: '{v}'")
                found = False
                for lbl in all_labels:
                    lbl_text = lbl.inner_text().strip()
                    if lbl_text.lower() == v.lower():
                        logger.info(f"         ✓ Found match: '{lbl_text}' (clicking...)")
                        lbl.click()
                        found = True
                        break
                if found:
                    logger.info(f"         ✅ Checked: {v}")
                else:
                    logger.warning(f"         ⚠️  Not found: {v}")
                    logger.info(f"         🔍 Available options were: {[l.inner_text().strip() for l in all_labels]}")
            
            logger.info(f"      ✅ Selected checkboxes: {', '.join(values_to_select)}")
        else:
            logger.warning(f"      ⚠️  Could not find container for checkboxes")
    
    def _handle_dropdown(self, page, element, value, field_title: str):
        """Handle regular dropdown selection."""
        logger.info(f"         🔽 This is a dropdown/combobox")
        element.click()
        logger.info(f"         ✓ Clicked dropdown")
        
        if isinstance(value, list):
            # Multi-select dropdown
            for v in value:
                logger.info(f"         📝 Typing to filter: {v}")
                element.type(str(v), delay=50)
                try:
                    option = page.locator(f'[role="option"]:has-text("{v}")').first
                    if option.count() > 0:
                        option.click()
                        logger.info(f"         ✓ Selected: {v}")
                except:
                    logger.warning(f"         ⚠️  Could not select: {v}")
        else:
            # Single select dropdown
            value_str = str(value)
            logger.info(f"         📝 Typing to filter: {value_str}")
            element.type(value_str, delay=50)
            
            try:
                page.wait_for_selector('[role="option"]', timeout=2000)
                option = page.locator(f'[role="option"]:has-text("{value_str}")').first
                if option.count() > 0:
                    option.click()
                    logger.info(f"      ✅ Selected: {value_str}")
                else:
                    element.press('Enter')
                    logger.info(f"      ✅ Selected first option (pressed Enter)")
            except Exception as e:
                try:
                    option = page.locator('[role="option"]').first
                    if option.count() > 0:
                        option.click()
                        logger.info(f"      ✅ Selected first visible option")
                    else:
                        logger.warning(f"      ⚠️  No options found for: {value_str}")
                except:
                    logger.warning(f"      ⚠️  Could not select any option")
    
    def _fill_text_field(self, element, value: str, field_title: str):
        """Handle text input fields."""
        element.scroll_into_view_if_needed()
        time.sleep(random.uniform(0.2, 0.5))
        element.click()
        time.sleep(random.uniform(0.3, 0.6))
        
        element.fill('')
        time.sleep(0.1)
        
        text_to_type = str(value)
        
        # For longer text, use fill() then verify
        if len(text_to_type) > 200:
            element.fill(text_to_type)
            time.sleep(random.uniform(0.5, 1))
            
            filled_value = element.input_value()
            if len(filled_value) < len(text_to_type) - 10:
                logger.warning(f"      ⚠️  Only filled {len(filled_value)}/{len(text_to_type)} chars, retrying...")
                element.fill('')
                time.sleep(0.2)
                # Type in chunks
                chunk_size = 100
                for i in range(0, len(text_to_type), chunk_size):
                    chunk = text_to_type[i:i+chunk_size]
                    element.type(chunk, delay=5)
                    time.sleep(0.1)
        else:
            element.type(text_to_type, delay=random.randint(20, 50))
        
        time.sleep(random.uniform(0.3, 0.7))
        
        # Final verification
        filled_value = element.input_value()
        expected_length = len(text_to_type)
        actual_length = len(filled_value) if filled_value else 0
        
        if actual_length >= expected_length - 10:
            logger.info(f"      ✅ Filled: {field_title} ({actual_length}/{expected_length} chars)")
        else:
            logger.warning(f"      ⚠️  Incomplete fill: {field_title} ({actual_length}/{expected_length} chars)")
            logger.info(f"         Trying one more time with press_sequentially...")
            element.click()
            element.press_sequentially(text_to_type, delay=10)
            time.sleep(0.5)
    
    def _fill_eeo_fields(self, page):
        """Fill additional EEO fields (Gender, Race, Veteran status)."""
        logger.info(f"\n   🔍 Looking for additional EEO fields (Gender, Race, Veteran)...")
        
        demographics = self.settings.user_info.demographics
        
        # Gender identity
        self._fill_gender_field(page, demographics.gender)
        
        # Race identity
        self._fill_race_field(page, demographics.race)
        
        # Veteran status
        self._fill_veteran_field(page, demographics.veteran_status)
    
    def _fill_gender_field(self, page, gender_value: str):
        """Fill gender identity field."""
        try:
            gender_heading = page.locator('text=/Gender identity/i').first
            if gender_heading.count() > 0:
                logger.info(f"   📋 Found Gender identity field")
                gender_heading.scroll_into_view_if_needed()

                # Find all radio inputs after the heading in the DOM
                radio_inputs = gender_heading.locator('xpath=following::input[@type="radio"]').all()
                logger.info(f"   🔍 (Fixed) Found {len(radio_inputs)} radio inputs after heading")

                # Log all radio labels for debugging
                for idx, radio in enumerate(radio_inputs):
                    input_id = radio.get_attribute('id')
                    label = page.locator(f'label[for="{input_id}"]').first if input_id else None
                    label_text = label.inner_text() if label and label.count() > 0 else "(no label)"
                    logger.info(f"      [{idx}] id={input_id} label={label_text}")

                # Now select the correct radio based on gender_value (exact match only)
                gender_value_lower = gender_value.strip().lower()
                found = False
                for radio in radio_inputs:
                    input_id = radio.get_attribute('id')
                    label = page.locator(f'label[for="{input_id}"]').first if input_id else None
                    label_text = label.inner_text().strip() if label and label.count() > 0 else ""
                    if label_text.lower() == gender_value_lower:
                        label.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        label.click()
                        time.sleep(0.5)
                        logger.info(f"      ✅ Selected Gender: {label_text}")
                        found = True
                        break
                if not found:
                    logger.warning(f"      ⚠️  Could not find radio for gender value: {gender_value}")
        except Exception as e:
            logger.error(f"      ⚠️  Gender field error: {str(e)[:150]}")
    
    def _fill_race_field(self, page, race_value: str):
        """Fill race identity field."""
        try:
            race_label = page.locator('text=/Race identity/i').first
            if race_label.count() > 0:
                logger.info(f"   📋 Found Race identity field")
                
                race_input = page.locator('input[placeholder="Start typing..." i]').last
                if race_input.count() > 0:
                    race_input.scroll_into_view_if_needed()
                    time.sleep(0.3)
                    race_input.click()
                    time.sleep(0.5)
                    race_input.press_sequentially(race_value, delay=80)
                    time.sleep(0.8)
                    
                    option = page.locator('[role="option"]').first
                    if option.count() > 0:
                        option.click()
                        time.sleep(0.5)
                        logger.info(f"      ✅ Selected Race: {race_value}")
        except Exception as e:
            logger.error(f"      ⚠️  Race field error: {str(e)[:150]}")
    
    def _fill_veteran_field(self, page, veteran_value: str):
        """Fill veteran status field."""
        try:
            veteran_label = page.locator('text=/Veteran status/i').first
            if veteran_label.count() > 0:
                logger.info(f"   📋 Found Veteran status field")
                
                # Map to radio button text
                if veteran_value.lower() == 'no':
                    veteran_text = 'I am not a Veteran'
                elif veteran_value.lower() == 'yes':
                    veteran_text = 'Yes, I am a Veteran'
                else:
                    veteran_text = 'Prefer not to disclose'
                
                veteran_radio = page.locator(f'label:has-text("{veteran_text}")').first
                if veteran_radio.count() > 0:
                    veteran_radio.click()
                    logger.info(f"      ✅ Selected Veteran: {veteran_text}")
        except Exception as e:
            logger.error(f"      ⚠️  Veteran field error: {str(e)[:50]}")
    
    def _manual_submit(self, browser_context, browser) -> Dict:
        """Handle manual submission workflow."""
        logger.info(f"\n" + "="*70)
        logger.info(f"   🛑 AUTO-SUBMIT DISABLED (Spam Detection Bypass)")
        logger.info(f"   " + "="*70)
        logger.info(f"   The form has been filled automatically.")
        logger.info(f"   Please review the form and click Submit MANUALLY.")
        logger.info(f"   ")
        logger.info(f"   Why? Ashby detects automated submissions. By having a human")
        logger.info(f"   click the final Submit button, it looks like a human applied.")
        logger.info(f"   " + "="*70)
        logger.info(f"   ⏸️  Review the form, then click Submit in the browser")
        logger.info(f"   ⏸️  Press ENTER after you've submitted to close browser...")
        logger.info(f"   " + "="*70 + "\n")
        input()
        logger.info(f"   ✅ Closing browser...")
        browser_context.close()
        browser.close()
        return {
            'success': True,
            'status': 'manual_submit',
            'message': 'Form filled, human submitted manually'
        }
    
    def _auto_submit(self, page, browser_context, browser) -> Dict:
        """Handle automatic submission workflow."""
        logger.info(f"\n   ⏳ Looking for submit button...")
        self._simulate_human_behavior(page)
        submit_selectors = [
            'button:has-text("Submit Application")',
            'button:has-text("Submit")',
            'button:has-text("Apply")',
            'input[type="submit"]',
            'button[type="submit"]'
        ]
        submitted = False
        for selector in submit_selectors:
            try:
                count = page.locator(selector).count()
                logger.info(f"      🔍 Checking selector '{selector}': found {count}")
                if count > 0:
                    logger.info(f"   🚀 Clicking submit button: {selector}")
                    button = page.locator(selector).first
                    button.scroll_into_view_if_needed()
                    self._simulate_human_behavior(page)
                    button.click()
                    submitted = True
                    break
            except Exception as e:
                logger.warning(f"      ⚠️  Error with selector '{selector}': {str(e)[:50]}")
                continue
        if submitted:
            logger.info(f"   ⏳ Waiting for submission to process...")
            # Check for CAPTCHA before and after submit
            if self._detect_captcha(page):
                logger.info(f"\n" + "="*70)
                logger.info(f"   🤖 CAPTCHA DETECTED!")
                logger.info(f"   " + "="*70)
                logger.info(f"   Please solve the CAPTCHA manually in the browser window.")
                logger.info(f"   Press ENTER after solving the CAPTCHA...")
                logger.info(f"   " + "="*70 + "\n")
                input()
            page.wait_for_load_state('networkidle', timeout=30000)
            # Check for CAPTCHA again after load
            if self._detect_captcha(page):
                logger.info(f"\n" + "="*70)
                logger.info(f"   🤖 CAPTCHA STILL PRESENT after submit!")
                logger.info(f"   Please solve the CAPTCHA manually in the browser window.")
                logger.info(f"   Press ENTER after solving the CAPTCHA...")
                logger.info(f"   " + "="*70 + "\n")
                input()
            # Take post-submit screenshot
            post_submit_path = get_post_submit_screenshot_path()
            page.screenshot(path=str(post_submit_path))
            logger.info(f"   📸 Screenshot saved: {post_submit_path}")
            # Check for success/error
            page_content = page.content().lower()
            if 'spam' in page_content or 'flagged' in page_content:
                logger.warning(f"\n   ⚠️  WARNING: Application may have been flagged as spam!")
                # Dump HTML for debugging
                logger.info(f"   ⚠️  Dumping page HTML for spam debug:")
                logger.info(page.content()[:2000])
                status = 'flagged'
                success = False
                message = 'Application flagged as spam'
            elif 'thank you' in page_content or 'submitted' in page_content or 'received' in page_content:
                logger.info(f"\n   ✅ Application submitted successfully!")
                status = 'submitted'
                success = True
                message = 'Application submitted successfully'
            else:
                logger.warning(f"\n   ⚠️  Submission status unclear - check browser window")
                status = 'uncertain'
                success = True
                message = 'Submitted but confirmation unclear'
        else:
            logger.error(f"\n   ❌ Could not find submit button")
            status = 'failed'
            success = False
            message = 'Submit button not found'
        # Keep browser open for inspection
        logger.info(f"\n   ⏸️  Browser kept open for inspection...")
        logger.info(f"   ℹ️  Status: {status}")
        logger.info(f"   ℹ️  Message: {message}")
        logger.info(f"   ℹ️  Check the browser window to verify submission")
        logger.info(f"   ℹ️  Press Ctrl+C when done\n")
        def handler(signum, frame):
            logger.info(f"\n   🛑 Closing browser...")
            browser_context.close()
            browser.close()
            exit(0)
        signal.signal(signal.SIGINT, handler)
        # Wait indefinitely
        while True:
            time.sleep(1)
    
    def _detect_captcha(self, page):
        """Detect if a CAPTCHA is present on the page."""
        # Check for iframes
        if page.locator('iframe[title*="recaptcha" i], iframe[src*="captcha" i]').count() > 0:
            logger.info("   🤖 CAPTCHA detected via iframe!")
            return True
        # Check for elements with class or id containing 'captcha'
        if page.locator('[class*="captcha" i], [id*="captcha" i]').count() > 0:
            logger.info("   🤖 CAPTCHA detected via class/id!")
            return True
        # Check for visible text
        if page.locator('text=/captcha/i').count() > 0:
            logger.info("   🤖 CAPTCHA detected via visible text!")
            return True
        return False

    def _simulate_human_behavior(self, page):
        """Simulate human-like mouse movement and scrolling."""
        import random
        width = page.viewport_size['width'] if page.viewport_size else 1920
        height = page.viewport_size['height'] if page.viewport_size else 1080
        for _ in range(random.randint(3, 7)):
            x = random.randint(0, width-1)
            y = random.randint(0, height-1)
            page.mouse.move(x, y, steps=random.randint(10, 30))
            page.wait_for_timeout(random.randint(100, 400))
        # Scroll randomly
        for _ in range(random.randint(1, 3)):
            scroll_y = random.randint(0, height)
            page.evaluate(f"window.scrollTo(0, {scroll_y})")
            page.wait_for_timeout(random.randint(200, 600))
