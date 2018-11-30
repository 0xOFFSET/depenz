#!/bin/bash


if [ $UID -ne 0 ]
then
	echo "error, Run with root privilege .. "
	exit 1
fi


PACKAGE_NAME=$1

if [ -z "$PACKAGE_NAME" ]
then
	echo "error, specify a deb package in the current directory to install"
	exit 1
fi


DPKGInstall()
{
	DPKG_OUTPUT=$((dpkg --install $PACKAGE_NAME) 2>&1 )

	if [ $? -eq 0 ]
	then
		echo $DPKG_OUTPUT
		echo "Succuess Installation ! No dependencies needed :)"
	fi
}


GetDependencies()
{
	
	MAIN_DEPS=$(echo $DPKG_OUTPUT\
	 | grep	-Eo "dpkg(.+)however"\
	 | sed -e '/./!Q' \
	 | awk -F' ' 'NF {print $11}' \
	 | awk -F';' 'NF {print $1}'
	 	)
}











