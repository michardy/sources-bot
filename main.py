from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

import datetime
import re
import praw
from bs4 import BeautifulSoup
from string import Template
try:
	import urllib2
	from urlparse import urljoin
except ImportError:
	import urllib.request as urllib2
	from urllib.parse import urljoin

from news import *

client = language.LanguageServiceClient()

reddit = praw.Reddit('sourcesbot', user_agent='web:sourcesbot:v0.0.2 by /u/michaelh115')

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

class Snippet():
	def __init__(self, token):
		

class Langtree():
	def __tree_from_point(self, point, tokens):
		if point == tokens[point].dependency_edge.head_token_index:
			self._data
	def from_data(self, annotated):
		processed = [False for i in annotated.tokens]
		t = 0 # iterator for scanning flattened tree
		parent = None # parent index currently unset and it may not be 0
		while False in processed:
			token = annotated.tokens[t]

def annotate(text):
	'''Gets Google Natural Language API to annotate a sentence'''
	document = types.Document(
		content=text,
		type=enums.Document.Type.PLAIN_TEXT
	)
	features={
		"extract_syntax":				True,
		"extract_entities":				True,
		"extract_document_sentiment":	False,
		"extract_entity_sentiment":		False,
	}
	return(client.annotate_text(document=document, features=features, encoding_type='UTF8'))

def read_words(n, key, subk, r):
	name = ''
	for l in n.leaves():
		if l[0] not in NOT_GPE:
			name += l[0] + ' '
		else:
			if l[0] not in r['talley']['people']:
				r[key][subk].append(l[0].lower())
	name = name[:len(name)-1]
	if name not in r[key][subk]:
		r[key][subk].append(name.lower())
	return(r)

def find_mandatory_words_start(t, n, r):
	if n == 0: # start end
		if len(t) > 2 and len(t[n+1]) == 2:
			if t[n+1][1] == ':': # <Name>:
				r = read_words(t[n], 'mandate', 'speakers', r)
		elif len(t) > 4 and len(t[n+1]) == 2:
			if (t[n+1][1] == 'CC' and
				t[n+3].label() == 'PERSON' and
				t[n+4].label() == ':'): # <Name> and <Name>:
				r = read_words(t[n], 'mandate', 'speakers', r)
				r = read_words(t[n+3], 'mandate', 'speakers', r)
	return(r)

def find_mandatory_words_end(t, n, r):
	if n == len(t) - 1:
		if len(t)-n > 2:
			if t[n+1].label() == 'PERSON': # <Name>:
				r = read_words(t[n+1], 'mandate', 'speakers', r)
		elif len(t)-n > 4:
			if (t[n+1].label() == 'PERSON' and
				t[n+3][1] == 'CC' and
				t[n+4].label() == 'PERSON'): # <Name> and <Name>:
				r = read_words(t[n+1], 'mandate', 'speakers', r)
				r = read_words(t[n+4], 'mandate', 'speakers', r)
	return(r)

def get_characteristics(t, r):
	# Get people, places, organizations, actions and other things of signifigance
	for n in range(len(t)):
		if type(t[n]) == nltk.tree.Tree:
			if t[n].label() == 'GPE':
				r = read_words(t[n], 'talley', 'places', r)
			elif t[n].label() == 'ORGANIZATION':
				r = read_words(t[n], 'talley', 'organizations', r)
			elif t[n].label() == 'PERSON':
				r = find_mandatory_words_start(t, n, r)
				r = read_words(t[n], 'talley', 'people', r)
			else:
				get_characteristics(t[n], r)
		else:
			if len(t[n]) == 2:
				if t[n][1].startswith('N'):
					if t[n][0].lower() not in r['talley']['things']:
						r['talley']['things'].append(t[n][0].lower())
				elif t[n][1].startswith('V'):
					if (t[n][0].lower() not in r['talley']['actions'] and
						t[n][0].lower() not in USELESS_VERBS):
						r['talley']['actions'].append(t[n][0].lower())
				elif t[n][1] == ':':
					r = find_mandatory_words_end(t, n, r)
	return(r)

class Source:
	def __init__(self):
		self._time = None
		self._content = None

	def get(self):
		refresh = datetime.timedelta(minutes=30)
		if datetime.datetime.utcnow() - self._time > refresh:
			self.update()
		return(self._content)

	def update(self):
		raise NotImplementedError("Must override update")

	def _characterize(self):
		for s in range(len(self._content)):
			# The default r NEEDS to be passed or the function below becomes possessed
			c = get_characteristics(
				self._content[s]['machine_title'],
				{
					'talley':{
						'places':[],
						'people':[],
						'organizations':[],
						'things':[],
						'actions':[]
					},
					'mandate':{
						'speakers':[]
					}
				}
			)
			c = get_characteristics(self._content[s]['description'], c)
			c = dedup_entities(c)
			self._content[s]['character'] = c

