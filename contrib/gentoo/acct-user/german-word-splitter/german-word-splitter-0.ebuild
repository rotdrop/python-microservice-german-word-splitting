# Copyright 2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

inherit acct-user

DESCRIPTION="User for the German compound-word splitting microservice"

ACCT_USER_ID=-1
ACCT_USER_GROUPS=( german-word-splitter )
ACCT_USER_HOME=/opt/german-word-splitter
ACCT_USER_HOME_OWNER=root:german-word-splitter
ACCT_USER_HOME_PERMS=0750

acct-user_add_deps
