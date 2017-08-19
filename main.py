# Natural Language Toolkit: code_traverse
# add collection into list for back searching
import nltk
import datetime
try:
	import urllib2
	from urlparse import urljoin
except ImportError:
	import urllib.request as urllib2
	from urllib.parse import urljoin
import praw
from bs4 import BeautifulSoup
from string import Template
from news import SITES, ENTITIES

cp = nltk.data.load('chunkers/maxent_ne_chunker/english_ace_multiclass.pickle')

tagger = nltk.data.load('taggers/maxent_treebank_pos_tagger/english.pickle')

reddit = praw.Reddit('sourcesbot', user_agent='web:sourcesbot:v0.0.1 by /u/michaelh115')

TEMPLATE = '''Other sources for this story:

$sources

Opinions:

$opinions

__________

Note on opinions: due to sourcing and how articles are matched the opinions may not be terribly diverse.  

This bot was written by $writer and the source code can be found [here]($code).  

This bot is still very much in beta.  Feedback is is welcome.  '''

def read_words(n, key, r):
	name = ''
	for l in n.leaves():
		name += l[0] + ' '
	name = name[:len(name)-1]
	if name not in r[key]:
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
					if n[0].lower() not in r['things']:
						r['things'].append(n[0].lower())
				elif n[1].startswith('V'):
					if n[0].lower() not in r['actions']:
						r['actions'].append(n[0].lower())
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
				{'places':[], 'people':[], 'organizations':[], 'things':[], 'actions':[]}
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
			thresh = 1
			if desc:
				thresh = 2
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
			thresh = 1
			if desc:
				thresh = 2
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
			thresh = 1
			if desc:
				thresh = 2
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
				if 'menu__link' not in h['class'] and 'hide_overlay' not in h['class']:
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
			thresh = 1
			if desc:
				thresh = 2
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
			thresh = 1
			if desc:
				thresh = 2
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
	for t in entities:
		e = 0
		while e < len(entities[t])-1:
			while entities[t][e].lower() in ENTITIES:
				if entities[t][e+1].lower() in ENTITIES[entities[t][e].lower()]:
					entities[t][e] += ' '+entities[t][e+1]
					del entities[t][e+1]
			e += 1
	return(entities)

def calc_overlap(title, s, cp):
	overlap = 0
	for k in title.keys():
		for i in title[k]:
			overlap += i in s[k] and len(i) > 2
	return(overlap)

class Story:
	def __init__(self, title, url, score, opinion=False):
		self.title = title
		self.url = url
		self.score = score
		self.opinion = opinion

def score_stories(s, wc, cp, source_url):
	stories = []
	opinions = []
	for h in wc:
		o = calc_overlap(h['character'], s, cp)
		thresh = h['threshold']
		if o > thresh:
			url = h['url']
			if '/opinion/' in url or '/opinions/' in url or '/blogs/' in url or '/commentisfree/' in url or '/posteverything/' in url:
				opinions.append({'title':h['title'], 'url':url, 'score': o})
			elif url != source_url:
				stories.append({'title':h['title'], 'url':url, 'score': o})
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
	t = nltk.word_tokenize(title)
	t = tagger.tag(t)
	t = cp.parse(t)
	# The default r NEEDS to be passed or the function below becomes possessed
	t = get_characteristics(t, {'places':[], 'people':[], 'organizations':[], 'things':[], 'actions':[]})
	t = dedup_entities(t)
	for s in sources:
		res = s.get()
		out = score_stories(t, res, cp, url)
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

sources = {
	AlJazeera(),
	Bbc(),
	Guardian(),
	Hill(),
	Wapo()
}
for k in sources:
	k.update()
for s in reddit.subreddit('test').hot(limit = 3):
	if test_in_sites(s.url):
		with urllib2.urlopen(s.url) as p:
			html = p.read()
		soup = BeautifulSoup(html, "html.parser")
		title = soup.find_all('title')[0].contents[0]
		if '|' in title:
			title = title.split('|')[0]
		elif ' - ' in title:
			title = title.split(' - ')[0]
		elif '«' in title:
			title = title.split('«')[0]
		stories, opinions = process(title, sources, s.url)
		temp = Template(TEMPLATE)
		articles = template_links(stories)
		editorials = template_links(opinions)
		if articles or editorials:
			print()
			print(title)
			print(temp.substitute(sources=articles, opinions=editorials, writer='/u/michaelh115', code='https://github.com/michardy/sources-bot'))
			#time.sleep(10)
			s.reply(temp.substitute(sources=articles, opinions=editorials, writer='/u/michaelh115', code='https://github.com/michardy/sources-bot'))
