# _*_ coding: utf-8 _*_

from bs4 import BeautifulSoup
import os
import platform
import json
import sys
from optparse import OptionParser

from _internal.bar_progress import bar_adaptive

from _internal.glibc import libc_ver
from _internal.utils.misc import format_size
from _internal.utils.coloredlogging import Logger


PY3K = sys.version_info >= (3, 0)
if PY3K:
    import urllib.request as ulib
    import urllib.parse as urlparse
else:
    import urllib as ulib
    import urlparse
import urllib.error


download_dir = "/tmp/temp_dependencies/"   
	# temporary directory ,where to save our downloads
	# packages 

arches  = [ 'amd64', 
			'arm64',
			'armel',
			'armhf',
			'i386',
			'mips', 
			'mipsel',
			'powerpc',
			'ppc64el',
			's390x' ]

logger = Logger()	# A CLASS for adding colors to our messages
					# utils.coloredlogging.py 


def user_agent():
	""" 
	Return a string representing the user agent.
	~ forked from "pip" project.
	"""

	data = {
		"installer" : {"name": "depener", "version": "alpha"},
	}

	if sys.platform.startswith("linux"):
		import _vendor.distro as distro
		distro_infos = dict(filter(
			lambda x: x[1],
			zip(["name", "version", "id"], distro.linux_distribution()),
		))

	if sys.platform.startswith("darwin") and platform.mac_ver()[0]:
		data["distro"] = {"name": "macOS", "version": platform.mac_ver()[0]}

	if platform.system():
		data.setdefault("system", {})["name"] = platform.system()

	if platform.release():
		data.setdefault("system", {})["release"] = platform.release()

	if platform.machine():
		data["cpu"] = platform.machine()

	data["codename"] = distro.codename()


	############################################################

	if data["codename"] == "kali-rolling":
		if data["system"]["release"].split('.')[0] == "4":
			data["codename"] = "jessie"
		else:
			data["codename"] = "wheezy"
	
	# From Kali Linux Official Documentation: The Kali Linux 
	# distribution is based on Debian Wheezy. But, as noted, 
	# Kali 2.0's new 4.0 kernel is based on Debian Jessie.	
	#
	############################################################
	# Json output 
	'''
	return "{data[installer][name]}/{data[installer][version]} {json}".format(
		data=data,
		json=json.dumps(data, separators=(",", ":"), sort_keys=True),
	)

	'''
	return data


# check the connectivity to a target host

def ConnectivityToRepos(repository):
	try:
		ulib.urlopen(repository,timeout=5)
		return True
	except Exception as e:
		return False


##########   SCRAPING PROCESSES   ############

def DebianPackagesCrawler(pkg, index=0): 
	"""
	Scraping & downloading debian packages from official mirrors
	"""
	
	url_download = "https://packages.debian.org/{0}/{1}/{2}/download"\
		.format(deb_rel, arch, pkg)
		# official site for debian DebianPackagesCrawler
	try:
		page = ulib.urlopen(url_download)
		soup = BeautifulSoup(page.read() ,'html.parser')

		if "error" not in str(soup.find("title")).lower():
			# check for availability of target package
			output = soup.find("div", {"class": "cardleft"})\
				.find_all('a', href=True)
			# several mirrors(sites/servers) to download debian packages
		else:
			raise Exception
	except Exception as e:
			logger.warning("[-] can't find ( {} )  package or mismatch in user agent data!\n".format(pkg))
			return pkg,'',''
			# placeholder for (mirror[index], filename, found) values respectively 

	mirrors = []
	for mirror in output:
		mirrors.append(mirror['href'])
	# retrieving all mirrors in cardleft div
	# "North America" mirrors

	filename = os.path.basename(mirrors[0])
	# just picking the package file name
	
	#file_exists_or_not(filename, download_dir)
	# exit if file exists
	
	def validate_mirrors(index=0):
		#############################################################
		#
		# This part to check whether the crawled mirrors are
		# working or not!
		##############################################################

		while True:
			try:
				resp = ulib.urlopen(mirrors[index], timeout=5)
				if resp.getcode() == 200 :
					break
			except IndexError:
				logger.warning("[-] No valid mirror !\n    Exiting..")
				return False
			except Exception as e:  
				index += 1
				logger.debug('[*] Trying to retrieve from another mirror !')
		return resp

	found = validate_mirrors()
	return mirrors[index], filename, found # our working mirror


__current_size = 0	# global state variable, which exists solely as a
                    # workaround against Python 3.3.0 regression
                    # http://bugs.python.org/issue16409
                    # fixed in Python 3.3.1


