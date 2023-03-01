#!/bin/sh
sudo su - <<EOF
apt-get install openjdk-8-jdk -y
echo JAVA_HOME="/usr/lib/jvm/java-8-openjdk-armhf/jre/bin/java" >> /etc/environment
EOF