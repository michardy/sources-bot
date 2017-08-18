# Natural Language Toolkit: code_traverse
# add collection into list for back searching
import nltk

import datetime

try:
	import urllib2
except ImportError:
	import urllib.request as urllib2

from urllib.parse import urljoin

import praw

from news import SITES, ENTITIES, Source

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

Note on opinions: due to sourcing and how articles are matched the opinions may not be terribly diverse.  

This bot was written by $writer and the source code can be found [here]($code).  

This bot is still very much in beta.  Feedback is is welcome.  '''

class AlJazeera(Source):
	def update(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("http://www.aljazeera.com/")
		html = r.read()
		soup = BeautifulSoup(html, "html.parser")
		self._content = soup.find_all('a')

class Bbc(Source):
	def update(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("http://www.bbc.com/news")
		html = r.read()
		soup = BeautifulSoup(html, "html.parser")
		self._content = soup.find_all('a', {'class':'gs-c-promo-heading'})

class Guardian(Source):
	def update(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("https://www.theguardian.com")
		html = r.read()
		soup = BeautifulSoup(html, "html.parser")
		self._content = soup.find_all('a', {'class':'js-headline-text'})

class Wapo(Source):
	def update(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("http://www.washingtonpost.com")
		html = r.read()
		soup = BeautifulSoup(html, "html.parser")
		self._content = soup.find_all('a', {'data-pb-field':'web_headline'})

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

def strip(s):
	s = s.lower()
	if s.endswith('ed'):
		return(s[:len(s)-2])
	elif s.endswith('es'):
		return(s[:len(s)-2])

def dedup_entities(entities):
	for t in entities:
		for e in range(len(entities[t])-1):
			if entities[t][e].lower() in ENTITIES and e+1 < len(entities):
				if entities[t][e+1].lower() in ENTITIES[entities[t][e].lower()]:
					entities[t][e] += ' '+entities[t][e+1]
					del entities[t][e+1]
	return(entities)

def calc_overlap(title, s, cp):
	story = nltk.word_tokenize(title)
	story = cp.parse(tagger.tag(story))
	# The default r NEEDS to be passed or the function below becomes possessed
	new = get_characteristics(story, {'places':[], 'people':[], 'organizations':[], 'things':[], 'actions':[]})
	new = dedup_entities(new)
	overlap = 0
	for k in new.keys():
		for i in new[k]:
			overlap += i in s[k] and len(i) > 2
	return(overlap)

class Story:
	def __init__(self, title, url, score, opinion=False):
		self.title = title
		self.url = url
		self.score = score
		self.opinion = opinion

def score_stories(s, wc, cp, source, source_url):
	stories = []
	opinions = []
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
				if url == source_url:
					pass
				if '/opinion/' in url or '/opinions/' in url or '/blogs/' in url or '/commentisfree/' in url:
					opinions.append({'title':title, 'url':url, 'score': o})
				else:
					stories.append({'title':title, 'url':url, 'score': o})
			#t += list(h.children)[0].contents[0]
		except AttributeError:
			pass
	return(stories, opinions)

def title_clean(title):
	title = title.replace('‘', "'")
	title = title.replace('’', "'")
	title = title.replace('“', '"')
	title = title.replace('”', '"')
	return(title)

def process(title, sources, url):
	title = title_clean(title)
	stories = []
	opinions = []
	s = nltk.word_tokenize(title)
	s = tagger.tag(s)
	s = cp.parse(s)
	# The default r NEEDS to be passed or the function below becomes possessed
	s = get_characteristics(s, {'places':[], 'people':[], 'organizations':[], 'things':[], 'actions':[]})
	s = dedup_entities(s)
	wp = sources['wapo'].get()
	out = score_stories(s, wp, cp, 'https://washingtonpost.com', url)
	stories += out[0]
	opinions += out[1]
	bbc = sources['bbc'].get()
	out = score_stories(s, bbc, cp, 'http://www.bbc.com/news', url)
	stories += out[0]
	opinions += out[1]
	guard = sources['guardian'].get()
	out = score_stories(s, guard, cp, 'https://www.theguardian.com', url)
	stories += out[0]
	opinions += out[1]
	aljazeera = sources['aljazeera'].get()
	out = score_stories(s, aljazeera, cp, 'http://www.aljazeera.com/', url)
	stories += out[0]
	opinions += out[1]
	return(stories, opinions)

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

sources = {'aljazeera':AlJazeera(), 'bbc':Bbc(), 'guardian':Guardian(), 'wapo':Wapo()}
for k in sources:
	sources[k].update()
for s in reddit.subreddit('news').hot(limit = 70):
	if test_in_sites(s.url):
		with urllib2.urlopen(s.url) as p:
			html = p.read()
		soup = BeautifulSoup(html, "html.parser")
		title = soup.find_all('title')[0].contents[0]
		if '|' in title:
			title = title.split('|')[0]
		elif ' - ' in title:
			title = title.split(' - ')[0]
		stories, opinions = process(title, sources, s.url)
		temp = Template(TEMPLATE)
		articles = template_links(stories)
		editorials = template_links(opinions)
		if articles or editorials:
			s.reply(temp.substitute(sources=articles, opinions=editorials, writer='/u/michaelh115', code='https://github.com/michardy/sources-bot'))
