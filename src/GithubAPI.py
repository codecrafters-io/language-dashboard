import os

import requests


class GithubAPI:
    def __init__(self):
        self.token = os.environ.get("GITHUB_API_PAT")
        self.base_url = "https://api.github.com"

    def generate_headers_for_github_api(self):
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + self.token,
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def make_api_call(self, url: str):
        headers = self.generate_headers_for_github_api()

        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(
                f"Failed to fetch repo contents: {r.status_code}:{r.reason}"
            )
        return r

    def get_repo_contents(
        self, repo_owner: str, repo_name: str, file_path: str = ""
    ):
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        return self.make_api_call(url)
