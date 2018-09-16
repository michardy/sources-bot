try:
	import urllib2 as request
	from urllib2 import HTTPError
	from urlparse import urlparse, urljoin
	import robotparser
except ImportError:
	from urllib import request
	from urllib.parse import urlparse, urljoin
	from urllib.error import *
	from urllib import robotparser

import pickle
import time
import http.client

# The Washington Post has weird servers
# this number only needs to be 120
http.client._MAXHEADERS = 200

class Request():
	def __init__(self, ua=None):
		self.__robots = {}
		if ua is not None:
			self._user_agent = ua
		else:
			self._user_agent = "sourcesbot-crawler / 2.0 (url)"

	def __check_robots(self, url):
		loc = urlparse(url).netloc
		path = urlparse(url).path
		if loc not in self.__robots:
			self.__robots[loc] = robotparser.RobotFileParser(
				urljoin(loc, '/robots.txt')
			)
			self.__robots[loc].read()
		if time.time()-self.__robots[loc].mtime() > 60*30:
			self.__robots[loc].read()
		return(self.__robots[loc].can_fetch(self._user_agent, url))

	def get(self, url):
		if self.__check_robots(url):
			req = request.Request(url)
			req.add_header('User-Agent', self._user_agent)
			try:
				with request.urlopen(req) as r:
					return(r.read())
			except HTTPError:
				return(None)
		else:
			return(None)
