# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

PYTHON_COMPAT=( python3_{13..15} )

inherit git-r3 python-single-r1 systemd

DESCRIPTION="FastAPI microservice for splitting German compound words"
HOMEPAGE="https://github.com/rotdrop/python-microservice-german-word-splitting"
EGIT_REPO_URI="https://github.com/rotdrop/python-microservice-german-word-splitting"

LICENSE="AGPL-3"
SLOT="0"
IUSE="systemd"
REQUIRED_USE="${PYTHON_REQUIRED_USE}"

# The Python dependencies (including a git-only one) and the dictionary are
# fetched from the network while building, hence no network sandbox.
RESTRICT="network-sandbox"

RDEPEND="
	${PYTHON_DEPS}
	acct-group/german-word-splitter
	acct-user/german-word-splitter
"
BDEPEND="
	${PYTHON_DEPS}
	app-arch/7zip
	dev-vcs/git
	net-misc/curl
	virtual/libiconv
"

MY_PREFIX="/opt/${PN}"
DICT_NAME="german_utf8_linux.dic"

src_compile() {
	# Same steps as the Makefile targets "dictionary".
	curl -fL -o german.dic.7z \
		"https://sourceforge.net/projects/germandict/files/latest/download" || die
	7z x -y german.dic.7z german.dic || die
	iconv -f ISO_8859-15 -t UTF-8 german.dic | tr -d '\r' > "${DICT_NAME}" || die
}

src_install() {
	# The virtual environment is created inside the image and its absolute
	# paths are rewritten to the final location afterwards.
	local venv="${ED}${MY_PREFIX}/venv"
	"${PYTHON}" -m venv "${venv}" || die
	"${venv}/bin/pip" install --no-cache-dir --upgrade pip . || die
	grep -rIl --null -e "${D%/}" "${venv}/bin" "${venv}/pyvenv.cfg" \
		| xargs -0 -r sed -i -e "s|${D%/}||g" || die

	insinto "${MY_PREFIX}/share"
	doins "${DICT_NAME}"

	newins contrib/${PN}.default ${PN}.default

	# Same as the other packages: only the dictionary path is set, to the
	# installed dictionary; all other options stay commented out.
	sed -e "s|^#\(GERMAN_WORD_SPLITTER_DICTIONARY=\).*|\1${MY_PREFIX}/share/${DICT_NAME}|" \
		contrib/${PN}.default > "${T}/${PN}.etc" || die
	insinto /etc/default
	newins "${T}/${PN}.etc" ${PN}

	if use systemd; then
		systemd_dounit contrib/${PN}.service
	else
		newinitd contrib/${PN}.initd ${PN}
	fi
}

pkg_postinst() {
	elog "Settings are read from /etc/default/${PN}, see"
	elog "${MY_PREFIX}/share/${PN}.default for the available variables."
	if use systemd; then
		elog "Enable the service with: systemctl enable --now ${PN}"
	else
		elog "Enable the service with: rc-update add ${PN} default && rc-service ${PN} start"
	fi
}
