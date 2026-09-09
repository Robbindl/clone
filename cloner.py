#!/usr/bin/env python3
"""
Website Cloner Script
Downloads an entire website for offline viewing.
Supports multiple rendering engines: requests, playwright, selenium, puppeteer
"""

import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import urllib.request
import re
import time
import argparse
import shutil
from pathlib import Path
from urllib.robotparser import RobotFileParser


class WebsiteCloner:
    def __init__(self, base_url, output_dir="cloned_site", delay=1, respect_robots=True, renderer="requests"):
        self.base_url = base_url.rstrip('/')
        self.domain = urllib.parse.urlparse(base_url).netloc
        self.output_dir = Path(output_dir)
        self.visited = set()
        self.delay = delay
        self.respect_robots = respect_robots
        self.follow_pages = False
        self.renderer = renderer
        self.browser = None
        self.playwright_browser = None
        self.selenium_driver = None
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup robots.txt parser
        if respect_robots:
            self.rp = RobotFileParser()
            self.rp.set_url(f"{urllib.parse.urlparse(base_url).scheme}://{self.domain}/robots.txt")
            try:
                self.rp.read()
            except:
                self.rp = None
        
        # Initialize browser if needed
        self._init_browser()
    
    def _init_browser(self):
        """Initialize browser for JavaScript rendering"""
        if self.renderer == "playwright":
            try:
                from playwright.sync_api import sync_playwright
                self._playwright = sync_playwright().start()
                self.playwright_browser = self._playwright.chromium.launch(headless=True)
                print("[INFO] Playwright browser initialized")
            except ImportError:
                print("[WARNING] Playwright not installed. Install with: pip install playwright")
                self.renderer = "requests"
        elif self.renderer == "selenium":
            try:
                from selenium import webdriver
                from selenium.webdriver.common.by import By
                self.selenium_driver = webdriver.Chrome()
                print("[INFO] Selenium WebDriver initialized")
            except ImportError:
                print("[WARNING] Selenium not installed. Install with: pip install selenium")
                self.renderer = "requests"
            except Exception as e:
                print(f"[WARNING] Selenium initialization failed: {e}")
                self.renderer = "requests"
        elif self.renderer == "puppeteer":
            try:
                import asyncio
                import pyppeteer
                print("[INFO] Puppeteer (pyppeteer) will be used for rendering")
            except ImportError:
                print("[WARNING] Pyppeteer not installed. Install with: pip install pyppeteer")
                self.renderer = "requests"
    
    def _fetch_with_renderer(self, url):
        """Fetch page content using the configured renderer"""
        if self.renderer == "playwright":
            return self._fetch_playwright(url)
        elif self.renderer == "selenium":
            return self._fetch_selenium(url)
        elif self.renderer == "puppeteer":
            return self._fetch_puppeteer(url)
        else:
            return self._fetch_requests(url)
    
    def _fetch_requests(self, url):
        """Fetch using requests library"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"  ✗ Error fetching {url}: {e}")
            return None
    
    def _fetch_playwright(self, url):
        """Fetch using Playwright (renders JavaScript)"""
        try:
            page = self.playwright_browser.new_page()
            page.goto(url, wait_until="networkidle")
            content = page.content()
            page.close()
            
            # Create a response-like object
            class PlaywrightResponse:
                def __init__(self, content):
                    self.content = content.encode('utf-8')
                    self.text = content
                    self.headers = {'content-type': 'text/html'}
                    self.status_code = 200
            
            return PlaywrightResponse(content)
        except Exception as e:
            print(f"  ✗ Playwright error fetching {url}: {e}")
            return None
    
    def _fetch_selenium(self, url):
        """Fetch using Selenium (renders JavaScript)"""
        try:
            self.selenium_driver.get(url)
            time.sleep(2)  # Wait for page to render
            content = self.selenium_driver.page_source
            
            # Create a response-like object
            class SeleniumResponse:
                def __init__(self, content):
                    self.content = content.encode('utf-8')
                    self.text = content
                    self.headers = {'content-type': 'text/html'}
                    self.status_code = 200
            
            return SeleniumResponse(content)
        except Exception as e:
            print(f"  ✗ Selenium error fetching {url}: {e}")
            return None
    
    def _fetch_puppeteer(self, url):
        """Fetch using Pyppeteer (renders JavaScript)"""
        try:
            import asyncio
            from pyppeteer import launch
            
            async def fetch_async():
                browser = await launch(headless=True)
                page = await browser.newPage()
                await page.goto(url, waitUntil='networkidle')
                content = await page.content()
                await browser.close()
                return content
            
            content = asyncio.run(fetch_async())
            
            # Create a response-like object
            class PuppeteerResponse:
                def __init__(self, content):
                    self.content = content.encode('utf-8')
                    self.text = content
                    self.headers = {'content-type': 'text/html'}
                    self.status_code = 200
            
            return PuppeteerResponse(content)
        except Exception as e:
            print(f"  ✗ Puppeteer error fetching {url}: {e}")
            return None
    
    def cleanup(self):
        """Clean up browser resources"""
        if self.playwright_browser:
            self.playwright_browser.close()
            print("[INFO] Playwright browser closed")
        if self.selenium_driver:
            self.selenium_driver.quit()
            print("[INFO] Selenium driver closed")
    
    def can_fetch(self, url):
        """Check robots.txt permission"""
        if not self.respect_robots or not self.rp:
            return True
        return self.rp.can_fetch("*", url)
    
    def get_local_path(self, url):
        """Convert URL to local file path"""
        parsed = urllib.parse.urlparse(url)
        path = urllib.parse.unquote(parsed.path).lstrip('/')
        
        # Handle query strings by incorporating them into filename
        if parsed.query:
            path = f"{path}_{urllib.parse.quote(parsed.query, safe='')}"
        
        # Default to index.html for directories
        if not path or path.endswith('/'):
            path = os.path.join(path, "index.html")
        
        # Ensure proper extension for HTML files
        if '.' not in os.path.basename(path):
            path += '.html'
        
        return self.output_dir / self.domain / path
    
    def download_file(self, url, local_path):
        """Download a single file"""
        try:
            response = self._fetch_with_renderer(url)
            if not response:
                return None
            
            response.raise_for_status() if hasattr(response, 'raise_for_status') else None
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return response
            
        except Exception as e:
            print(f"  ✗ Error downloading {url}: {e}")
            return None
    
    def extract_links(self, soup, base_url):
        """Extract page dependencies from HTML."""
        links = []
        
        for tag in soup.find_all('link', href=True):
            full_url = urllib.parse.urljoin(base_url, tag['href'])
            links.append(full_url)
        
        # Scripts, images, sources
        for tag in soup.find_all(['script', 'img', 'source', 'video', 'audio'], src=True):
            full_url = urllib.parse.urljoin(base_url, tag['src'])
            links.append(full_url)
        
        # Inline styles with url()
        for tag in soup.find_all(style=True):
            urls = re.findall(r'url\(["\']?(.*?)["\']?\)', tag['style'])
            for u in urls:
                full_url = urllib.parse.urljoin(base_url, u)
                links.append(full_url)
        
        # CSS files - parse for @import and url()
        for tag in soup.find_all('link', rel='stylesheet'):
            css_url = urllib.parse.urljoin(base_url, tag.get('href', ''))
            links.append(css_url)
        
        return links

    def extract_page_links(self, soup, base_url):
        """Extract navigational links when recursive page crawling is enabled."""
        return [
            urllib.parse.urljoin(base_url, tag['href'])
            for tag in soup.find_all('a', href=True)
        ]
    
    def update_html_links(self, soup, base_url):
        """Update links in HTML to point to local files"""
        def make_relative(url):
            parsed = urllib.parse.urlparse(url)
            if parsed.netloc != self.domain:
                return url  # External link, keep as is
            
            local_path = self.get_local_path(url)
            try:
                return os.path.relpath(
                    local_path, self.get_local_path(base_url).parent
                ).replace(os.sep, '/')
            except:
                return url
        
        # Update href attributes
        for tag in soup.find_all(['a', 'link'], href=True):
            tag['href'] = make_relative(urllib.parse.urljoin(base_url, tag['href']))
        
        # Update src attributes
        for tag in soup.find_all(['script', 'img', 'source', 'video', 'audio'], src=True):
            tag['src'] = make_relative(urllib.parse.urljoin(base_url, tag['src']))

        for tag in soup.find_all(attrs={'srcset': True}):
            candidates = []
            for candidate in tag['srcset'].split(','):
                parts = candidate.strip().split(maxsplit=1)
                if parts:
                    parts[0] = make_relative(urllib.parse.urljoin(base_url, parts[0]))
                candidates.append(' '.join(parts))
            tag['srcset'] = ', '.join(candidates)
        
        return soup

    def update_css_links(self, content, base_url):
        """Rewrite same-site CSS URLs to their downloaded paths."""
        def replace_url(match):
            raw_url = match.group(1).strip()
            if raw_url.startswith(('data:', '#')):
                return match.group(0)
            absolute_url = urllib.parse.urljoin(base_url, raw_url)
            parsed = urllib.parse.urlparse(absolute_url)
            if parsed.netloc != self.domain:
                return match.group(0)
            local_path = self.get_local_path(absolute_url)
            relative_path = os.path.relpath(
                local_path, self.get_local_path(base_url).parent
            ).replace(os.sep, '/')
            return f'url({relative_path})'

        return re.sub(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)', replace_url, content)

    def extract_script_links(self, content, base_url):
        """Find framework chunks referenced by downloaded JavaScript."""
        paths = re.findall(
            r'static/(?:chunks|css)/[A-Za-z0-9._%\[\]\\/-]+\.(?:js|css)',
            content,
        )
        chunk_values = {}
        for chunk_id, value in re.findall(r'(\d+):"([^"\\]+)"', content):
            chunk_values.setdefault(chunk_id, []).append(value)
        for chunk_id, values in chunk_values.items():
            chunk_hash = next(
                (value for value in values if re.fullmatch(r'[a-f0-9]{8,}', value)),
                None,
            )
            if not chunk_hash:
                continue
            chunk_name = next(
                (value for value in values if value != chunk_hash and '/' not in value),
                None,
            )
            if chunk_name:
                paths.append(f'{chunk_name}.{chunk_hash}.js')
            else:
                paths.append(f'{chunk_id}.{chunk_hash}.js')
        paths.extend(re.findall(r'[a-f0-9]{8,}\.css', content))
        paths = list(dict.fromkeys(paths))
        return [
            urllib.parse.urljoin(
                base_url,
                ('/_next/' + path if path.startswith('static/') else
                 '/_next/static/css/' + path if path.endswith('.css') else
                 '/_next/static/chunks/' + path)
                .replace('\\/', '/'),
            )
            for path in paths
        ]

    def mirror_root_assets(self):
        """Mirror root-relative framework assets for static SPA servers."""
        site_root = self.output_dir / self.domain
        for relative_path in ('_next', 'manifest.json', 'favicon.ico', 'logo.png'):
            source = site_root / relative_path
            target = self.output_dir / relative_path
            if source.is_dir():
                shutil.copytree(source, target, dirs_exist_ok=True)
            elif source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

        root_chunks = self.output_dir / '_next' / 'static' / 'chunks'
        if root_chunks.is_dir():
            for chunk in root_chunks.glob('*.js'):
                match = re.fullmatch(r'(.+)\.([a-f0-9]{8,})\.js', chunk.name)
                if match:
                    alternate = root_chunks / f'{match.group(2)}.{match.group(1)}.js'
                    if not alternate.exists():
                        shutil.copy2(chunk, alternate)
    
    def clone(self, url=None, depth=0, max_depth=10):
        """Recursively clone website"""
        if url is None:
            url = self.base_url
        
        # Normalize URL
        url = urllib.parse.urldefrag(url)[0]  # Remove fragment
        
        # Skip if already visited or external
        if url in self.visited:
            return
        if self.domain not in urllib.parse.urlparse(url).netloc:
            return
        if depth > max_depth:
            return
        if not self.can_fetch(url):
            print(f"  ⊘ Skipping {url} (robots.txt)")
            return
        
        self.visited.add(url)
        print(f"[{len(self.visited)}] Downloading: {url}")
        
        # Download file
        local_path = self.get_local_path(url)
        response = self.download_file(url, local_path)
        
        if not response:
            return
        
        # Process HTML files recursively
        content_type = response.headers.get('content-type', '').lower()
        
        if 'text/html' in content_type:
            try:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract and follow asset links
                links = self.extract_links(soup, url)
                
                # Update links to local paths
                soup = self.update_html_links(soup, url)
                
                # Save modified HTML
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                # Follow navigation only when explicitly requested.
                if self.follow_pages:
                    links.extend(self.extract_page_links(soup, url))

                # Follow links with delay
                for link in links:
                    time.sleep(self.delay)
                    self.clone(link, depth + 1, max_depth)
                    
            except Exception as e:
                print(f"  ✗ Error parsing {url}: {e}")
        
        elif 'text/css' in content_type:
            try:
                content = response.content.decode('utf-8')
                urls = re.findall(r'url\(["\']?(.*?)["\']?\)', content)
                content = self.update_css_links(content, url)
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                for css_url in urls:
                    full_url = urllib.parse.urljoin(url, css_url)
                    if self.domain in full_url:
                        time.sleep(self.delay)
                        self.clone(full_url, depth + 1, max_depth)
            except:
                pass

        elif 'javascript' in content_type or 'application/javascript' in content_type:
            try:
                content = response.content.decode('utf-8')
                for script_url in self.extract_script_links(content, url):
                    time.sleep(self.delay)
                    self.clone(script_url, depth + 1, max_depth)
            except UnicodeDecodeError:
                pass


def main():
    parser = argparse.ArgumentParser(description='Clone a website for offline viewing')
    parser.add_argument('url', help='Website URL to clone')
    parser.add_argument('-o', '--output', default='cloned_site', help='Output directory')
    parser.add_argument('-d', '--delay', type=float, default=0.5, help='Delay between requests (seconds)')
    parser.add_argument('--depth', type=int, default=10, help='Maximum crawl depth')
    parser.add_argument('--follow-pages', action='store_true', help='Also crawl same-domain navigation links')
    parser.add_argument('--no-robots', action='store_true', help='Ignore robots.txt')
    parser.add_argument('--renderer', choices=['requests', 'playwright', 'selenium', 'puppeteer'], 
                        default='requests', help='Rendering engine for JavaScript-heavy sites')
    
    args = parser.parse_args()
    
    print(f"Starting clone of {args.url}")
    print(f"Output directory: {args.output}")
    print(f"Renderer: {args.renderer}")
    print(f"Delay: {args.delay}s | Max depth: {args.depth}")
    print("-" * 50)
    
    cloner = WebsiteCloner(
        args.url,
        output_dir=args.output,
        delay=args.delay,
        respect_robots=not args.no_robots,
        renderer=args.renderer
    )
    cloner.follow_pages = args.follow_pages
    
    try:
        cloner.clone(max_depth=args.depth)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        cloner.cleanup()
    
    print("-" * 50)
    cloner.mirror_root_assets()
    print(f"Done! Downloaded {len(cloner.visited)} files to {args.output}/")


if __name__ == "__main__":
    main()