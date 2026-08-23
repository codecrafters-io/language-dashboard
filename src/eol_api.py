from typing import Any

import requests


class EOLApi:
    def __init__(self) -> None:
        pass

    @staticmethod
    def fetch_data(language: str) -> dict[str, Any]:
        if language == "java":
            language = "openjdk-builds-from-oracle"
        elif language == "haskell":
            language = "ghc"

        url = f"https://endoflife.date/api/v1/products/{language}"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            raise RuntimeError(
                f"Language '{language}' not found on endoflife.date; "
                "add it to data.yaml"
            )
        response.raise_for_status()

        return response.json()  # type: ignore

    @staticmethod
    def parse_response(response: dict[str, Any]) -> tuple[str, str]:
        latest_cycle = response["result"]["releases"][0]
        latest_version, latest_version_release_date = (
            latest_cycle["name"],
            latest_cycle["releaseDate"],
        )

        return latest_version, latest_version_release_date
