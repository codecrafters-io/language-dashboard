import os

import requests

from utils import convert_timestamp_format


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

    def make_api_call(self, URL: str):
        headers = self.generate_headers_for_github_api()

        r = requests.get(URL, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(
                f"Failed to fetch repo contents: {r.status_code}:{r.reason}"
            )
        return r

    def get_repo_contents(
        self, repo_owner: str, repo_name: str, file_path: str = ""
    ):
        URL = f"{self.base_url}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        return self.make_api_call(URL)

    # def get_github_release_data(self, repo_owner: str, repo_name: str, release_type: str):
    #     URL = f"{self.base_url}/repos/{repo_owner}/{repo_name}/{release_type}"
    #     return self.make_api_call(URL)

    def get_tag_data(self, repo_owner: str, repo_name: str):
        URL = f"{self.base_url}/repos/{repo_owner}/{repo_name}/tags"
        return self.make_api_call(URL)

    def get_release_data(self, repo_owner: str, repo_name: str):
        URL = f"{self.base_url}/repos/{repo_owner}/{repo_name}/releases"
        return self.make_api_call(URL)

    def get_latest_cycle_release(
        self, response: list[dict[str, str]]
    ) -> tuple[str, str]:
        # Run only on release data
        # Returns latest minor version release, and its timestamp
        X = list(
            filter(
                lambda x: x[0].split(".")[-1] == "0",
                map(lambda x: (x["name"], x["published_at"]), response),
            )
        )[0]
        release_version = X[0]
        formatted_timestamp = convert_timestamp_format(X[1])
        return (release_version, formatted_timestamp)

    def get_latest_cycle_tag(
        self, response: list[dict[str, str]]
    ) -> tuple[str, str]:
        # Run only on tag data
        # Returns latest minor version release, and its timestamp
        t = list(
            filter(
                lambda x: x[0].split(".")[-1] == "0",
                map(lambda x: (x["name"], x["commit"]["url"]), response),
            )
        )[0]
        tag_commit_data = self.make_api_call(t[1])
        release_version = t[0][1:]  # vX.Y.Z -> X.Y.Z
        timestamp = tag_commit_data.json()["commit"]["author"]["date"]
        formatted_timestamp = convert_timestamp_format(timestamp)
        return (release_version, formatted_timestamp)
