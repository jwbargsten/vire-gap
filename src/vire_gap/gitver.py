import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitInfo:
    ref: str
    uncommitted: bool
    staged: bool
    email: str

    @property
    def name(self):
        return self.email.split("@")[0]

    @property
    def versioned(self) -> bool:
        return self.ref != "unversioned"

    def __str__(self) -> str:
        parts = [self.ref]
        if self.uncommitted:
            parts.append("uncommitted changes")
        if self.staged:
            parts.append("staged changes")
        return ", ".join(parts)

    @property
    def shortver(self) -> str:
        if not self.versioned:
            return "g0"
        flags = ("d" if self.uncommitted else "") + ("s" if self.staged else "")
        return f"g{self.ref}.{flags}" if flags else f"g{self.ref}"


def git_info(path: Path | None) -> GitInfo | None:
    if path is None:
        return None

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=path,
            capture_output=True,
            text=True,
        )

    email = git("config", "user.email").stdout.strip()

    rev = git("rev-parse", "--short", "--verify", "HEAD")
    if rev.returncode != 0:
        return GitInfo(ref="unversioned", uncommitted=False, staged=False)

    ref = rev.stdout.strip()

    # Refresh the index so the diff checks aren't fooled by stale stat info.
    git("update-index", "-q", "--ignore-submodules", "--refresh")

    # Non-zero exit code from these means "there are changes".
    uncommitted = git("diff-files", "--quiet", "--ignore-submodules").returncode != 0
    staged = (
        git(
            "diff-index",
            "--cached",
            "--quiet",
            "--ignore-submodules",
            "HEAD",
            "--",
        ).returncode
        != 0
    )

    return GitInfo(ref=ref, uncommitted=uncommitted, staged=staged, email=email)
