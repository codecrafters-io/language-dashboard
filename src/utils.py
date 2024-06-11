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


class Challenge(Enum):
    REDIS = "build-your-own-redis"
    GIT = "build-your-own-git"
    SQLITE = "build-your-own-sqlite"
    DNS_SERVER = "build-your-own-dns-server"
    HTTP_SERVER = "build-your-own-http-server"
    BITTORRENT = "build-your-own-bittorrent"
    GREP = "build-your-own-grep"
    SHELL = "build-your-own-shell"


class Status(Enum):
    UP_TO_DATE = "✅"
    BEHIND = "⚠️"
    OUTDATED = "❗"
    NOT_SUPPORTED = "❌"
    UNKNOWN = "🥑"


class Language(Enum):
    rust = "Rust"
    go = "Go"
    python = "Python"
    c = "C"
    clojure = "Clojure"
    cpp = "C++"
    crystal = "Crystal"
    dotnet = "C#"
    elixir = "Elixir"
    gleam = "Gleam"
    haskell = "Haskell"
    java = "Java"
    kotlin = "Kotlin"
    nim = "Nim"
    nodejs = "Javascript"
    php = "PHP"
    ruby = "Ruby"
    scala = "Scala"
    swift = "Swift"
    bun = "Typescript"
    zig = "Zig"


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
class LanguageRelease(VersionedItem):
    name: Language
    release_at: datetime

    def __repr__(self) -> str:
        return f"{self.name.value} {self.generate_version_string()} updated at {self.release_at.date()}"


@dataclass
class CourseLanguageConfiguration(VersionedItem):
    language: LanguageRelease
    challenge: Challenge
    status: Status

    def __repr__(self) -> str:
        return f"{self.challenge.name}:{self.language.name} => {self.generate_version_string()}"


def get_days_from_today(date: datetime) -> int:
    today = datetime.now().date()
    difference = (today - date.date()).days

    return difference


def parse_datetime_string(date_str: str) -> datetime:
    # Accepts and parses date string in format "YYYY-MM-DD"
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj


def parse_dockerfile_contents(
    dockerfiles: list[dict[str, str]],
) -> dict[str, tuple[int, int]]:
    version_data: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))

    for file in dockerfiles:
        file_name = file["path"].split("/")[1].removesuffix(".Dockerfile")
        language, v = file_name.split("-")
        version = SemVer.parse_version(v)
        version_data[language] = max(
            version_data[language],
            version,
            key=functools.cmp_to_key(SemVer.compare_versions),
        )

    return version_data


def parse_release_data_from_yaml(file_path: str) -> dict[str, LanguageRelease]:
    logger.debug(f"Reading version data from {file_path}")
    language_releases: dict[str, LanguageRelease] = {}

    assert os.path.exists(file_path), "Version data file not found."
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    logger.info(f"Data read from file for languages: {data.keys()}")

    for language, version_data in data.items():
        version_string, date_string = version_data.values()
        language_releases[language] = LanguageRelease(
            name=Language[language],
            version=SemVer.parse_version(version_string),
            release_at=parse_datetime_string(date_string),
        )

    logger.debug(f"Read and parsed data from file: {language_releases}")
    return language_releases


def get_or_fetch_language_release(
    language: str,
    eol: EOLApi,
    language_releases: dict[str, LanguageRelease],
) -> LanguageRelease:
    if language not in language_releases:
        eol_data = eol.fetch_data(language)
        latest_version, latest_version_release_date = eol.parse_response(eol_data)

        language_releases[language] = LanguageRelease(
            SemVer.parse_version(latest_version),
            Language[language],
            parse_datetime_string(latest_version_release_date),
        )
        logger.debug(language_releases[language])

    return language_releases[language]


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
