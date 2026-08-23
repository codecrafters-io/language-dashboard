from typing import Any

import requests
from loguru import logger

from src.eol_api import EOLApi
from src.github_api import GithubAPI
from src.sem_ver import SemVer
from src.utils import Language, LanguageRelease, parse_datetime_string

GITHUB_RELEASE_REPOS = {
    "ada": "alire-project/alire",
    "bun": "oven-sh/bun",
    "crystal": "crystal-lang/crystal",
    "gleam": "gleam-lang/gleam",
    "ocaml": "ocaml/ocaml",
    "odin": "odin-lang/Odin",
    "swift": "swiftlang/swift",
}

GITHUB_TAG_REPOS = {
    "clojure": "clojure/clojure",
    "nim": "nim-lang/Nim",
}

DART_STABLE_VERSION_URL = (
    "https://storage.googleapis.com/dart-archive/"
    "channels/stable/release/latest/VERSION"
)
ZIG_DOWNLOAD_INDEX_URL = "https://ziglang.org/download/index.json"

PRERELEASE_MARKERS = ("alpha", "beta", "rc", "preview", "snapshot")


def normalize_version_tag(language: str, tag: str) -> str | None:
    version = tag.strip()
    if language == "bun":
        version = version.removeprefix("bun-")
    elif language == "clojure":
        version = version.removeprefix("clojure-")
    elif language == "swift":
        version = version.removeprefix("swift-")
        version = version.removesuffix("-RELEASE")
    elif language == "odin":
        version = version.removeprefix("dev-")
        version = version.replace("-", ".")

    version = version.removeprefix("v")
    lowered = version.lower()
    if any(marker in lowered for marker in PRERELEASE_MARKERS):
        return None

    try:
        SemVer.parse_version(version)
    except (TypeError, ValueError):
        return None
    return version


def _commit_date(commit: dict[str, Any]) -> str:
    return str(commit["commit"]["committer"]["date"])[:10]


def fetch_github_release_version(
    gh: GithubAPI, language: str, repo: str
) -> tuple[str, str]:
    url = f"{gh.base_url}/repos/{repo}/releases/latest"
    release = gh.make_api_call(url).json()
    version = normalize_version_tag(language, str(release["tag_name"]))
    if version is None:
        raise RuntimeError(
            f"Could not parse latest GitHub release for {language}: "
            f"{release['tag_name']}"
        )
    return version, str(release["published_at"])[:10]


def fetch_github_tag_version(
    gh: GithubAPI, language: str, repo: str
) -> tuple[str, str]:
    url = f"{gh.base_url}/repos/{repo}/tags?per_page=40"
    tags = gh.make_api_call(url).json()
    for tag in tags:
        version = normalize_version_tag(language, str(tag["name"]))
        if version is None:
            continue
        commit = gh.make_api_call(tag["commit"]["url"]).json()
        return version, _commit_date(commit)
    raise RuntimeError(f"No stable GitHub tag found for {language} ({repo})")


def fetch_dart_stable_version() -> tuple[str, str]:
    response = requests.get(DART_STABLE_VERSION_URL, timeout=30)
    response.raise_for_status()
    data = response.json()
    return str(data["version"]), str(data["date"])[:10]


def fetch_zig_stable_version() -> tuple[str, str]:
    response = requests.get(ZIG_DOWNLOAD_INDEX_URL, timeout=30)
    response.raise_for_status()
    releases = response.json()
    latest_version = ""
    latest_date = ""
    latest_parsed = (-1, -1)
    for name, info in releases.items():
        if name == "master":
            continue
        version = str(info.get("version", name))
        if "dev" in version:
            continue
        try:
            parsed = SemVer.parse_version(version)
        except (TypeError, ValueError):
            continue
        if SemVer.compare_versions(parsed, latest_parsed) == 1:
            latest_parsed = parsed
            latest_version = version
            latest_date = str(info["date"])[:10]
    if not latest_version:
        raise RuntimeError("No stable Zig release found")
    return latest_version, latest_date


def _set_language_release(
    language_releases: dict[str, LanguageRelease],
    language: str,
    version: str,
    release_date: str,
    source: str,
) -> None:
    language_releases[language] = LanguageRelease(
        SemVer.parse_version(version),
        Language[language],
        parse_datetime_string(release_date),
    )
    logger.info(
        f"Updated {language} from {source}: {version} ({release_date})"
    )


def update_language_releases_from_remote_sources(
    language_releases: dict[str, LanguageRelease],
    gh: GithubAPI,
    eol: EOLApi,
) -> None:
    for language, repo in GITHUB_RELEASE_REPOS.items():
        try:
            version, release_date = fetch_github_release_version(
                gh, language, repo
            )
            _set_language_release(
                language_releases,
                language,
                version,
                release_date,
                f"GitHub {repo}",
            )
        except Exception as exc:
            logger.warning(f"Keeping data.yaml for {language}: {exc}")

    for language, repo in GITHUB_TAG_REPOS.items():
        try:
            version, release_date = fetch_github_tag_version(
                gh, language, repo
            )
            _set_language_release(
                language_releases,
                language,
                version,
                release_date,
                f"GitHub tags {repo}",
            )
        except Exception as exc:
            logger.warning(f"Keeping data.yaml for {language}: {exc}")

    try:
        version, release_date = fetch_dart_stable_version()
        _set_language_release(
            language_releases, "dart", version, release_date, "Dart stable"
        )
    except Exception as exc:
        logger.warning(f"Keeping data.yaml for dart: {exc}")

    try:
        version, release_date = fetch_zig_stable_version()
        _set_language_release(
            language_releases, "zig", version, release_date, "ziglang.org"
        )
    except Exception as exc:
        logger.warning(f"Keeping data.yaml for zig: {exc}")

    try:
        version, release_date = eol.parse_response(eol.fetch_data("haskell"))
        _set_language_release(
            language_releases,
            "haskell",
            version,
            release_date,
            "endoflife.date",
        )
    except Exception as exc:
        logger.warning(f"Keeping data.yaml for haskell: {exc}")
