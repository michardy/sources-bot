import sys
sys.path.append("..") 

import asyncio
import praw
from bs4 import BeautifulSoup
from string import Template
from elasticsearch import Elasticsearch
try:
	import urllib2
	from urlparse import urljoin
except ImportError:
	import urllib.request as urllib2
	from urllib.parse import urljoin

from news import *
from indexer import indexer


reddit = praw.Reddit('sourcesbot', user_agent='web:sourcesbot:v0.0.2 by /u/michaelh115')

es = Elasticsearch()

TEMPLATE = '''Other sources for this story:

$sources

Opinions:

$opinions
__________
^(*Note on opinions: due to sourcing and how articles are matched the opinions may not be terribly diverse.*)
^*[feedback](https://www.reddit.com/r/sourcesbot/comments/6v0pa5/feedback/)* ^| ^*[usage](https://www.reddit.com/r/sourcesbot/wiki/index)* ^| ^*[code]($code)* ^| ^*author:* ^*$writer*'''

TEMPLATE_NFOUND = '''No acceptable matches were found
__________
^*[feedback](https://www.reddit.com/r/sourcesbot/comments/6v0pa5/feedback/)* ^| ^*[usage](https://www.reddit.com/r/sourcesbot/wiki/index)* ^| ^*[code]($code)* ^| ^*author:* ^*$writer*'''

def get_query(document):
	query = {
		"query": {
			"bool": {
				"should": [],
				"filter": {
					"range": {
						"timestamp": {
							"gte": "now-2d"
						}
					}
				}
			}
		}
	}
	keys = [
		'person_ids',
		'organizations',
		'actions',
		'places',
		'thing_ids',
		'place_ids',
		'organization_ids',
		'things',
		'people',
		'speakers'
	]
	for key in keys:
		for component in document[key]:
			if key in ['people', 'person_ids', 'places', 'place_ids']:
				boost = 2
			else:
				boost = 1
			match = {
				"match": {
					key: {
						"query": component,
						"boost": boost
					}
				}
			}
			query["query"]["bool"]["should"].append(match)
	return(query)


def test_in_sites(url):
	'''Checks if the input story is from an acceptable site.
	For example this will not return true for:
	https://entertainment.theonion.com/showrunner-disappointed-world-will-never-see-episode-wh-1826423126
	But will return true for:
	https://www.nytimes.com/2018/05/29/opinion/roseanne-canceled-abc-racist-tweets.html
	'''
	for s in SITES:
		if s in url:
			return(True)
	return(False)

def template_links(stories):
	out = ''
	urls = []
	n = 0
	for s in reversed(sorted(stories, key=lambda k: k['score'])):
		if s['url'] not in urls:
			n += 1
			out += '{n}. [{title}]({url}) ({score})\n'.format(
				n=str(n), title=s["title"], url=s["url"], score=str(s["score"])
			)
			urls.append(s['url'])
	return(out)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
for s in reddit.subreddit('worldnews').hot(limit = 30):
	if test_in_sites(s.url):
		doc_id = loop.run_until_complete(indexer.index('user-stories', url=s.url, refresh=True))
		if doc_id is None:
			continue
		query = {
			"query": {
				"match": {
					"_id": doc_id['id']
				}
			}
		}
		queries = es.search(index=doc_id['index'], body=query)
		if queries['hits']['total'] > 0:
			query = get_query(queries['hits']['hits'][0]['_source'])
			results = es.search(index="stories*", body=query)
			stories = []
			opinions = []
			for r in results['hits']['hits']:
				if r['_score'] > 9.5 and r['_source']['url'] != s.url:
					if (
						'/opinion/' in r['_source']['url'] or
						'/opinions/' in r['_source']['url'] or
						'/blogs/' in r['_source']['url'] or
						'/commentisfree/' in r['_source']['url'] or
						'/posteverything/' in r['_source']['url']
					):
						opinions.append({
							'url': r['_source']['url'],
							'title': r['_source']['title'],
							'score': r['_score']
						})
					else:
						stories.append({
							'url': r['_source']['url'],
							'title': r['_source']['title'],
							'score': r['_score']
						})
			temp = Template(TEMPLATE)
			articles = template_links(stories)
			editorials = template_links(opinions)
			if len(stories) > 0 or len(opinions) > 0:
				print(queries['hits']['hits'][0]['_source']['title'])
				print(
					temp.substitute(
						sources=articles,
						opinions=editorials,
						writer='/u/michaelh115',
						code='https://github.com/michardy/sources-bot'
					)
				)
				print()
				#s.reply(
				#	temp.substitute(
				#		sources=articles,
				#		opinions=editorials,
				#		writer='/u/michaelh115',
				#		code='https://github.com/michardy/sources-bot'
				#	)
				#)
