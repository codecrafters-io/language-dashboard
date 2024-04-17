import functools
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import yaml
from loguru import logger

from src.eol_api import EOLApi
from src.sem_ver import SemVer


class Challenges(Enum):
    REDIS = "build-your-own-redis"
    GIT = "build-your-own-git"
    SQLITE = "build-your-own-sqlite"
    DNS_SERVER = "build-your-own-dns-server"
    HTTP_SERVER = "build-your-own-http-server"
    BITTORRENT = "build-your-own-bittorrent"
    GREP = "build-your-own-grep"
    DOCKER = "build-your-own-docker"


class Status(Enum):
    UP_TO_DATE = "✅"
    BEHIND = "⚠️"
    OUTDATED = "❌"
    NOT_SUPPORTED = "❓"
    UNKNOWN = "🥑"


class Languages(Enum):
    go = "Go"
    rust = "Rust"
    python = "Python"
    nodejs = "Javascript"
    cpp = "C++"
    dotnet = "C#"
    java = "Java"
    haskell = "Haskell"
    ruby = "Ruby"
    c = "C"
    elixir = "Elixir"
    php = "PHP"
    clojure = "Clojure"
    crystal = "Crystal"
    deno = "Typescript"
    gleam = "Gleam"
    zig = "Zig"
    kotlin = "Kotlin"
    nim = "Nim"
    swift = "Swift"


@dataclass
class VersionedItem:
    version: tuple[int, int]

    def generate_version_string(self) -> str:
        """Generate a version string from the version tuple."""
        return f"v{self.version[0]}.{self.version[1]}"

    def set_version(self, version: str) -> None:
        """Set the version from a version string."""
        self.version = SemVer.parse_version(version)


@dataclass
class Language(VersionedItem):
    name: Languages
    updated_on: datetime

    def __repr__(self) -> str:
        return f"{self.name.value} {self.generate_version_string()} updated at {self.updated_on.date()}"


@dataclass
class VersionSupport(VersionedItem):
    language: Language
    challenge: Challenges
    days_since_update: int
    status: Status

    def __repr__(self) -> str:
        return f"{self.challenge.name}:{self.language.name.name} => {self.generate_version_string()}"


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


def parse_dockerfile_names(
    data: list[dict[str, str]]
) -> dict[str, tuple[int, int]]:
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
    logger.debug(f"Reading version data from {file_path}")
    language_cycle_data: dict[str, Language] = {}

    assert os.path.exists(file_path), "Version data file not found."
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    logger.info(f"Data read from file for languages: {data.keys()}")

    for language, version_data in data.items():
        version_string, date_string = version_data.values()
        version = SemVer.parse_version(version_string)
        dt = parse_datetime_string(date_string)
        language_cycle_data[language] = Language(
            name=Languages[language], version=version, updated_on=dt
        )

    logger.debug(f"Read and parsed data from file: {language_cycle_data}")
    return language_cycle_data


def get_or_fetch_language_cycle(
    language: str, eol: EOLApi, language_cycle_data: dict[str, Language]
) -> Language:
    if language not in language_cycle_data:
        eol_data = eol.fetch_data(language)
        latest_version, latest_version_release_date = eol.parse_response(
            eol_data
        )

        version = SemVer.parse_version(latest_version)
        timestamp = parse_datetime_string(latest_version_release_date)
        language_cycle_data[language] = Language(
            version, Languages[language], timestamp
        )
        logger.debug(language_cycle_data[language])

    return language_cycle_data[language]


def get_status_from_elapsed_time(
    version_comparison_int: int, elapsed_time: int
) -> Status:
    # if version_comparison_int == 0: Same version
    # If version_comparison_int == 1: New version available
    match version_comparison_int:
        case 0:
            return Status.UP_TO_DATE
        case 1:
            if elapsed_time <= 14:
                return Status.UP_TO_DATE
            elif elapsed_time <= 90:
                return Status.BEHIND
            else:
                return Status.OUTDATED
        case _:
            return Status.UNKNOWN


def copy_template_to_readme(template_file: str, output_file: str) -> None:
    with open(template_file, "r") as file:
        template = file.read()
    with open(output_file, "w") as file:
        file.write(template)


def format_course_name(name: str) -> str:
    if "_" in name:
        parts = name.split("_")
        return parts[0].upper() + " " + parts[1].lower()
    return name.capitalize()
