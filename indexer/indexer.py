import sys
sys.path.append("..") 

from annotator.annotator import Annotator

from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
import datetime
from urllib import request
from urllib.error import *
from urllib.parse import urljoin

annotator = Annotator()
es = Elasticsearch()

def clean_url(url):
	'''Remove the protocol, url parameters, and ID selectors'''
	if '://' in url:
		url = ':'.join(url.split(':')[1:])
	if '?' in url:
		url = '?'.join(url.split('?')[:1])
	if '#' in url:
		url = '#'.join(url.split('#')[:1])
	return(url)

def get_story_title(url):
	'''Remove the little trailing bits that websites add to article titles.
	for example:
	Andrew McCabe turned over memo on Comey firing to Mueller - CNNPolitics
	becomes:
	Andrew McCabe turned over memo on Comey firing to Mueller
	'''
	try:
		with request.urlopen(url) as p:
			html = p.read()
	except HTTPError:
		return(None)
	soup = BeautifulSoup(html, "lxml")
	try:
		title = soup.find_all('title')[0].contents[0]
	except IndexError: # untitled site
		title = ''
	if '|' in title:
		title = title.split('|')[0]
	elif ' - ' in title:
		title = title.split(' - ')[0]
	elif '«' in title:
		title = title.split('«')[0]
	title = title.strip(' ')
	return(title)

async def create_document(index, url=None, title=None, description=None, refresh=False):
	if url is None and (title is None or len(title) < 2):
		return(None)
	if title is None or len(title) < 2:
		title = get_story_title(url)
		if title is None:
			return(None)
	document = {
		'url': url,
		'timestamp': datetime.datetime.utcnow(),
		'title': title,
		'description': description,
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
	title = '. '.join(titles)

	machine_title = annotator.annotate(title)
	for sentence in machine_title:
		ideas.append(sentence.get_simple_parts({}, None, False))
		document = sentence.get_characteristics(document)
	if description is not None:
		machine_desc = annotator.annotate(description)
		for sentence in machine_desc:
			ideas.append(sentence.get_simple_parts({}, None, False))
			document = sentence.get_characteristics(document)
	document['ideas'] = ideas
	if refresh:
		res = es.index(
			index='<'+index+'{now{YYYY-MM-dd}}>',
			body=document,
			doc_type='_doc',
			refresh="true"
		)
	else:
		res = es.index(
			index='<'+index+'{now{YYYY-MM-dd}}>',
			body=document,
			doc_type='_doc',
			refresh="false"
		)

	return({
		'index': res['_index'],
		'id': res['_id']
	})

async def index_by_url(index, url, title=None, description=None, refresh=False, check_all=True):
	# Check if the URL is already in the database and if so return the old object
	# The URL needs to be matched without protocol and without arguments
	cleaned_url = clean_url(url)
	# In order to do this an inexact match is perfomed
	query = {
		"query": {
			"match_phrase": {
				"url": cleaned_url
			}
		}
	}
	if check_all:
		search = es.search(index="*stories*", body=query)
	else:
		search = es.search(index="stories*", body=query)
	# Because this is an inexact match we need to not only check that there are matched
	# But also checj that the full path was matched
	if search['hits']['total'] == 0 or cleaned_url not in search['hits']['hits'][0]['_source']['url']:
		# There are no results or the first (and closest) match was not a complete match
		return(await(create_document(index, url, title, description, refresh)))
	else:
		# There are results and the zeroth result contains the full host and path excluding protocol and parameters
		return({
			'index': search['hits']['hits'][0]['_index'],
			'id': search['hits']['hits'][0]['_id']
		})

async def index_by_title(index, title, description=None, refresh=False, check_all=True):
	title = title.strip(' ')
	query = {
		"query": {
			"match": {
				"title.keyword": title
			}
		}
	}
	if check_all:
		search = es.search(index="*stories*", body=query)
	else:
		search = es.search(index="stories*", body=query)
	if search['hits']['total'] == 0:
		return(await(create_document(index, None, title, description, refresh)))
	else:
		return({
			'index': search['hits']['hits'][0]['_index'],
			'id': search['hits']['hits'][0]['_id']
		})

async def index(index, url=None, title=None, description=None, refresh=False, check_all=True):
	'''Indexes an article in elasticsearch and returns an ID dictionary'''
	if url is None and (title is None or len(title) < 2):
		return(None)
	if url is not None:
		return(await(index_by_url(index, url, title, description, refresh, check_all)))
	else:
		return(await(index_by_title(index, title, description, refresh, check_all)))
