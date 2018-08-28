#! venv/bin/python
# -*- coding: UTF-8 -*-

import datetime
import re
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from google.cloud.language import enums
try:
	import urllib2
	from urlparse import urljoin
except ImportError:
	import urllib.request as urllib2
	from urllib.parse import urljoin

from news import *
from annotator import Annotator

annotator = Annotator()
es = Elasticsearch()

class Source:
	'''Generic class describing sources and how to parse them'''
	def get(self):
		'''Generic method to scan home pages.  Must be overriden'''
		raise NotImplementedError("Must override update")

	def _process(self, url, title, desc):
		time = datetime.datetime.utcnow()
		'''Gets the characteristics of  a story and saves it'''
		query = {
			"query": {
				"match": {
					"url.keyword": url
				}
			}
		}
		if es.search(index="stories*", body=query)['hits']['total'] == 0:
			document = {
				'url': url,
				'timestamp': time,
				'title': title,
				'description': desc,
				'people': [],
				'person_ids': [],
				'places': [],
				'place_ids': [],
				'organizations': [],
				'organization_ids': [],
				'things': [],
				'thing_ids': [],
				'actions': [],
				'speakers': []
			}
			ideas = []

			# Split off '<location>:' '<speaker>:' parts
			titles = title.split(':')
			if len(titles[0]) < 20:
				title = titles[0] + '. ' + ':'.join(titles[1:])

			machine_title = annotator.annotate(title)
			for sentence in machine_title:
				ideas.append(sentence.get_simple_parts({}, None, False))
				document = sentence.get_characteristics(document)
			if desc is not None:
				machine_desc = annotator.annotate(desc)
				for sentence in machine_desc:
					ideas.append(sentence.get_simple_parts({}, None, False))
					document = sentence.get_characteristics(document)
			document['ideas'] = ideas
			es.index(index='<stories{now{YYYY-MM-dd}}>', body=document, doc_type='_doc')

class AlJazeera(Source):
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
				if url.startswith('/'):
					url = urljoin('http://www.aljazeera.com/', url)
			except KeyError: # Yes, here at Al Jazeera we use empty <a> tags!
				pass
			if not url.startswith('http') or title == '' or title == '\n':
				continue
			self._process(url, title, desc)

	def get(self):
		r = urllib2.urlopen("http://www.aljazeera.com/")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all('a')
		self.__isolate_content(links)

class Bbc(Source):
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
				if url.startswith('/'):
					url = urljoin('http://www.bbc.com/news', url)
				self._process(url, title, desc)

	def get(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("http://www.bbc.com/news")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all('div', {'class':'gs-c-promo'})
		self.__isolate_content(links)

class Guardian(Source):
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
			if url.startswith('/'):
				url = urljoin('https://www.theguardian.com', url)
			self._process(url, title, desc)

	def get(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("https://www.theguardian.com")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all('a', {'class':'js-headline-text'})
		self.__isolate_content(links)

class Hill(Source):
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
			if url.startswith('/'):
				url = urljoin('http://thehill.com/', url)
			self._process(url, title, desc)

	def get(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("http://thehill.com/")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all('a')
		self.__isolate_content(links)

class Wapo(Source):
	def __isolate_content(self, links):
		self._content = []
		for h in links:
			desc = None
			title = h.contents[0]
			if 'blurb' in h.parent.parent.contents[1]['class']:
				desc = h.parent.parent.contents[1].contents[0]
			url = h['href']
			if url.startswith('/'):
				url = urljoin('http://www.washingtonpost.com', url)
			self._process(url, title, desc)

	def get(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("http://www.washingtonpost.com")
		html = r.read()
		soup = BeautifulSoup(html, "lxml")
		links = soup.find_all('a', {'data-pb-field':'web_headline'})
		self.__isolate_content(links)

sources = {
	AlJazeera(),
	Bbc(),
	Guardian(),
	Hill(),
	Wapo()
}

for source in sources:
	source.get()
