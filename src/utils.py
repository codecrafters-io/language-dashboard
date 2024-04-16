import functools
from collections import defaultdict
from datetime import datetime

from SemVer import SemVerComparison


def get_days_from_today(date: datetime) -> int:
    today = datetime.now().date()
    difference = (today - date.date()).days

    return difference


def convert_timestamp_format(input_string: str) -> str:
    input_format = "%Y-%m-%dT%H:%M:%SZ"  # Input: 2024-04-09T13:12:23Z
    output_format = "%Y-%m-%d"

    input_datetime = datetime.strptime(input_string, input_format)
    output_string = input_datetime.strftime(output_format)

    return output_string  # Output: 2024-03-04


def parse_datetime_string(date_str: str) -> datetime:
    # Accepts and parses date string in format "YYYY-MM-DD"
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj


def parse_dockerfile_names(data: list[dict[str, str]]):
    version_data: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))

    for file in data:
        file_name = file["path"].split("/")[1].removesuffix(".Dockerfile")
        language, v = file_name.split("-")
        version = SemVerComparison.parse_version(v)
        version_data[language] = max(
            version_data[language],
            version,
            key=functools.cmp_to_key(SemVerComparison.compare_versions),
        )

    return version_data
