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
%global    prefix0 /opt/opencpi
Prefix:    %{prefix0}

Summary:   OpenCPI Documentation
Group:     Documentation

License:   LGPLv3+
URL:       https://opencpi.org
Vendor:    OpenCPI
Packager:  OpenCPI <discuss@lists.opencpi.org>

Requires:  man

%description
Man pages, PDFs and HTML index files installed into %{prefix0}/doc

%{?RPM_HASH:ReleaseID: %{RPM_HASH}}

%prep

%build

%install
cd %{RPM_OPENCPI}
set -e
rm -rf %{buildroot}%{prefix0}
./packaging/prepare-rpm-doc-files.sh %{RPM_PLATFORM} "%{?RPM_CROSS:1}" \
                                     %{buildroot} %{prefix0} %{_builddir} %{RPM_VERSION}
cd %{_builddir}/opencpi-doc-%{RPM_VERSION}
%{__mkdir_p} %{buildroot}%{prefix0}
%{__cp} -r . %{buildroot}%{prefix0}

%files
%defattr(0444,root,root,0555)
%dir %{prefix0}/doc
%doc %{prefix0}/doc/*
