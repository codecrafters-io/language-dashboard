import os

import pandas as pd
import yaml

from EolAPI import EOLApi
from GithubAPI import GithubAPI
from meta import Challenges, Language, Status, VersionSupport
from SemVer import SemVerComparison
from utils import get_days_from_today, parse_datetime_string, parse_dockerfile_names

df = pd.DataFrame()
gh = GithubAPI()
eol = EOLApi()

repo_owner = "codecrafters-io"
docker_file_path = "dockerfiles"
repositories = list(c.value for c in Challenges)


Languages: dict[str, Language] = {}


file_path = r"./data.yaml"
assert os.path.exists(file_path), "Version data file not found."
with open(file_path, "r") as file:
    data = yaml.safe_load(file)


for key in data:
    v1, date = (data[key]["cycle"], data[key]["releaseDate"])
    version = SemVerComparison.parse_version(v1)
    datetime = parse_datetime_string(date)
    Languages[key] = Language(name=key, version=version, updated_on=datetime)
print(len(Languages))


v: list[VersionSupport] = []


for challenge in Challenges:
    repo_name = challenge.value
    r = gh.get_repo_contents(repo_owner, repo_name, "dockerfiles")
    d = parse_dockerfile_names(r.json())

    for language in d:
        if language not in Languages:
            data = eol.fetch_data(language)
            latest_version, latest_version_release_date = eol.parse_response(
                data
            )

            version = SemVerComparison.parse_version(latest_version)
            datetime = parse_datetime_string(latest_version_release_date)
            Languages[language] = Language(
                name=language, version=version, updated_on=datetime
            )

        version = d[language]
        lang = Languages[language]
        v.append(
            VersionSupport(
                language=lang,
                challenge=challenge,
                version=version,
                days_since_update=get_days_from_today(lang.updated_on),
                status=Status.UNKNOWN,
            )
        )

output_file = "dashboard.md"
with open(output_file, "w") as file:
    file.write("# CodeCrafters Challenge Language Support\n")

for language in Languages:
    filtered = list(filter(lambda x: x.language == Languages[language], v))

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
        language = entry.language.name
        mj, mn = Languages[language].version
        v1 = f"v{mj}.{mn}"
        mj, mn = entry.version
        v2 = f"v{mj}.{mn}"
        df.loc[challenge_name, f"{language}_release_cycle"] = v1
        df.loc[challenge_name, f"{language}_supported_cycle"] = v2
        df.loc[challenge_name, "support_status"] = entry.status.value

    with open(output_file, "a") as file:
        file.write(f"## {language}\n")
        file.write(df.to_markdown())
        file.write("\n\n")
