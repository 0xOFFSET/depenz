#  Getting Linux Wild Packages
Have you ever failed to install a linux package ?Either from high or low level package managers, like *"apt-get"* and *"dpkg"* in debian.

**Depenz** is a python based script that downloads -manually-packages (dependencies) from main and official repositories. Just supply a keyword of your desired package.
It works on both python2.x & 3.x.

In the **Beta Version**, it searches for **Debian** Packages (dpkg) from packages.debian.org host.

## How it Works ?
- To download one package by name:
```$ python depenz.py -p <package_name> -d /home/user/```
- list of packages in file 
```$ python depenz.py -f <file>```
