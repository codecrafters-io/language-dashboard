import requests


class EOLApi:
    def __init__(self) -> None:
        pass

    @staticmethod
    def fetch_data(language: str) -> list[dict[str, str]]:
        url = f"https://endoflife.date/api/{language}.json"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)
        data = response.json()
        if "message" in data and data["message"] == "Product not found":
            raise RuntimeError(f"Language '{language}' not found")
        return data  # type: ignore

    @staticmethod
    def parse_response(response: list[dict[str, str]]) -> tuple[str, str]:
        latest_cycle = response[0]
        latest_version, latest_version_release_date = (
            latest_cycle["cycle"],
            latest_cycle["releaseDate"],
        )

        return latest_version, latest_version_release_date
