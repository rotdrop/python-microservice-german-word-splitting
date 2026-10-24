#!/usr/bin/env python3
"""Append authors of merged pull requests to CONTRIBUTORS.md.

Without arguments the author given in the environment (PR_AUTHOR,
PR_AUTHOR_TYPE) is added. With --all the authors of all merged pull requests
of GITHUB_REPOSITORY are added. Bots and already listed users are skipped.
Requires the gh CLI with GH_TOKEN set.
"""

import argparse
import os
import re
import subprocess
from pathlib import Path

CONTRIBUTORS = Path("CONTRIBUTORS.md")
LOGIN_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
LISTED_RE = re.compile(r"\(\[@([^\]]+)\]\(https://github\.com/", re.IGNORECASE)


def gh(*args):
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def display_name(login):
    name = gh("api", f"users/{login}", "--jq", '.name // ""')
    # The profile name is user controlled; keep it to plain text.
    return re.sub(r"[\[\]<>()`*_|\\\r\n]", "", name).strip()


def merged_authors():
    jq = '.[] | select(.merged_at != null and .user.type != "Bot") | .user.login'
    out = gh(
        "api",
        "--paginate",
        f"repos/{os.environ['GITHUB_REPOSITORY']}/pulls?state=closed&per_page=100",
        "--jq",
        jq,
    )
    return list(dict.fromkeys(out.split()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="backfill from all merged PRs")
    args = parser.parse_args()

    if args.all:
        logins = merged_authors()
    elif os.environ.get("PR_AUTHOR_TYPE") == "Bot":
        logins = []
    else:
        logins = [os.environ["PR_AUTHOR"]]

    text = CONTRIBUTORS.read_text()
    listed = {m.lower() for m in LISTED_RE.findall(text)}
    lines = []
    for login in logins:
        if not LOGIN_RE.match(login) or login.lower() in listed:
            continue
        listed.add(login.lower())
        name = display_name(login)
        link = f"[@{login}](https://github.com/{login})"
        lines.append(f"- {name} ({link})" if name else f"- {link}")

    if lines:
        CONTRIBUTORS.write_text(text.rstrip("\n") + "\n" + "\n".join(lines) + "\n")
        print("Added:", *lines, sep="\n")
    else:
        print("No new contributors.")


if __name__ == "__main__":
    main()
