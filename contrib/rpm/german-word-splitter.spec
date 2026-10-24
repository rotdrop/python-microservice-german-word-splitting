# The package ships a self-contained virtual environment below /opt.
%global debug_package %{nil}
%global __brp_python_bytecompile %{nil}
%global __brp_strip %{nil}
%global __brp_mangle_shebangs %{nil}
%global __requires_exclude ^.*$
%global prefix_dir /opt/german-word-splitter
%global dict german_utf8_linux.dic

Name:           german-word-splitter
Version:        0.2.0
Release:        1%{?dist}
Summary:        FastAPI microservice for splitting German compound words
License:        AGPL-3.0-or-later
URL:            https://github.com/rotdrop/python-microservice-german-word-splitting
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  ca-certificates
BuildRequires:  curl
BuildRequires:  git-core
BuildRequires:  p7zip
BuildRequires:  p7zip-plugins
BuildRequires:  python3
BuildRequires:  python3-pip
BuildRequires:  systemd-rpm-macros
Requires:       python3
Requires(pre):  shadow-utils
%{?systemd_requires}

%description
A small HTTP service which splits German compound words into their
components. It is installed below %{prefix_dir} together with its own
Python virtual environment and the German dictionary, and runs as a systemd
service under the dedicated user and group german-word-splitter. Settings
are read from /etc/default/%{name}.

%prep
%autosetup

%build
# Needs network access: dictionary download.
curl -fL -o german.dic.7z "https://sourceforge.net/projects/germandict/files/latest/download"
7z x -y german.dic.7z german.dic
iconv -f ISO_8859-15 -t UTF-8 german.dic | tr -d '\r' > %{dict}

%install
# Needs network access: PyPI and GitHub.
/usr/bin/python3 -m venv %{buildroot}%{prefix_dir}/venv
%{buildroot}%{prefix_dir}/venv/bin/pip install --no-cache-dir --no-compile .
grep -rIl --null -e "%{buildroot}" %{buildroot}%{prefix_dir}/venv/bin %{buildroot}%{prefix_dir}/venv/pyvenv.cfg \
    | xargs -0 -r sed -i -e "s|%{buildroot}||g"
install -D -m 0644 %{dict} %{buildroot}%{prefix_dir}/share/%{dict}
install -D -m 0644 contrib/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
install -D -m 0644 contrib/%{name}.default %{buildroot}%{_sysconfdir}/default/%{name}
sed -i 's|^#\(GERMAN_WORD_SPLITTER_DICTIONARY=\).*|\1%{prefix_dir}/share/%{dict}|' \
    %{buildroot}%{_sysconfdir}/default/%{name}

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
    useradd -r -g %{name} -d %{prefix_dir} -M -s /sbin/nologin \
    -c "German compound-word splitting service" %{name}
exit 0

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%license LICENSE
%doc README.md
%{prefix_dir}
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/default/%{name}

%changelog
* Sat Oct 24 2026 rotdrop <1494769+rotdrop@users.noreply.github.com> - 0.2.0-1
- Update to 0.2.0.

* Sat Oct 24 2026 rotdrop <1494769+rotdrop@users.noreply.github.com> - 0.1.0-1
- Initial RPM package.
