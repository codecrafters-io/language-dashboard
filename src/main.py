import pandas as pd

from src.EolAPI import EOLApi
from src.GithubAPI import GithubAPI
from src.meta import Challenges, Languages, Status, VersionSupport
from src.SemVer import SemVer
from src.utils import (get_days_from_today, get_or_fetch_language_cycle,
                       get_status_from_elapsed_time, parse_dockerfile_names,
                       parse_version_data_from_yaml)

gh = GithubAPI()
eol = EOLApi()

local_version_data_file_path = r"./data.yaml"
repo_owner = "codecrafters-io"
docker_file_path = "dockerfiles"
repositories = list(c.value for c in Challenges)

all_language_cycle_data = parse_version_data_from_yaml(
    local_version_data_file_path
)
all_version_support_data: list[VersionSupport] = []


for challenge in Challenges:
    repo_name = challenge.value
    response = gh.get_repo_contents(repo_owner, repo_name, docker_file_path)
    dockerfiles = parse_dockerfile_names(response.json())

    for language in dockerfiles:
        language_cycle = get_or_fetch_language_cycle(
            language, eol, all_language_cycle_data
        )
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

output_file = "dashboard.md"
with open(output_file, "w") as file:
    file.write("# CodeCrafters Challenge Language Support\n")

for key in Languages:
    language = key.value
    filtered_version_support_data = filter(
        lambda x: x.language == all_language_cycle_data[language],
        all_version_support_data,
    )

    for version_support in filtered_version_support_data:
        comparison = SemVer.compare_versions(
            version_support.language.version, version_support.version
        )
        match comparison:
            case 0:
                version_support.status = Status.UP_TO_DATE
            case 1:
                version_support.status = get_status_from_elapsed_time(
                    version_support.days_since_update
                )

    df = pd.DataFrame()

    for version_support in filtered_version_support_data:
        challenge_name = version_support.challenge.name
        language = version_support.language.name.value
        language_obj = all_language_cycle_data[language]
        df.loc[challenge_name, f"{language}_release_cycle"] = (
            language_obj.generate_version_string()
        )
        df.loc[challenge_name, f"{language}_supported_cycle"] = (
            version_support.generate_version_string()
        )
        df.loc[challenge_name, "support_status"] = version_support.status.value

    with open(output_file, "a") as file:
        file.write(f"## {language}\n")
        file.write(df.to_markdown())
        file.write("\n\n")