def callback_progress(blocks, block_size, total_size, bar_function):
    """callback function for urlretrieve that is called when connection is
    created and when once for each block

    draws adaptive progress bar in terminal/console

    use sys.stdout.write() instead of "print,", because it allows one more
    symbol at the line end without linefeed on Windows

    :param blocks: number of blocks transferred so far
    :param block_size total_size):
        # 'closure' to set : in bytes
    :param total_size: in bytes, can be -1 if server doesn't return it
    :param bar_function: another callback function to visualize progress
    """
    global __current_size
    width = 100
    if sys.version_info[:3] == (3, 3, 0):  # regression workaround
        if blocks == 0:  # first call
            __current_size = 0
        else:
            __current_size += block_size
        current_size = __current_size
    else:
        current_size = min(blocks*block_size, total_size)
    progress = bar_function(current_size, total_size, width)
    if progress:
        sys.stdout.write("\r" + progress)


def filename_fix_existing(filename):
    """Expands name portion of filename with numeric ' (x)' suffix to
    return filename that doesn't exist already.
    """
    dirname = u'.'
    name, ext = filename.rsplit('.', 1)
    names = [x for x in os.listdir(dirname) if x.startswith(name)]
    names = [x.rsplit('.', 1)[0] for x in names]
    suffixes = [x.replace(name, '') for x in names]
    # filter suffixes that match ' (x)' pattern
    suffixes = [x[2:-1] for x in suffixes
                   if x.startswith(' (') and x.endswith(')')]
    indexes  = [int(x) for x in suffixes
                   if set(x) <= set('0123456789')]
    idx = 1
    if indexes:
        idx += sorted(indexes)[-1]
    return '%s (%d).%s' % (name, idx, ext)


def downloaded_url(url, filename, bar=bar_adaptive):

	# set progress monitoring callback
	def callback_charged(blocks, block_size, total_size):
		# 'closure' to set bar drawing function in callback
		callback_progress(blocks, block_size, total_size, bar_function=bar)

	if bar:
		callback = callback_charged
	else:
		callback = None

	if PY3K:
		# Python 3 can not quote URL as needed
		binurl = list(urlparse.urlsplit(url))
		binurl[2] = urlparse.quote(binurl[2])
		binurl = urlparse.urlunsplit(binurl)
	else:
		binurl = url

	full_path = os.path.join(download_dir, filename)

	logger.info("  Downloading ", binurl)
	logger.info("at %s" %download_dir)
	(tmpfile, headers) = ulib.urlretrieve(binurl, full_path, callback)
	logger.info("") # newline 

	return headers


def main(*args, **kwargs):
	for pkg in list_of_packages:
		url, filename, found = DebianPackagesCrawler(pkg)
		if found:
			downloaded_url(url, filename)
	

if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option("-p", "--package", dest="package", default=False,
					help="supply package name")
	parser.add_option("-f", "--file", dest="file", default=False,
					help="supply file of packages")
	parser.add_option("-d", "--directory", dest="download_dir", default=False,
					help="where to download the packages")
	(options, args) = parser.parse_args()

	usage = """\
	usage: %s [option] [argument]

	options:
	-p, --package     (one package)
	-f, --file        (file of packages)\
	""" % os.path.basename(sys.argv[0]) 

	# as mention , if both (-f) & (-p) are supplied, then the priority for (-f)
	
	list_of_packages = []
	if options.file:
		try:
			with open(options.file, 'rb') as f:
				lines = f.read().splitlines()
				if PY3K:
					list_of_packages = [ i.decode('utf-8') for i in lines]
				else:
					list_of_packages = list(lines)
				# decoding issue in Python3x	

		except IOError as e:
			if e.errno == 2:
				logger.warning("No such file !\n    Exiting..")
			elif e.errno == 13:
				logger.warning("\n  Permission denied !\n Exiting..")
			exit(1)
	elif options.package:
		list_of_packages.append(options.package)
	else:
		sys.exit(usage)

	user_agent_data = user_agent()
	deb_rel = user_agent_data["codename"]
	arch    = user_agent_data["system"]["release"]

	if "64" in arch:
		arch = "amd64"
	else:
		logger.info("Please put your OS architecture: ")
		arch = str(raw_input())
		if arch not in arches:
			logger.warning("\n can't recognize this architecture!\nExiting ..")
			exit(1)

	host = "https://packages.debian.org"

	if(not ConnectivityToRepos(host)):
		logger.warning("[-] can't connect to host [{}]".format(host))
		exit(1)

	if options.download_dir:
		download_dir = options.download_dir
	try:
		os.makedirs(download_dir)
	except OSError:
		if not os.path.isdir(download_dir):
			raise

	main(list_of_packages)