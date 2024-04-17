from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.SemVer import SemVer


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
    OUTDATED = "⚠️"
    BEHIND = "❌"
    NOT_SUPPORTED = "❓"
    UNKNOWN = "???"


class Languages(Enum):
    GO = "go"
    RUST = "rust"
    PYTHON = "python"
    JAVASCRIPT = "nodejs"
    CPP = "cpp"
    CSHARP = "dotnet"
    JAVA = "java"
    HASKELL = "haskell"
    RUBY = "ruby"
    C = "c"
    ELIXIR = "elixir"
    PHP = "php"
    CLOJURE = "clojure"
    CRYSTAL = "crystal"
    TYPESCRIPT = "deno"
    GLEAM = "gleam"
    ZIG = "zig"
    KOTLIN = "kotlin"
    NIM = "nim"
    SWIFT = "swift"


@dataclass
class Language:
    name: Languages
    version: tuple[int, int]
    updated_on: datetime

    def generate_version_string(self) -> str:
        return f"v{self.version[0]}.{self.version[1]}"

    def set_version(self, version: str) -> None:
        self.version = SemVer.parse_version(version)

    def __repr__(self) -> str:
        return f"{self.name.value} {self.generate_version_string()} updated at {self.updated_on.date()}"


@dataclass
class VersionSupport:
    language: Language
    challenge: Challenges
    version: tuple[int, int]
    days_since_update: int
    status: Status

    def generate_version_string(self) -> str:
        return f"v{self.version[0]}.{self.version[1]}"

    def set_version(self, version: str) -> None:
        self.version = SemVer.parse_version(version)

    def __repr__(self) -> str:
        return f"{self.challenge.name}:{self.language.name.name} => {self.generate_version_string()}"
