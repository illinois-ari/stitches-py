#!/bin/bash
#fail if anything fails
set -e


rm -rf lpsolve

mkdir lpsolve
pushd lpsolve
mkdir dev
pushd dev
wget https://sourceforge.net/projects/lpsolve/files/lpsolve/5.5.2.3/lp_solve_5.5.2.3_dev_ux64.tar.gz/download
tar xvf download
#rm download
popd

mkdir java
pushd java
wget https://sourceforge.net/projects/lpsolve/files/lpsolve/5.5.2.3/lp_solve_5.5.2.3_java.zip/download
unzip download -d . 
#rm -r download

popd

mkdir jar
pushd jar

#cp /tmp/lp_solve_5.5/lpsolve55/bin/ux64/liblpsolve55.so .
cp ../dev/*.so . 
jar cvf lpsolve-native-5.5.2.3.jar ./*.so

popd

mvn install:install-file -Dfile=./java/lp_solve_5.5_java/lib/lpsolve55j.jar -DgroupId=lpsolve -DartifactId=lpsolve -Dversion=5.5.2.3 -Dpackaging=jar
mvn install:install-file -Dfile=./jar/lpsolve-native-5.5.2.3.jar -DgroupId=lpsolve -DartifactId=lpsolve-native -Dversion=5.5.2.3 -Dpackaging=jar


popd

mvn compile
