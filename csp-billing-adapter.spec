#
# spec file for package csp-billing-adapter
#
# Copyright (c) 2023 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#

%if 0%{?suse_version} > 1500
%bcond_without libalternatives
%else
%bcond_with libalternatives
%endif
%define python python
%{?sle15_python_module_pythons}

Name:           csp-billing-adapter
Version:        0.10.0
Release:        0
Summary:        Reports marketplace billing information to CSP API
License:        Apache-2.0
Group:          Development/Languages/Python
URL:            https://github.com/SUSE-Enceladus/csp-billing-adapter
Source:         https://files.pythonhosted.org/packages/source/c/%{name}/%{name}-%{version}.tar.gz
BuildRequires:  fdupes
BuildRequires:  python-rpm-macros
BuildRequires:  %{python_module pip}
BuildRequires:  %{python_module pluggy}
BuildRequires:  %{python_module python-dateutil}
BuildRequires:  %{python_module PyYAML}
BuildRequires:  %{python_module setuptools}
BuildRequires:  %{python_module wheel}
%if %{with test}
BuildRequires:  %{python_module pytest}
BuildRequires:  %{python_module coverage}
BuildRequires:  %{python_module pytest-cov}
%endif
Requires:       python-setuptools
Requires:       python-pluggy
Requires:       python-python-dateutil
Requires:       python-PyYAML
%if %{with libalternatives}
BuildRequires:  alts
Requires:       alts
%else
Requires(post): update-alternatives
Requires(postun): update-alternatives
%endif
BuildArch:      noarch
%python_subpackages

%description
Configurable isolation layer that provides the information needed
to report billing information to the CSP API.

%package service
Summary:        The unit file for csp billing adapter
Group:          System/Management
Requires:       %{python_module csp-billing-adapter} = %{version}
# pkg-config is needed to find correct systemd unit dir
BuildRequires:  pkg-config
BuildRequires:  pkgconfig(systemd)
%{?systemd_requires}

%description service
This package contains the unti file for the csp billing adapter. It is
separated to avoid pulling systemd into container builds of the code. We only
want the dependency on systemd when the adapter runs in a VM.

%prep
%autosetup -n %{name}-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%python_clone -a %{buildroot}%{_bindir}/%{name}
%python_expand %fdupes %{buildroot}%{$python_sitelib}
mkdir -p %{buildroot}%{_unitdir}
install -m 644 systemd/csp-billing-adapter.service %{buildroot}%{_unitdir}

%check
%if %{with test}
%pytest
%endif


%post service
%{python_install_alternative %{name}}
%service_add_post csp-billing-adapter.service

%postun service
%{python_uninstall_alternative %{name}}
%service_del_postun csp-billing-adapter.service

%pre service
%python_libalternatives_reset_alternative %{name}
%service_add_pre csp-billing-adapter.service

%preun service
%service_del_preun csp-billing-adapter.service

%files %{python_files}
%license LICENSE
%doc README.md CONTRIBUTING.md CHANGES.md
%{python_sitelib}/csp_billing_adapter
%{python_sitelib}/csp_billing_adapter-%{version}*-info
%python_alternative %{_bindir}/%{name}

%files service
%{_unitdir}/csp-billing-adapter.service

%changelog
