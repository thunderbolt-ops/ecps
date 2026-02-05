# Tool Versions

This document captures the versions of core tools used by the
Enterprise Cloud Platform Simulator (ECPS).

All outputs below are generated directly from the local system.

---

## Git

$(git --version)
rohan@rohan-Nitro-AN515-56:~$ git --version
git version 2.34.1


## curl
rohan@rohan-Nitro-AN515-56:~$ curl --version
curl 7.81.0 (x86_64-pc-linux-gnu) libcurl/7.81.0 OpenSSL/3.0.2 zlib/1.2.11 brotli/1.0.9 zstd/1.4.8 libidn2/2.3.2 libpsl/0.21.0 (+libidn2/2.3.2) libssh/0.9.6/openssl/zlib nghttp2/1.43.0 librtmp/2.3 OpenLDAP/2.5.19
Release-Date: 2022-01-05
Protocols: dict file ftp ftps gopher gophers http https imap imaps ldap ldaps mqtt pop3 pop3s rtmp rtsp scp sftp smb smbs smtp smtps telnet tftp 
Features: alt-svc AsynchDNS brotli GSS-API HSTS HTTP2 HTTPS-proxy IDN IPv6 Kerberos Largefile libz NTLM NTLM_WB PSL SPNEGO SSL TLS-SRP UnixSockets zstd


## wget
rohan@rohan-Nitro-AN515-56:~$ wget --version
GNU Wget 1.21.2 built on linux-gnu.

-cares +digest -gpgme +https +ipv6 +iri +large-file -metalink +nls 
+ntlm +opie +psl +ssl/openssl 

Wgetrc: 
    /etc/wgetrc (system)
Locale: 
    /usr/share/locale 
Compile: 
    gcc -DHAVE_CONFIG_H -DSYSTEM_WGETRC="/etc/wgetrc" 
    -DLOCALEDIR="/usr/share/locale" -I. -I../../src -I../lib 
    -I../../lib -Wdate-time -D_FORTIFY_SOURCE=2 -DHAVE_LIBSSL -DNDEBUG 
    -g -O2 -ffile-prefix-map=/build/wget-g8YXtr/wget-1.21.2=. 
    -flto=auto -ffat-lto-objects -flto=auto -ffat-lto-objects 
    -fstack-protector-strong -Wformat -Werror=format-security 
    -DNO_SSLv2 -D_FILE_OFFSET_BITS=64 -g -Wall 
Link: 
    gcc -DHAVE_LIBSSL -DNDEBUG -g -O2 
    -ffile-prefix-map=/build/wget-g8YXtr/wget-1.21.2=. -flto=auto 
    -ffat-lto-objects -flto=auto -ffat-lto-objects 
    -fstack-protector-strong -Wformat -Werror=format-security 
    -DNO_SSLv2 -D_FILE_OFFSET_BITS=64 -g -Wall -Wl,-Bsymbolic-functions 
    -flto=auto -ffat-lto-objects -flto=auto -Wl,-z,relro -Wl,-z,now 
    -lpcre2-8 -luuid -lidn2 -lssl -lcrypto -lz -lpsl ftp-opie.o 
    openssl.o http-ntlm.o ../lib/libgnu.a 

Copyright (C) 2015 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later
<http://www.gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Originally written by Hrvoje Niksic <hniksic@xemacs.org>.
Please send bug reports and questions to <bug-wget@gnu.org>.


## Docker
rohan@rohan-Nitro-AN515-56:~$ docker --version
Docker version 29.2.1, build a5c7197


## kubectl
rohan@rohan-Nitro-AN515-56:~$ kubectl version --client
Client Version: v1.29.15
Kustomize Version: v5.0.4-0.20230601165947-6ce0bf390ce3

## kind
rohan@rohan-Nitro-AN515-56:~$ kind version
kind v0.23.0 go1.21.10 linux/amd64

## terraform

rohan@rohan-Nitro-AN515-56:~$ terraform version
Terraform v1.14.4
on linux_amd64

## helm
rohan@rohan-Nitro-AN515-56:~$ helm version
version.BuildInfo{Version:"v3.16.1", GitCommit:"5a5449dc42be07001fd5771d56429132984ab3ab", GitTreeState:"clean", GoVersion:"go1.22.7"}
