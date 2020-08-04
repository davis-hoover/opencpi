# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

Name:      opencpi-doc
Version:   %{RPM_VERSION}
Release:   %{RPM_RELEASE}%{?RELEASE_TAG}%{?COMMIT_TAG}%{?dist}
BuildArch: noarch
Source0:   %{name}-%{RPM_VERSION}.tar.gz

Summary:   OpenCPI Documentation
Group:     Documentation

License:   LGPLv3+
URL:       https://opencpi.org
Vendor:    OpenCPI
Packager:  OpenCPI <discuss@lists.opencpi.org>

Requires:  man

%description
Man pages, PDFs and HTML index files installed into %{_pkgdocdir}
%if "0%{?COMMIT_HASH}"
Release ID: %{COMMIT_HASH}
%endif

%prep
%setup -c -q

%build
# Nothing to build

%install
%{__mkdir_p} %{buildroot}/opt/opencpi/doc/
%{__cp} -r . %{buildroot}/opt/opencpi/doc/

%files
%defattr(0444,root,root,0555)
%dir /opt/opencpi/doc
%doc /opt/opencpi/doc/*
