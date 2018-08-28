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
from annotator import Annotator

reddit = praw.Reddit('sourcesbot', user_agent='web:sourcesbot:v0.0.2 by /u/michaelh115')

annotator = Annotator()

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
	return(title)

def get_attributes(machine_title):
	document = {
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
	for sentence in machine_title:
		document = sentence.get_characteristics(document)
	return(document)

def get_query(attributes):
	query = {
		"query": {
			"bool": {
				"should": []
			}
		}
	}
	for attribute in attributes:
		for component in attributes[attribute]:
			if attribute is in ['people', 'person_ids', 'places', 'place_ids']:
				boost = 2
			else:
				boost = 1
			match = {
				"match": {
					attribute: {
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

for s in reddit.subreddit('worldnews').hot(limit = 30):
	if test_in_sites(s.url):
		title = get_story_title(s.url)
		query = get_query(
			get_attributes(
				annotator.annotate(title)
			)
		)
		res = es.search(index='stories*', body=query)
		stories = []
		opinions = []
		for r in res['hits']['hits']:
			if r['_score'] > 6 and r['_source']['url'] != s.url:
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
			print(title)
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
