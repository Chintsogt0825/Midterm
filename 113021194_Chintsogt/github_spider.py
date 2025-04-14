import scrapy
from urllib.parse import urljoin

class GithubSpider(scrapy.Spider):
    name = "github"
    allowed_domains = ["github.com"]
    start_urls = ["https://github.com/Chintsogt0825?tab=repositories"]

    custom_settings = {
        'FEED_FORMAT': 'xml',
        'FEED_URI': 'github_repositories.xml',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'DOWNLOAD_DELAY': 2,  # Be polite to GitHub's servers
        'AUTOTHROTTLE_ENABLED': True,
    }

    def parse(self, response):
        repos = response.css('li[itemprop="owns"]')
        for repo in repos:
            name = repo.css('a[itemprop="name codeRepository"]::text').get().strip()
            relative_url = repo.css('a[itemprop="name codeRepository"]::attr(href)').get()
            url = urljoin(response.url, relative_url)
            
            about = repo.css('p[itemprop="description"]::text').get()
            about = about.strip() if about else "No description"
            
            last_updated = repo.css('relative-time::attr(datetime)').get()
            
            # Get initial language from the repo list if available
            lang_in_list = repo.css('span[itemprop="programmingLanguage"]::text').get()
            
            yield scrapy.Request(
                url,
                callback=self.parse_repo,
                meta={
                    'name': name,
                    'about': about,
                    'last_updated': last_updated,
                    'url': url,
                    'initial_language': lang_in_list.strip() if lang_in_list else None
                },
                priority=1
            )

        # Improved pagination handling
        next_buttons = response.css('a.BtnGroup-item::attr(href)').getall()
        if next_buttons and len(next_buttons) > 1:
            next_page = next_buttons[1]
            yield response.follow(next_page, self.parse, priority=0)

    def parse_repo(self, response):
        # Improved language detection
        languages = response.css('[itemprop="programmingLanguage"]::text').getall()
        if not languages and response.meta['initial_language']:
            languages = [response.meta['initial_language']]
        languages = [lang.strip() for lang in languages] if languages else ["None"]
        
        # More reliable commit count extraction
        commits_text = response.css('.commits a span::text').get()
        if not commits_text:
            commits_text = response.css('.num.text-emphasized::text').get()
        
        commits = commits_text.strip().replace(',', '') if commits_text else "None"
        
        yield {
            'name': response.meta['name'],
            'about': response.meta['about'],
            'url': response.meta['url'],
            'last_updated': response.meta['last_updated'],
            'languages': ', '.join(languages),
            'commits': commits
        }