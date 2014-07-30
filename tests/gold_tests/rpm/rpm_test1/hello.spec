%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Summary: The "Hello World" 
Name: Intel
Version: 1.0
Release: 1
Source0: %{name}-%{version}.tar.gz
License: GPLv3+
Group: Development/Tools
BuildArch: noarch

%description 
The "Hello World" program,

Buildroot: %{_tmppath}/%{name}-%{version}-root

%prep
%setup -q

%build

%install
rm -rf %{buildroot}
mkdir -p  %{buildroot}

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
