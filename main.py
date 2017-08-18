# Natural Language Toolkit: code_traverse
# add collection into list for back searching
import nltk, time
try:
	import urllib2
except ImportError:
	import urllib.request as urllib2

from nltk.corpus import wordnet as wn

from urllib.parse import urljoin

import praw

from news import SITES, SOURCES

from bs4 import BeautifulSoup

from string import Template

cp = nltk.data.load('chunkers/maxent_ne_chunker/english_ace_multiclass.pickle')

tagger = nltk.data.load('taggers/maxent_treebank_pos_tagger/english.pickle')

reddit = praw.Reddit('sourcesbot', user_agent='web:sourcesbot by /u/michaelh115')

TEMPLATE = '''Other sources for this story:

$sources

Opinions:

$opinions

__________
To report a source or opinion article that is not relevant reply "Irrelevant <source or opinion> and the number

Note on opinions: due to sourcing and how articles are matched the opinions may not be terrribly diverse.  

This bot was written by $writer and the source code can be found [here]($code)

To rant about how biased this bot is go [here](#)'''

def read_words(n, key, r):
	name = ''
	for l in n.leaves():
		name += l[0] + ' '
	name = name[:len(name)-1]
	r[key].append(name)
	return(r)

def get_characteristics(t, r):
	for n in t:
		if type(n) == nltk.tree.Tree:
			if n.label() == 'GPE':
				r = read_words(n, 'places', r)
			elif n.label() == 'ORGANIZATION':
				r = read_words(n, 'organizations', r)
			elif n.label() == 'PERSON':
				r = read_words(n, 'people', r)
			else:
				get_characteristics(n, r)
		else:
			if len(n) == 2:
				if n[1].startswith('N'):
					r['things'].append(n[0].lower())
				elif n[1].startswith('V'):
					r['actions'].append(n[0].lower())
	return(r)

def uin(cp):
	s = input('story: ')
	story = nltk.word_tokenize(s)
	story = tagger.tag(story)
	return(cp.parse(story))

def get_aljazeera():
	r = urllib2.urlopen("http://www.aljazeera.com/")
	html = r.read()
	soup = BeautifulSoup(html, "html.parser")
	return(soup.find_all('a'))


def get_bbc():
	r = urllib2.urlopen("http://www.bbc.com/news")
	html = r.read()
	soup = BeautifulSoup(html, "html.parser")
	return(soup.find_all('a', {'class':'gs-c-promo-heading'}))

def get_guardian():
	r = urllib2.urlopen("https://www.theguardian.com")
	html = r.read()
	soup = BeautifulSoup(html, "html.parser")
	return(soup.find_all('a', {'class':'js-headline-text'}))

def get_wapo():
	r = urllib2.urlopen("http://www.washingtonpost.com")
	html = r.read()
	soup = BeautifulSoup(html, "html.parser")
	return(soup.find_all('a', {'data-pb-field':'web_headline'}))

def strip(s):
	s = s.lower()
	if s.endswith('ed'):
		return(s[:len(s)-2])
	elif s.endswith('es'):
		return(s[:len(s)-2])

def calc_overlap(title, s, cp):
	story = nltk.word_tokenize(title)
	story = cp.parse(tagger.tag(story))
	# The default r NEEDS to be passed or the function below becomes possessed
	new = get_characteristics(story, {'places':[], 'people':[], 'organizations':[], 'things':[], 'actions':[]})
	overlap = 0
	for k in new.keys():
		for i in new[k]:
			overlap += i in s[k]
	return(overlap)

class story:
	def __init__(self, title, url, score, opinion=False):
		self.title = title
		self.url = url
		self.score = score
		self.opinion = opinion

def score_stories(s, wc, cp, source):
	stories = []
	for h in wc:
		try:
			if source == 'http://www.bbc.com/news':
				try:
					o = calc_overlap(h.contents[0].contents[0], s, cp)
					title = h.contents[0].contents[0]
				except TypeError:
					o = calc_overlap(h.contents[1].contents[0], s, cp)
					title = h.contents[1].contents[0]
			elif source == 'https://www.theguardian.com':
				try:
					o = calc_overlap(h.contents[0], s, cp)
					title = h.contents[0]
				except TypeError:
					if str(h.contents[0].contents[0]).startswith('<'):
						o = calc_overlap(h.contents[1].contents[0], s, cp)
						title = h.contents[1].contents[0]
					else:
						o = calc_overlap(h.contents[0].contents[0], s, cp)
						title = h.contents[0].contents[0]
			elif source == 'http://www.aljazeera.com/':
				try:
					if str(h.contents[0]).startswith('<'):
						try:
							o = calc_overlap(h.contents[0].contents[0], s, cp)
							title = h.contents[0].contents[0]
						except TypeError:
							o = 0
					else:
						o = 0
				except IndexError: # malformed HTML
					o = 0
			else:
				o = calc_overlap(h.contents[0], s, cp)
				title = h.contents[0]
			if o > 1:
				url = h['href']
				if url.startswith('/'):
					url = urljoin(source, url)
				stories.append({'title':title, 'url':url, 'score': o})
			#t += list(h.children)[0].contents[0]
		except AttributeError:
			pass
	return(stories)

def process(title):
	stories = []
	s = nltk.word_tokenize(title)
	s = tagger.tag(s)
	s = cp.parse(s)
	# The default r NEEDS to be passed or the function below becomes possessed
	s = get_characteristics(s, {'places':[], 'people':[], 'organizations':[], 'things':[], 'actions':[]})
	wp = get_wapo()
	stories += (score_stories(s, wp, cp, 'https://washingtonpost.com'))
	bbc = get_bbc()
	stories += score_stories(s, bbc, cp, 'http://www.bbc.com/news')
	guard = get_guardian()
	stories += score_stories(s, bbc, cp, 'https://www.theguardian.com')
	aljazeera = get_aljazeera()
	stories += score_stories(s, aljazeera, cp, 'http://www.aljazeera.com/')
	return(stories)

def test_in_sites(url):
	for s in SITES:
		if s in url:
			return(True)
	return(False)

def template_links(stories):
	out = ''
	urls = []
	for s in sorted(stories, key=lambda k: k['score']):
		if s['url'] not in urls:
			out += f'- [{s["title"]}]({s["url"]})\n'
			urls.append(s['url'])
	return(out)

for s in reddit.subreddit('test').hot(limit = 10):
	if test_in_sites(s.url):
		with urllib2.urlopen(s.url) as p:
			html = p.read()
		soup = BeautifulSoup(html, "html.parser")
		title = soup.find_all('title')[0].contents[0]
		if '|' in title:
			title = title.split('|')[0]
		elif ' - ' in title:
			title = title.split(' - ')[0]
		stories = process(title)
		temp = Template(TEMPLATE)
		sources = template_links(stories)
		s.reply(temp.substitute(sources=sources, opinions='- Not Yet\n', writer='/u/michaelh115', code='https://github.com/michardy/sources-bot'))
