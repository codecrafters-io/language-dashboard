import datetime
import json
import os
from typing import Any

from loguru import logger

from src.utils import CourseLanguageConfiguration, LanguageRelease

STATUS_FILE_PATH = "status.json"


def format_version(version: tuple[int, int] | None) -> str | None:
    if version is None:
        return None
    return f"{version[0]}.{version[1]}"


def build_language_data(
    language_releases: dict[str, LanguageRelease],
) -> dict[str, Any]:
    return {
        key: {
            "latest": format_version(release.version),
            "released_at": release.release_at.date().isoformat(),
        }
        for key, release in sorted(language_releases.items())
    }


def build_entry_data(config: CourseLanguageConfiguration) -> dict[str, Any]:
    # config.language is a LanguageRelease, whose .name is a Language enum.
    # The enum's member name ("go", "nodejs", "dotnet") is the buildpack, which
    # is what Dockerfile filenames are prefixed with.
    buildpack = config.language.name.name

    return {
        "course": config.challenge.value,
        "buildpack": buildpack,
        "current": format_version(config.version),
        "latest": format_version(config.language.version),
        "released_at": config.language.release_at.date().isoformat(),
        "status": config.status.name,
    }


def build_payload(
    language_configurations: list[CourseLanguageConfiguration],
    language_releases: dict[str, LanguageRelease],
) -> dict[str, Any]:
    entries = sorted(
        (build_entry_data(config) for config in language_configurations),
        key=lambda entry: (entry["course"], entry["buildpack"]),
    )

    return {
        "languages": build_language_data(language_releases),
        "entries": entries,
    }


def is_unchanged(file_path: str, payload: dict[str, Any]) -> bool:
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "r") as file:
            existing = json.load(file)
    except (OSError, json.JSONDecodeError):
        return False

    # generated_at is excluded so that a run which found no version changes
    # leaves the file byte-identical, and therefore produces no commit.
    existing.pop("generated_at", None)
    return bool(existing == payload)


def write_status_json(
    language_configurations: list[CourseLanguageConfiguration],
    language_releases: dict[str, LanguageRelease],
    file_path: str = STATUS_FILE_PATH,
) -> bool:
    payload = build_payload(language_configurations, language_releases)

    if is_unchanged(file_path, payload):
        logger.info(f"No version changes, leaving {file_path} untouched")
        return False

    generated_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )

    with open(file_path, "w") as file:
        json.dump({"generated_at": generated_at, **payload}, file, indent=2)
        file.write("\n")

    logger.info(
        f"Wrote {file_path} with {len(payload['entries'])} entries "
        f"across {len(payload['languages'])} languages"
    )
    return True
