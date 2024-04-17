import datetime

import pandas as pd
from loguru import logger

from src.EolAPI import EOLApi
from src.GithubAPI import GithubAPI
from src.meta import Challenges, Languages, Status, VersionSupport
from src.SemVer import SemVer
from src.utils import (get_days_from_today, get_or_fetch_language_cycle,
                       get_status_from_elapsed_time, parse_dockerfile_names,
                       parse_version_data_from_yaml)


@logger.catch
def main() -> None:
    gh = GithubAPI()
    eol = EOLApi()
    logger.debug(
        f"Starting run at {datetime.datetime.now(datetime.timezone.utc).isoformat()}"
    )

    local_version_data_file_path = r"./data.yaml"
    repo_owner = "codecrafters-io"
    docker_file_path = "dockerfiles"

    all_language_cycle_data = parse_version_data_from_yaml(
        local_version_data_file_path
    )
    all_version_support_data: list[VersionSupport] = []

    for challenge in Challenges:
        repo_name = challenge.value
        logger.debug(f"Processing: {repo_name}")
        response = gh.get_repo_contents(
            repo_owner, repo_name, docker_file_path
        )
        dockerfiles = parse_dockerfile_names(response.json())
        logger.debug(
            f"Data fetched for: {repo_name}, found: {len(dockerfiles)} languages"
        )
        for language in dockerfiles:
            language_cycle = get_or_fetch_language_cycle(
                language, eol, all_language_cycle_data
            )
            # logger.debug(f"Processing language: {language}")
            # logger.debug(f"Language cycle: {language_cycle}")
            version = dockerfiles[language]
            all_version_support_data.append(
                VersionSupport(
                    language_cycle,
                    challenge,
                    version,
                    get_days_from_today(language_cycle.updated_on),
                    Status.UNKNOWN,
                )
            )
            logger.debug(f"Version support: {all_version_support_data[-1]}")

    output_file = "dashboard.md"
    with open(output_file, "w") as file:
        file.write("# CodeCrafters Challenge Language Support\n")

    logger.info(
        "Finished fetching and processing language and version data. Starting to render markdown"
    )
    for key in Languages:
        language = key.value
        logger.debug(f"Processing language: {language}")
        filtered_version_support_data = filter(
            lambda x: x.language == all_language_cycle_data[language],
            all_version_support_data,
        )
        logger.debug(
            f"Found {len(list(filtered_version_support_data))} entries for {language}"
        )
        df = pd.DataFrame()

        for version_support in filtered_version_support_data:
            comparison = SemVer.compare_versions(
                version_support.language.version, version_support.version
            )
            version_support.status = get_status_from_elapsed_time(
                comparison, version_support.days_since_update
            )

            challenge_name = version_support.challenge.name
            language_cycle = all_language_cycle_data[language]
            df.loc[challenge_name, f"{language}_release_cycle"] = (
                language_cycle.generate_version_string()
            )
            df.loc[challenge_name, f"{language}_supported_cycle"] = (
                version_support.generate_version_string()
            )
            df.loc[challenge_name, "support_status"] = (
                version_support.status.value
            )

        with open(output_file, "a") as file:
            file.write(f"## {language}\n")
            file.write(df.to_markdown())
            file.write("\n\n")

        logger.debug(f"Finished rendering table for language: {language}")


if __name__ == "__main__":
    main()