class AlJazeera(Source):
	def __isolate_content(self, links):
		self._content = []
		for h in links:
			desc, title = '', ''
			try:
				if str(h.contents[0]).startswith('<'):
					if not str(h.contents[0].contents[0]).startswith('<'):
						title = h.contents[0].contents[0]
						try:
							if 'top-sec-desc' in h.parent.contents[3]['class']:
								desc = h.parent.contents[3].contents[0]
						except KeyError:
							pass
			except IndexError: # malformed HTML
				pass
			try:
				url = h['href']
				if url.startswith('/'):
					url = urljoin('http://www.aljazeera.com/', url)
			except KeyError: # Yes, here at Al Jazeera we use empty <a> tags!
				pass
			machine_title = nltk.word_tokenize(title)
			machine_title = cp.parse(tagger.tag(machine_title))
			thresh = 2
			if desc:
				thresh += 1
			desc = nltk.word_tokenize(desc)
			desc = cp.parse(tagger.tag(desc))
			self._content.append({
				'title':title,
				'machine_title':machine_title,
				'description':desc,
				'threshold':thresh,
				'url':url
			})

	def update(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("http://www.aljazeera.com/")
		html = r.read()
		soup = BeautifulSoup(html, "html.parser")
		links = soup.find_all('a')
		self.__isolate_content(links)
		self._characterize()

class Bbc(Source):
	def __isolate_content(self, links):
		self._content = []
		for h in links:
			desc = ''
			if not str(h.contents[0].contents[0]).startswith('<'):
				title = h.contents[0].contents[0]
				if len(h.parent.contents) > 1:
					desc = h.parent.contents[1].contents[0]
			else:
				title = h.contents[1].contents[0]
			url = h['href']
			if url.startswith('/'):
				url = urljoin('http://www.bbc.com/news', url)
			machine_title = nltk.word_tokenize(title)
			machine_title = cp.parse(tagger.tag(machine_title))
			thresh = 2
			if desc:
				thresh += 1
			desc = nltk.word_tokenize(desc)
			desc = cp.parse(tagger.tag(desc))
			self._content.append({
				'title':title,
				'machine_title':machine_title,
				'description':desc,
				'threshold':thresh,
				'url':url
			})

	def update(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("http://www.bbc.com/news")
		html = r.read()
		soup = BeautifulSoup(html, "html.parser")
		links = soup.find_all('a', {'class':'gs-c-promo-heading'})
		self.__isolate_content(links)
		self._characterize()

class Guardian(Source):
	def __isolate_content(self, links):
		self._content = []
		for h in links:
			desc = ''
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
			machine_title = nltk.word_tokenize(title)
			machine_title = cp.parse(tagger.tag(machine_title))
			thresh = 2
			if desc:
				thresh += 1
			desc = nltk.word_tokenize(desc)
			desc = cp.parse(tagger.tag(desc))
			self._content.append({
				'title':title,
				'machine_title':machine_title,
				'description':desc,
				'threshold':thresh,
				'url':url
			})

	def update(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("https://www.theguardian.com")
		html = r.read()
		soup = BeautifulSoup(html, "html.parser")
		links = soup.find_all('a', {'class':'js-headline-text'})
		self.__isolate_content(links)
		self._characterize()

class Hill(Source):
	def __isolate_content(self, links):
		self._content = []
		for h in links:
			desc = ''
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
			url = h['href']
			if url.startswith('/'):
				url = urljoin('http://thehill.com/', url)
			machine_title = nltk.word_tokenize(title)
			machine_title = cp.parse(tagger.tag(machine_title))
			thresh = 2
			if desc:
				thresh += 1
			desc = nltk.word_tokenize(desc)
			desc = cp.parse(tagger.tag(desc))
			self._content.append({
				'title':title,
				'machine_title':machine_title,
				'description':desc,
				'threshold':thresh,
				'url':url
			})

	def update(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("http://thehill.com/")
		html = r.read()
		soup = BeautifulSoup(html, "html.parser")
		links = soup.find_all('a')
		self.__isolate_content(links)
		self._characterize()

class Wapo(Source):
	def __isolate_content(self, links):
		self._content = []
		for h in links:
			desc = ''
			title = h.contents[0]
			if 'blurb' in h.parent.parent.contents[1]['class']:
				desc = h.parent.parent.contents[1].contents[0]
			url = h['href']
			if url.startswith('/'):
				url = urljoin('http://www.washingtonpost.com', url)
			machine_title = nltk.word_tokenize(title)
			machine_title = cp.parse(tagger.tag(machine_title))
			thresh = 2
			if desc:
				thresh += 1
			desc = nltk.word_tokenize(desc)
			desc = cp.parse(tagger.tag(desc))
			self._content.append({
				'title':title,
				'machine_title':machine_title,
				'description':desc,
				'threshold':thresh,
				'url':url
			})

	def update(self):
		self._time = datetime.datetime.utcnow()
		r = urllib2.urlopen("http://www.washingtonpost.com")
		html = r.read()
		soup = BeautifulSoup(html, "html.parser")
		links = soup.find_all('a', {'data-pb-field':'web_headline'})
		self.__isolate_content(links)
		self._characterize()

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
	et = entities['talley']
	for t in et:
		e = 0
		while e < len(et[t])-1:
			while et[t][e].lower() in ENTITIES:
				if et[t][e+1].lower() in ENTITIES[et[t][e].lower()]:
					et[t][e] += ' '+et[t][e+1]
					del et[t][e+1]
				else:
					break
			if t not in ['things', 'actions'] and et[t][e].lower() in POSITIONS:
				if POSITIONS[et[t][e].lower()] in et['things']:
					del et[t][e]
			e += 1
	entities['talley'] = et
	return(entities)

def calc_overlap(title, s, cp):
	overlap = 0
	for k in title['talley'].keys():
		for i in title['talley'][k]:
			if k == 'places':
				overlap += (i in s['talley'][k] and len(i) > 2)*2
			else:
				overlap += i in s['talley'][k] and len(i) > 2
	for k in title['mandate'].keys():
		for i in title['mandate'][k]:
			overlap -= (i in s['mandate'][k] and
						i in s['talley']['people'] and
						len(i) > 2)
	return(overlap)

def score_stories(s, wc, cp, source_url, t_off):
	stories = []
	opinions = []
	for h in wc:
		o = calc_overlap(h['character'], s, cp)
		thresh = h['threshold']
		thresh += t_off
		url = h['url']
		if ('/opinion/' in url or
			'/opinions/' in url or
			'/blogs/' in url or
			'/commentisfree/' in url or
			'/posteverything/' in url):
			if o > (thresh - 1):
				opinions.append({
					'title':h['title'],
					'url':url,
					'score': o
				})
		elif url != source_url:
			if o > thresh:
				stories.append({
					'title':h['title'],
					'url':url,
					'score': o
				})
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
	thresh_off = 0
	t = nltk.word_tokenize(title)
	t = tagger.tag(t)
	t = cp.parse(t)
	# The default r NEEDS to be passed or the function below becomes possessed
	t = get_characteristics(t, {
		'talley':{
			'places':[],
			'people':[],
			'organizations':[],
			'things':[],
			'actions':[]
		},
		'mandate':{
			'speakers':[]
		}
	})
	t = dedup_entities(t)
	if ':' in title and len(t['mandate']['speakers']) == 0:
		thresh_off += 1
	for s in sources:
		res = s.get()
		out = score_stories(t, res, cp, url, thresh_off)
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
	n = 0
	for s in reversed(sorted(stories, key=lambda k: k['score'])):
		if s['url'] not in urls:
			n += 1
			out += f'{str(n)}. [{s["title"]}]({s["url"]}) ({str(s["score"])})\n'
			urls.append(s['url'])
	return(out)

def get_story_title(url):
	with urllib2.urlopen(url) as p:
		html = p.read()
	soup = BeautifulSoup(html, "html.parser")
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

sources = {
	AlJazeera(),
	Bbc(),
	Guardian(),
	Hill(),
	Wapo()
}
for k in sources:
	k.update()
for s in reddit.subreddit('news').hot(limit = 30):
	if test_in_sites(s.url):
		title = get_story_title(s.url)
		stories, opinions = process(title, sources, s.url)
		temp = Template(TEMPLATE)
		articles = template_links(stories)
		editorials = template_links(opinions)
		if articles or editorials:
			print(title)
			print(
				temp.substitute(
					sources=articles,
					opinions=editorials,
					writer='/u/michaelh115',
					code='https://github.com/michardy/sources-bot'
				)
			)
			#s.reply(
			#	temp.substitute(
			#		sources=articles,
			#		opinions=editorials,
			#		writer='/u/michaelh115',
			#		code='https://github.com/michardy/sources-bot'
			#	)
			#)
'''
for mention in reddit.inbox.mentions():
	b = mention.body
	urlregex = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)')
	if b.startswith('+/u/sourcesbot'):
		b = b.replace('+/u/sourcesbot ', '')
		b = b.replace('+/u/sourcesbot', '')
		if b == '':
			pass
			#mention.reply('Error: empty request')
		else:
			urls = urlregex.search(b)
			if urls is not None:
				q = get_story_title(urls.group(0))
			else:
				q = b
			stories, opinions = process(q, sources, urls.group(0))
			temp = Template(TEMPLATE)
			articles = template_links(stories)
			editorials = template_links(opinions)
			if articles or editorials:
				print(q)
				print(
					temp.substitute(
						sources=articles,
						opinions=editorials,
						writer='/u/michaelh115',
						code='https://github.com/michardy/sources-bot'
					)
				)
				mention.reply(
					temp.substitute(
						sources=articles,
						opinions=editorials,
						writer='/u/michaelh115',
						code='https://github.com/michardy/sources-bot'
					)
				)
			else:
				mention.reply('No matching articles were found')
'''
