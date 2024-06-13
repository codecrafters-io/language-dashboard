import datetime

import pandas as pd
from loguru import logger

from src.eol_api import EOLApi
from src.github_api import GithubAPI
from src.sem_ver import SemVer
from src.utils import (Challenge, CourseLanguageConfiguration, Language,
                       Status, copy_template_to_readme, format_course_name,
                       get_days_from_today, get_or_fetch_language_release,
                       get_status_from_elapsed_time, parse_dockerfile_contents,
                       parse_release_data_from_yaml)

LANGUAGES_RELEASE_DATA_FILE = r"./data.yaml"
REPO_OWNER = "codecrafters-io"
DOCKER_FILE_PATH = "dockerfiles"
OUTPUT_FILE_PATH, TEMPLATE_FILE_PATH = "README.md", "TEMPLATE.md"


@logger.catch
def main() -> None:
    gh = GithubAPI()
    eol = EOLApi()
    logger.debug(
        f"Starting run at {datetime.datetime.now(datetime.timezone.utc).isoformat()}"
    )

    language_releases = parse_release_data_from_yaml(
        LANGUAGES_RELEASE_DATA_FILE
    )
    language_configurations: list[CourseLanguageConfiguration] = []

    for challenge in Challenge:
        repo_name = challenge.value
        logger.debug(f"Processing: {repo_name}")

        response = gh.get_repo_contents(
            REPO_OWNER, repo_name, DOCKER_FILE_PATH
        )
        dockerfiles = parse_dockerfile_contents(response.json())
        logger.debug(
            f"Data fetched for: {repo_name}, found: {len(dockerfiles)} languages"
        )

        for language in dockerfiles:
            language_release = get_or_fetch_language_release(
                language, eol, language_releases
            )
            language_configurations.append(
                CourseLanguageConfiguration(
                    dockerfiles[language],
                    language_release,
                    challenge,
                    Status.UNKNOWN,
                )
            )
            logger.debug(f"Version support: {language_configurations[-1]}")

    logger.info(
        "Finished fetching and processing language and version data. Starting to render markdown"
    )
    copy_template_to_readme(TEMPLATE_FILE_PATH, OUTPUT_FILE_PATH)

    for key in Language:
        language_identifier = key.name
        language_name = key.value
        logger.debug(f"Processing language: {language_identifier}")
        course_language_configuration = list(
            filter(
                lambda x: x.language == language_releases[language_identifier],
                language_configurations,
            )
        )
        logger.debug(
            f"Found {len(course_language_configuration)} entries for {language_identifier}"
        )

        for challenge in Challenge:
            if not any(
                map(
                    lambda x: x.challenge == challenge,
                    course_language_configuration,
                )
            ):
                course_language_configuration.append(
                    CourseLanguageConfiguration(
                        None,
                        language_releases[language_identifier],
                        challenge,
                        Status.NOT_SUPPORTED,
                    )
                )
        df = pd.DataFrame()
        df.index.name = "Challenge"

        # version_support.language.version --> latest version
        # version_support.version --> CC supported version
        for version_support in course_language_configuration:
            if version_support.version is not None:
                comparison = SemVer.compare_versions(
                    version_support.language.version, version_support.version
                )

                version_support.status = get_status_from_elapsed_time(
                    comparison,
                    get_days_from_today(version_support.language.release_at),
                )

            row_id = f"{format_course_name(version_support.challenge.name)}: {version_support.status.value}"
            language_release = language_releases[language_identifier]
            df.loc[row_id, "Latest Release"] = (
                language_release.generate_version_string()
            )
            df.loc[row_id, "Release Date"] = (
                version_support.language.release_at.date().isoformat()
            )
            if version_support.version is not None:
                df.loc[row_id, "CodeCrafter's Version"] = (
                    version_support.generate_version_string()
                )
            else:
                df.loc[row_id, "CodeCrafter's Version"] = "-"

        with open(OUTPUT_FILE_PATH, "a") as file:
            link = f"https://app.codecrafters.io/tracks/{language_identifier}"
            file.write(f"### [{language_name}]({link})\n")
            file.write(df.to_markdown())
            file.write("\n\n")

        logger.debug(
            f"Finished rendering table for language: {language_identifier}"
        )


if __name__ == "__main__":
    main()
