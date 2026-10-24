#!/bin/bash
# Build a signed, static apt repository from .deb files.
#
# Usage: build-repo.sh INPUT_DIR OUTPUT_DIR
#
# INPUT_DIR contains one sub-directory per suite (the distribution codename,
# e.g. "trixie" or "resolute") holding the .deb files built for that suite.
# OUTPUT_DIR receives pool/, dists/ and, if signing is enabled, the public key.
#
# Signing: set GPG_KEY_ID to the fingerprint of a secret key in the current
# GnuPG home (it must have no passphrase). Without it the repository is left
# unsigned, which is only useful for local testing.

set -euo pipefail

if [ $# -ne 2 ]; then
	echo "Usage: $0 INPUT_DIR OUTPUT_DIR" >&2
	exit 2
fi

in_dir=$(realpath "$1")
out_dir=$(mkdir -p "$2" && realpath "$2")
component=main
keep_releases=${KEEP_RELEASES:-3}
origin=german-word-splitter

for suite_dir in "$in_dir"/*/; do
	suite=$(basename "$suite_dir")
	pool="pool/$suite/$component"
	mkdir -p "$out_dir/$pool"
	cp "$suite_dir"/*.deb "$out_dir/$pool/"

	# Keep only the newest $keep_releases versions per package and architecture.
	for deb in "$out_dir/$pool"/*.deb; do
		printf '%s %s %s %s\n' "$(dpkg-deb -f "$deb" Package)" "$(dpkg-deb -f "$deb" Architecture)" \
			"$(dpkg-deb -f "$deb" Version)" "$deb"
	done | sort -k1,2 -k3,3Vr | awk -v keep="$keep_releases" '
		{ key = $1 " " $2; if (key != last) { n = 0; last = key } if (++n > keep) print $4 }' \
		| xargs -r rm -f --

	archs=()
	for deb in "$out_dir/$pool"/*.deb; do
		archs+=("$(dpkg-deb -f "$deb" Architecture)")
	done
	mapfile -t archs < <(printf '%s\n' "${archs[@]}" | sort -u)

	for arch in "${archs[@]}"; do
		bin_dir="dists/$suite/$component/binary-$arch"
		mkdir -p "$out_dir/$bin_dir"
		(cd "$out_dir" && apt-ftparchive --arch "$arch" packages "$pool") > "$out_dir/$bin_dir/Packages"
		gzip -9kf "$out_dir/$bin_dir/Packages"
	done

	(
		cd "$out_dir"
		apt-ftparchive \
			-o "APT::FTPArchive::Release::Origin=$origin" \
			-o "APT::FTPArchive::Release::Label=$origin" \
			-o "APT::FTPArchive::Release::Suite=$suite" \
			-o "APT::FTPArchive::Release::Codename=$suite" \
			-o "APT::FTPArchive::Release::Components=$component" \
			-o "APT::FTPArchive::Release::Architectures=${archs[*]}" \
			release "dists/$suite" > "dists/$suite/Release.new"
		mv "dists/$suite/Release.new" "dists/$suite/Release"
	)

	if [ -n "${GPG_KEY_ID:-}" ]; then
		gpg --batch --yes --default-key "$GPG_KEY_ID" --clearsign \
			-o "$out_dir/dists/$suite/InRelease" "$out_dir/dists/$suite/Release"
		gpg --batch --yes --default-key "$GPG_KEY_ID" --armor --detach-sign \
			-o "$out_dir/dists/$suite/Release.gpg" "$out_dir/dists/$suite/Release"
	fi
done

if [ -n "${GPG_KEY_ID:-}" ]; then
	gpg --batch --yes --armor --export "$GPG_KEY_ID" > "$out_dir/$origin.asc"
fi

# GitHub Pages serves this as the landing page.
cat > "$out_dir/index.html" <<HTML
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>$origin apt repository</title></head>
<body>
<h1>$origin apt repository</h1>
<p>See the project README for setup instructions, or run <code>make install-apt-source</code>.</p>
<p><a href="$origin.asc">Signing key</a></p>
</body></html>
HTML
