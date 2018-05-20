import datetime

from annotator import Annotator

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
			c = get_characteristics_from_list(
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
			c = get_characteristics_from_list(self._content[s]['description'], c)
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
			machine_title = annotator.annotate(title)
			thresh = 2
			if desc:
				thresh += 1
			desc = annotator.annotate(desc)
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
	def __isolate_content(self, stories):
		self._content = []
		for s in stories:
			desc = ''
			h = s.find_all('a', {'class':'gs-c-promo-heading'})
			if len(h) > 0:
				if not str(h[0].contents[0].contents[0]).startswith('<'):
					title = h[0].contents[0].contents[0]
				else:
					title = h[0].contents[1].contents[0]
				d = s.find_all({'class':'gs-c-promo-summary'})
				if len(d) > 0:
						desc = d[0].contents[0]
				url = h[0]['href']
				if url.startswith('/'):
					url = urljoin('http://www.bbc.com/news', url)
				machine_title = annotator.annotate(title)
				thresh = 2
				if desc:
					thresh += 1
				desc = annotator.annotate(desc)
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
		links = soup.find_all('div', {'class':'gs-c-promo'})
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
			machine_title = annotator.annotate(title)
			thresh = 2
			if desc:
				thresh += 1
			desc = annotator.annotate(desc)
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
			machine_title = annotator.annotate(title)
			thresh = 2
			if desc:
				thresh += 1
			desc = annotator.annotate(desc)
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
			machine_title = annotator.annotate(title)
			thresh = 2
			if desc:
				thresh += 1
			desc = annotator.annotate(desc)
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
