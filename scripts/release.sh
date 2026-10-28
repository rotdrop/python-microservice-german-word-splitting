#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 VERSION (for example: 0.8.0)" >&2
  exit 2
}

[[ $# -eq 1 ]] || usage
version=$1
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || usage

repo_root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
cd "$repo_root"

if [[ $(git branch --show-current) != main ]]; then
  echo "Release must be run from the main branch." >&2
  exit 1
fi

if [[ -n $(git status --porcelain) ]]; then
  echo "Working tree must be clean before releasing." >&2
  exit 1
fi

tag="v$version"
package_version=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml)
if [[ $package_version != "$version" ]] ||
  ! head -1 CHANGELOG.md | grep -Fq "## [$version] -" ||
  ! head -1 contrib/debian/changelog | grep -Fq "($version)" ||
  ! grep -Fxq "Version:        $version" contrib/rpm/german-word-splitter.spec ||
  ! grep -Fxq "pkgver=$version" contrib/arch/PKGBUILD; then
  echo "Release version $version does not match the project and package metadata." >&2
  exit 1
fi

if git show-ref --verify --quiet "refs/tags/$tag"; then
  echo "Tag $tag already exists locally." >&2
  exit 1
fi

remote_tag=$(git ls-remote --tags origin "refs/tags/$tag")
if [[ -n $remote_tag ]]; then
  echo "Tag $tag already exists on origin." >&2
  exit 1
fi

git tag -a "$tag" -m "Release $tag"
git push origin "$tag"
