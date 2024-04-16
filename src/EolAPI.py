import requests


class EOLApi:
    def __init__(self) -> None:
        pass

    def fetch_data(self, language: str) -> list[dict[str, str]]:
        url = f"https://endoflife.date/api/{language}.json"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)
        data = response.json()
        if "message" in data and data["message"] == "Product not found":
            raise RuntimeError(f"Language '{language}' not found")
        return data

    def parse_response(
        self, response: list[dict[str, str]]
    ) -> tuple[str, str]:
        latest_cycle = response[0]
        latest_version, latest_version_release_date = (
            latest_cycle["cycle"],
            latest_cycle["releaseDate"],
        )

        return latest_version, latest_version_release_date
