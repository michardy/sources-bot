import sys
sys.path.append("..") 

from annotator.annotator import Annotator

from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
import datetime
try:
	import urllib2
	from urlparse import urljoin
except ImportError:
	import urllib.request as urllib2
	from urllib.parse import urljoin

annotator = Annotator()
es = Elasticsearch()

def get_story_title(url):
	'''Remove the little trailing bits that websites add to article titles.
	for example:
	Andrew McCabe turned over memo on Comey firing to Mueller - CNNPolitics
	becomes:
	Andrew McCabe turned over memo on Comey firing to Mueller
	'''
	with urllib2.urlopen(url) as p:
		html = p.read()
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
	if len(titles[0]) < 20:
		title = titles[0] + '. ' + ':'.join(titles[1:])

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

async def index_by_url(index, url, title=None, description=None, refresh=False):
	query = {
		"query": {
			"match": {
				"url.keyword": url
			}
		}
	}
	search = es.search(index="*stories*", body=query)
	if search['hits']['total'] == 0:
		return(await(create_document('stories', url, title, description, refresh)))
	else:
		return({
			'index': search['hits']['hits'][0]['_index'],
			'id': search['hits']['hits'][0]['_id']
		})

async def index_by_title(index, title, description=None, refresh=False):
	title = title.strip(' ')
	query = {
		"query": {
			"match": {
				"title.keyword": title
			}
		}
	}
	search = es.search(index="*stories*", body=query)
	if search['hits']['total'] == 0:
		return(await(create_document('stories', None, title, description, refresh)))
	else:
		return({
			'index': search['hits']['hits'][0]['_index'],
			'id': search['hits']['hits'][0]['_id']
		})

async def index(index, url=None, title=None, description=None, refresh=False):
	'''Indexes an article in elasticsearch and returns an ID dictionary'''
	if url is None and (title is None or len(title) < 2):
		return(None)
	if url is not None:
		return(await(index_by_url(index, url, title, description, refresh)))
	else:
		return(await(index_by_title(index, title, description, refresh)))
