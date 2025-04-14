import scrapy
import json

class GithubSpider(scrapy.Spider):
    name = 'github_spider'
    allowed_domains = ['api.github.com']
    start_urls = ['https://api.github.com/user/repos']

    # Replace with your GitHub Personal Access Token
    token = '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'

    def start_requests(self):
        # Pass the token in the header for authentication
        headers = {
            'Authorization': f'token {self.token}',
        }
        yield scrapy.Request(url=self.start_urls[0], headers=headers, callback=self.parse)

    def parse(self, response):
        # Parse the response as JSON
        repos = json.loads(response.text)
        for repo in repos:
            # Extract repository details
            yield {
                'url': repo.get('html_url'),
                'about': repo.get('description', 'No description available'),
                'last_updated': repo.get('updated_at'),
                'languages': repo.get('language', 'Not available'),
                'commits': repo.get('commits_url')  # GitHub API requires another request to get commit count
            }

            # Optionally, fetch commit count and languages using additional API calls
            # Here, we assume commit count is available in the URL provided in 'commits_url'
            commit_url = repo.get('commits_url').split('{')[0]  # Remove the parameter part
            yield scrapy.Request(commit_url, headers={'Authorization': f'token {self.token}'}, callback=self.parse_commits, meta={'repo_url': repo.get('html_url')})

    def parse_commits(self, response):
        commits = len(json.loads(response.text))  # Commit count is the number of items in the response
        repo_url = response.meta['repo_url']
        yield {
            'url': repo_url,
            'commits': commits
        }
