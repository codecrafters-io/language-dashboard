import re


class SemVer:
    @classmethod
    def _parse_version(cls, version: str) -> tuple[int, int, int, str]:
        # Parses the version passed in as a str,
        # Returns a tuple of major, minor, patch and prerelease.
        # If prerelease is not present, it is set to an empty string.
        # If minor or patch are not present, they are set to 0.
        parts = re.split(r"[-.]", version)
        if len(parts) < 3:
            parts += [0] * (3 - len(parts))
        major, minor, patch = map(int, parts[:3])
        prerelease = (
            parts[3] if len(parts) > 3 else ""
        )  # Should be string for every release.
        return major, minor, patch, prerelease

    @classmethod
    def parse_version(cls, version: str) -> tuple[int, int]:
        v = cls._parse_version(version)
        return v[0], v[1]

    @classmethod
    def compare_versions(
        cls, version1: tuple[int, int], version2: tuple[int, int]
    ) -> int:
        # If version1 > version2, return 1
        # Else -1, if same version return 0.
        for p1, p2 in zip(version1, version2):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0
