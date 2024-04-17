import datetime

import pandas as pd
from loguru import logger

from src.eol_api import EOLApi
from src.github_api import GithubAPI
from src.sem_ver import SemVer
from src.utils import (Challenges, Languages, Status, VersionSupport,
                       copy_template_to_readme, format_course_name,
                       get_days_from_today, get_or_fetch_language_cycle,
                       get_status_from_elapsed_time, parse_dockerfile_names,
                       parse_version_data_from_yaml)

LOCAL_VERSION_DATA_FILE_PATH = r"./data.yaml"
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

    all_language_cycle_data = parse_version_data_from_yaml(
        LOCAL_VERSION_DATA_FILE_PATH
    )
    all_version_support_data: list[VersionSupport] = []

    for challenge in Challenges:
        repo_name = challenge.value
        logger.debug(f"Processing: {repo_name}")
        response = gh.get_repo_contents(
            REPO_OWNER, repo_name, DOCKER_FILE_PATH
        )
        dockerfiles = parse_dockerfile_names(response.json())
        logger.debug(
            f"Data fetched for: {repo_name}, found: {len(dockerfiles)} languages"
        )

        for language in dockerfiles:
            language_cycle = get_or_fetch_language_cycle(
                language, eol, all_language_cycle_data
            )
            all_version_support_data.append(
                VersionSupport(
                    dockerfiles[language],
                    language_cycle,
                    challenge,
                    get_days_from_today(language_cycle.updated_on),
                    Status.UNKNOWN,
                )
            )
            logger.debug(f"Version support: {all_version_support_data[-1]}")

    logger.info(
        "Finished fetching and processing language and version data. Starting to render markdown"
    )
    copy_template_to_readme(TEMPLATE_FILE_PATH, OUTPUT_FILE_PATH)

    for key in Languages:
        language_identifier = key.name
        language_display_name = key.value
        logger.debug(f"Processing language: {language_identifier}")
        filtered_version_support_data = list(
            filter(
                lambda x: x.language
                == all_language_cycle_data[language_identifier],
                all_version_support_data,
            )
        )
        logger.debug(
            f"Found {len(filtered_version_support_data)} entries for {language_identifier}"
        )
        df = pd.DataFrame()
        df.index.name = "Challenge"

        for version_support in filtered_version_support_data:
            comparison = SemVer.compare_versions(
                version_support.language.version, version_support.version
            )
            version_support.status = get_status_from_elapsed_time(
                comparison, version_support.days_since_update
            )

            row_id = f"{format_course_name(version_support.challenge.name)}: {version_support.status.value}"
            language_cycle = all_language_cycle_data[language_identifier]
            df.loc[row_id, "Latest Release"] = (
                language_cycle.generate_version_string()
            )
            df.loc[row_id, "Release Date"] = (
                version_support.language.updated_on.date().isoformat()
            )
            df.loc[row_id, "CodeCrafter's Version"] = (
                version_support.generate_version_string()
            )

        with open(OUTPUT_FILE_PATH, "a") as file:
            link = f"https://app.codecrafters.io/tracks/{language_identifier}"
            file.write(f"### [{language_display_name}]({link})\n")
            file.write(df.to_markdown())
            file.write("\n\n")

        logger.debug(
            f"Finished rendering table for language: {language_identifier}"
        )


if __name__ == "__main__":
    main()
