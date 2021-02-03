# -------------------------------------------------------------------
# This is a build file for the lp_solve Java wrapper stub library
# on linux platforms.
#
# Requirements and preconditions:
#
# - gcc and g++ compiler installed (I used gcc Version 3.3.1)
# - Sun JDK 1.4 installed
# - lp_solve archive (lp_solve_5.5_source.tar.gz) unpacked
#
# Change the paths below this line and you should be ready to go!
# -------------------------------------------------------------------


LPSOLVE_DIR=/tmp/lp_solve_5.5
#JDK_DIR=/usr/local/lib/jdk1.5.0_02
#JDK_DIR=/usr/lib/jvm/java-6-sun-1.6.0.10

c=g++

#determine platform (32/64 bit)
>/tmp/platform.c
echo '#include <stdlib.h>'>>/tmp/platform.c
echo '#include <stdio.h>'>>/tmp/platform.c
echo 'main(){printf("ux%d", (int) (sizeof(void *)*8));}'>>/tmp/platform.c
$c /tmp/platform.c -o /tmp/platform
PLATFORM=`/tmp/platform`
rm /tmp/platform /tmp/platform.c >/dev/null 2>&1

mkdir $PLATFORM >/dev/null 2>&1

# OK, here we go!

SRC_DIR=../src/c
INCL="-I $JDK_DIR/include -I $JDK_DIR/include/linux -I $LPSOLVE_DIR -I $SRC_DIR"

$c -fpic $INCL -c $SRC_DIR/lpsolve5j.cpp
$c -shared -Wl,-soname,liblpsolve55j.so -o $PLATFORM/liblpsolve55j.so lpsolve5j.o -L../../../lpsolve55/bin/$PLATFORM -lc -llpsolve55