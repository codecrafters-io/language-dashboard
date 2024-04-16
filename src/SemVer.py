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
        return cls._parse_version(version)[0:2]

    @classmethod
    def _compare_versions(
        cls, version1: str, version2: str, skip_patch_and_prerelease=True
    ) -> int:
        # If version1 > version2, return 1
        # Else -1, if same version return 0.
        # skip_patch_and_prerelease is a flag to skip patch and prerelease comparison.
        parsed_v1 = SemVer.parse_version(version1)
        parsed_v2 = SemVer.parse_version(version2)
        if skip_patch_and_prerelease:
            v1 = parsed_v1[:2] + ("", "")
            v2 = parsed_v2[:2] + ("", "")

        for p1, p2 in zip(v1[:3], v2[:3]):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1

        # Prerelease comparison.
        if v1[3] == v2[3]:
            return 0
        elif v1[3] == "":
            return 1
        elif v2[3] == "":
            return -1
        else:
            return -1 if v1[3] < v2[3] else 1

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
