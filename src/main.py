import pandas as pd

from src.EolAPI import EOLApi
from src.GithubAPI import GithubAPI
from src.meta import LANGUAGES, Challenges, Language, Status, VersionSupport
from src.SemVer import SemVerComparison
from src.utils import (get_days_from_today, parse_datetime_string,
                       parse_dockerfile_names, parse_version_data_from_yaml)

gh = GithubAPI()
eol = EOLApi()

local_version_data_file_path = r"./data.yaml"
repo_owner = "codecrafters-io"
docker_file_path = "dockerfiles"
repositories = list(c.value for c in Challenges)

language_cycle_data = parse_version_data_from_yaml(
    local_version_data_file_path
)
v: list[VersionSupport] = []


for challenge in Challenges:
    repo_name = challenge.value
    response = gh.get_repo_contents(repo_owner, repo_name, "dockerfiles")
    dockerfiles = parse_dockerfile_names(response.json())

    for language in dockerfiles:
        if language not in language_cycle_data:
            eol_data = eol.fetch_data(language)
            latest_version, latest_version_release_date = eol.parse_response(
                eol_data
            )

            version = SemVerComparison.parse_version(latest_version)
            datetime = parse_datetime_string(latest_version_release_date)
            language_cycle_data[language] = Language(
                LANGUAGES(language), version, datetime
            )

        version = dockerfiles[language]
        lang = language_cycle_data[language]
        v.append(
            VersionSupport(
                lang,
                challenge,
                version,
                get_days_from_today(lang.updated_on),
                Status.UNKNOWN,
            )
        )

output_file = "dashboard.md"
with open(output_file, "w") as file:
    file.write("# CodeCrafters Challenge Language Support\n")

for l in LANGUAGES:
    language = l.value
    filtered = list(
        filter(lambda x: x.language == language_cycle_data[language], v)
    )

    for entries in filtered:
        ref = entries.language
        compare = SemVerComparison.compare_versions(
            ref.version, entries.version
        )
        match compare:
            case 0:
                entries.status = Status.UP_TO_DATE
            case 1:
                if entries.days_since_update < 365:
                    entries.status = Status.OUTDATED
                if entries.days_since_update <= 14:
                    entries.status = Status.UP_TO_DATE
                elif entries.days_since_update <= 90:
                    entries.status = Status.BEHIND
                else:
                    entries.status = Status.OUTDATED

    df = pd.DataFrame()

    for entry in filtered:
        challenge_name = entry.challenge.name
        language = entry.language.name.value
        language_obj = language_cycle_data[language]
        df.loc[challenge_name, f"{language}_release_cycle"] = (
            language_obj.generate_version_string()
        )
        df.loc[challenge_name, f"{language}_supported_cycle"] = (
            entry.generate_version_string()
        )
        df.loc[challenge_name, "support_status"] = entry.status.value

    with open(output_file, "a") as file:
        file.write(f"## {language}\n")
        file.write(df.to_markdown())
        file.write("\n\n")
