#!/bin/sh
# Local research tools only. No firmware build, system install or SHA operation.
# Run inside the existing Linux build image, /sources read-only and /work private.
set -eu
stage=${1:?usage: ep7_build_tools.sh binutils-or-gcc}
case "$stage" in binutils|gcc) ;; *) exit 2 ;; esac
mkdir -p /work/src /work/logs /work/install
extract() {
    archive=$1
    name=$2
    if [ ! -f "/work/src/$name.extracted" ]; then
        tar -xf "/sources/$archive" -C /work/src --no-same-owner
        touch "/work/src/$name.extracted"
    fi
}
if [ "$stage" = binutils ]; then
    extract binutils-2.45.tar.xz binutils-2.45
    mkdir -p /work/binutils-build
    cd /work/binutils-build
    if [ ! -f Makefile ]; then
        /work/src/binutils-2.45/configure --target=mn10300-elf --prefix=/work/install \
            --disable-nls --disable-werror --disable-gdb --disable-sim \
            --disable-gprof --disable-gprofng --disable-gold --disable-libctf \
            --with-system-zlib --disable-shared > /work/logs/binutils-configure.log 2>&1
    fi
    make -j4 all-gas all-ld all-binutils MAKEINFO=true > /work/logs/binutils-make.log 2>&1
    make install-gas install-ld install-binutils MAKEINFO=true > /work/logs/binutils-install.log 2>&1
    /work/install/bin/mn10300-elf-objdump --version | head -n 1
else
    test -x /work/install/bin/mn10300-elf-as
    extract gcc-13.4.0.tar.xz gcc-13.4.0
    extract mpfr-4.1.0.tar.bz2 mpfr-4.1.0
    extract mpc-1.2.1.tar.gz mpc-1.2.1
    test -e /work/src/gcc-13.4.0/mpfr || ln -s ../mpfr-4.1.0 /work/src/gcc-13.4.0/mpfr
    test -e /work/src/gcc-13.4.0/mpc || ln -s ../mpc-1.2.1 /work/src/gcc-13.4.0/mpc
    mkdir -p /work/gcc-build
    cd /work/gcc-build
    if [ ! -f Makefile ]; then
        /work/src/gcc-13.4.0/configure --target=mn10300-elf --prefix=/work/install \
            --enable-languages=c --without-headers --disable-bootstrap --disable-multilib \
            --disable-nls --disable-shared --disable-threads --disable-libssp \
            --disable-libquadmath --disable-libgomp --disable-libatomic \
            --disable-libstdcxx --disable-lto --with-newlib \
            --with-as=/work/install/bin/mn10300-elf-as \
            --with-ld=/work/install/bin/mn10300-elf-ld > /work/logs/gcc-configure.log 2>&1
    fi
    make -j4 all-gcc MAKEINFO=true > /work/logs/gcc-make.log 2>&1
    make install-gcc MAKEINFO=true > /work/logs/gcc-install.log 2>&1
    /work/install/bin/mn10300-elf-gcc --version | head -n 1
fi
