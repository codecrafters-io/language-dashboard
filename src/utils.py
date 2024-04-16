import functools
import os
from collections import defaultdict
from datetime import datetime

import yaml

from src.EolAPI import EOLApi
from src.meta import Language, Languages, Status
from src.SemVer import SemVer


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
        version = SemVer.parse_version(v)
        version_data[language] = max(
            version_data[language],
            version,
            key=functools.cmp_to_key(SemVer.compare_versions),
        )

    return version_data


def parse_version_data_from_yaml(file_path: str) -> dict[str, Language]:
    language_cycle_data: dict[str, Language] = {}

    assert os.path.exists(file_path), "Version data file not found."
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)

    for language, version_data in data.items():
        version_string, date_string = version_data.values()
        version = SemVer.parse_version(version_string)
        dt = parse_datetime_string(date_string)
        language_cycle_data[language] = Language(
            name=Languages(language), version=version, updated_on=dt
        )

    return language_cycle_data


def get_or_fetch_language_cycle(
    language: str, eol: EOLApi, language_cycle_data: dict[str, Language]
):
    if language not in language_cycle_data:
        eol_data = eol.fetch_data(language)
        latest_version, latest_version_release_date = eol.parse_response(
            eol_data
        )

        version = SemVer.parse_version(latest_version)
        datetime = parse_datetime_string(latest_version_release_date)
        language_cycle_data[language] = Language(
            Languages(language), version, datetime
        )

    return language_cycle_data[language]


def get_status_from_elapsed_time(elapsed_time: int) -> Status:
    if elapsed_time < 365:
        return Status.OUTDATED
    if elapsed_time <= 14:
        return Status.UP_TO_DATE
    elif elapsed_time <= 90:
        return Status.BEHIND
    else:
        return Status.OUTDATED
