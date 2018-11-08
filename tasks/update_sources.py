#! ../venv/bin/python
# -*- coding: UTF-8 -*-

import sys
sys.path.append("..") 

import asyncio
from bs4 import BeautifulSoup
try:
	import urllib2
	from urlparse import urljoin
except ImportError:
	import urllib.request as urllib2
	from urllib.parse import urljoin

from news import *
from indexer import indexer

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

class AlJazeera():
	def __isolate_content(self, links):
		for h in links:
			desc = None
			title = ''
			try:
				if str(h.contents[0]).startswith('<'):
					if not str(h.contents[0].contents[0]).startswith('<'):
						title = h.contents[0].contents[0]
						try:
							if 'top-sec-desc' in h.parent.contents[3]['class']:
								desc = h.parent.contents[3].contents[0]
						except KeyError:
							pass
						except TypeError:
							pass
					elif not h.contents[0].contents[0].contents[0].startswith('<'):
						title = h.contents[0].contents[0].contents[0]
			except IndexError: # malformed HTML
				pass
			try:
				url = h['href']
				if url.startswith('/topics'):
					continue
				elif url.startswith('#'):
					continue
				elif url.startswith('/'):
					url = urljoin('https://www.aljazeera.com/', url)
			except KeyError: # Yes, here at Al Jazeera we use empty <a> tags!
				pass
			if not url.startswith('http') or title == '' or title == '\n':
				continue
			doc_id = loop.run_until_complete(
				indexer.index(
					'stories',
					url=url,
					title=title,
					description=desc,
					check_all=False
				)
			)

	def get(self):
		r = urllib2.urlopen("https://www.aljazeera.com/")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all('a')
		self.__isolate_content(links)

class Bbc():
	def __isolate_content(self, stories):
		self._content = []
		for s in stories:
			desc = None
			h = s.find_all('a', {'class':'gs-c-promo-heading'})
			if len(h) > 0:
				if not str(h[0].contents[0].contents[0]).startswith('<'):
					title = h[0].contents[0].contents[0]
				else:
					title = h[0].contents[1].contents[0]
				d = s.find_all('p', {'class':'gs-c-promo-summary'})
				if len(d) > 0:
					desc = d[0].contents[0]
				url = h[0]['href']
				if url == '/radio/player/bbc_world_service' or url == '/news/world_radio_and_tv':
					continue
				elif url.startswith('#'):
					continue
				elif url.startswith('/'):
					url = urljoin('https://www.bbc.com/news', url)
				doc_id = loop.run_until_complete(
				indexer.index(
						'stories',
						url=url,
						title=title,
						description=desc,
						check_all=False
					)
				)

	def get(self):
		r = urllib2.urlopen("https://www.bbc.com/news")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all('div', {'class':'gs-c-promo'})
		self.__isolate_content(links)

class Cnn():
	def __isolate_content(self, stories):
		self._content = []
		for s in stories:
			desc = None
			title = ''
			h = s.find_all('a')
			t = s.find_all({'class':'cd__headline-text'})
			if len(h) > 0:
				url = h[0]['href']
			if len(t) > 0:
				title = t[0].contents
			if url.startswith('#'):
				continue
			elif url.startswith('/'):
				url = urljoin('https://cnn.com/', url)
			doc_id = loop.run_until_complete(
				indexer.index(
					'stories',
					url=url,
					title=title,
					description=desc,
					check_all=False
				)
			)

	def get(self):
		r = urllib2.urlopen("https://cnn.com/")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all({'class':'cd__headline'})
		self.__isolate_content(links)

class Guardian():
	def __isolate_content(self, links):
		self._content = []
		for h in links:
			desc = None
			try:
				title = h.contents[0]
			except TypeError:
				if str(h.contents[0].contents[0]).startswith('<'):
					title = h.contents[1].contents[0]
				else:
					title = h.contents[0].contents[0]
			url = h['href']
			if url.startswith('#'):
				continue
			elif url.startswith('/'):
				url = urljoin('https://www.theguardian.com', url)
			doc_id = loop.run_until_complete(
				indexer.index(
					'stories',
					url=url,
					title=title,
					description=desc,
					check_all=False
				)
			)

	def get(self):
		r = urllib2.urlopen("https://www.theguardian.com")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all('a', {'class':'js-headline-text'})
		self.__isolate_content(links)

class Hill():
	def __isolate_content(self, links):
		self._content = []
		for h in links:
			desc = None
			title = ''
			try:
				if ('menu__link' not in h['class'] and 
					'hide_overlay' not in h['class']):
					if not h['class'][0].startswith('social-share-'):
						try:
							title = h.contents[0]
						except IndexError:
							pass
			except KeyError:
				try:
					title = h.contents[0]
				except IndexError:
					pass
			try:
				url = h['href']
			except KeyError:
				continue
			if url.startswith('#'):
				continue
			elif url.startswith('/'):
				url = urljoin('http://thehill.com/', url)
			doc_id = loop.run_until_complete(
				indexer.index(
					'stories',
					url=url,
					title=title,
					description=desc,
					check_all=False
				)
			)

	def get(self):
		r = urllib2.urlopen("http://thehill.com/")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all('a')
		self.__isolate_content(links)

class Nyt():
	def __isolate_content(self, stories):
		self._content = []
		for s in stories:
			desc = None
			title = ''
			url = ''
			links = s.find_all('a')
			titles = s.find_all({'class':'esl82me2'})
			descriptions = s.find_all({'class':'e1n8kpyg0'})
			bulletpoints = s.find_all({'class':'e1n8kpyg1'})
			if len(links) > 0:
				url = links[0]['href']
			if len(titles) > 0:
				title = titles[0].contents
			if len(descriptions) > 0:
				desc = descriptions[0].contents
			elif len(bulletpoints) > 0:
				for b in bulletpoints[0]:
					desc += b.contents
			if url.startswith('#'):
				continue
			elif url.startswith('/'):
				url = urljoin('https://nytimes.com/', url)
			doc_id = loop.run_until_complete(
				indexer.index(
					'stories',
					url=url,
					title=title,
					description=desc,
					check_all=False
				)
			)

	def get(self):
		r = urllib2.urlopen("https://nytimes.com/")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all({'class':'assetWrapper'})
		self.__isolate_content(links)

class Wapo():
	def __isolate_content(self, links):
		self._content = []
		for h in links:
			desc = None
			if h.name == 'a':
				title = h.contents[0]
				url = h['href']
			elif h.name == 'div':
				title = h.contents[0].contents[0]
				url = h.contents[0]['href']
				b = h.parent.find_all({'class':'blurb'})
				if len(b) == 1:
					desc = b[0].contents[0]
			if url.startswith('#'):
				continue
			elif url.startswith('/'):
				url = urljoin('https://www.washingtonpost.com', url)
			doc_id = loop.run_until_complete(
				indexer.index(
					'stories',
					url=url,
					title=title,
					description=desc,
					check_all=False
				)
			)

	def get(self):
		r = urllib2.urlopen("https://www.washingtonpost.com")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all({'class':'headline'})
		self.__isolate_content(links)
		links = soup.find_all('a', {'data-pb-field':'web_headline'})
		self.__isolate_content(links)

sources = {
	AlJazeera(),
	Bbc(),
	#Cnn(),
	Guardian(),
	Hill(),
	Nyt(),
	Wapo()
}

for source in sources:
	source.get()
