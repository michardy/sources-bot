import datetime

# News sites I respond to (Sites in this list may not nessisarily be reliable)
# Note: I (the bot) only speak english so this list may be limited
# Note: I don't support the Korean Central News Agency because it is too hard to support
#	It attempts to be statefull using a statless protocol and thus breaks all hyperlinking
SITES = [
	'abcactionnews.com/news', # Some kind of affilate (US local)
	'abcnews.go.com', # ABC news US broadcaster (Disney subdomain)
	'english.alarabiya.net/en/News', # Saudi Arabian news channel (State run, Saudi Arabia)
	'aljazeera.com', # Qatari News Channel (State run, Qatar)
	'ahtribune.com', # "News" also a disturbing combination of hearsay, xenophobia, and bigotry (Probably run by the Assad regime)
	'hosted.ap.org/dynamic/stories', # Associated press site A
	'apnews.com', # Associated press site B (An AJAX catastrophe)
	'aol.com/article/news', # Surprisingly not dead yet (US internet company)
	'theatlantic.com', # US News magazine started as an aboltionist publication
	'bbc.com/news', # British broadcaster (Sort of state run, its complicated)
	'bbc.co.uk/news', # regional domain for england
	'theblaze.com', # US conservative news commentary site
	'bloomberg.com/news', # US financial news service
	'breitbart.com', # US conservative news commentary site
	'businessinsider.com', # US financial news company
	'businessinsider.in', # US financial news company (India page)
	'cbc.ca/news', # Canadian Broadcasting Service
	'cbslocal.com', # * CBS local affiliates (US local)
	'cbsnews.com', # US broadcaster
	'english.cctv.com', # China Central Telivision (State run, China)
	'news.cgtn.com', # China Global Television Network (State run, China)
	'chron.com/news',
	'cnn.com', # US 24h news broadcaster
	'nation.co.ke', # The Daily Nation (Kenyan newspaper run by Nation Media Group)
	'dawn.com/', # Pakistani newspaper
	'spiegel.de/international', # Der Spiegel (German Newspaper) hopefully english version
	'foxnews.com', # US conseravative news broadcaster
	'france24.com/en', # French news broadcaster
	'theguardian.com', # UK newspaper
	'haaretz.com,' # Israli newspaper
	'thehill.com', # US political news site
	'thehindu.com/news', # Indian news site
	'thehindu.com/opinion', # Indian news site
	'hindustantimes.com/india-news', # Indian newspaper (Was forced to limit subdirectories)
	'hindustantimes.com/world-news', # Indian newspaper
	'hindustantimes.com/opinion', # Indian newspaper
	'hindustantimes.com/buisness', # Indian newspaper
	'hindustantimes.com/tech', # Indian newspaper
	'hindustantimes.com/mumbai-news', # Indian newspaper
	'hindustantimes.com/delhi-news', # Indian newspaper
	'huffingtonpost.com', # US liberal news commentary site
	'independent.co.uk/news', # UK newspaper
	'infowars.com/news/', # This is so far gone I am not sure this software will even work. (The headlines contain too much opinion to reasonably find alternate sourcing) (US conservative news commentary)
	'miamiherald.com/news', # Miami newspaper (US)
	'msnbc.com', # US liberal news broadcaster
	'nationalreview.com', # US Conservative news magazine
	'nbcnews.com', # US news broadcaster
	'newsweek.com', # US news magazine
	'newyorker.com/news', # US magazine (based in New York)
	'npr.org', # National Public Radio (US not for profit broadcaster)
	'nytimes.com', # New York Times (US newspaper)
	'pakthought.com', # Pakistani news analysis
	'pbs.org/newshour', # PBS NewsHour (US news show)
	'en.people.cn', # People's Daily (State run, China)
	'politico.com', # US news magazine
	'reuters.com', # News wire
	'www.rt.com', # Russia Today (www. is the English subdomain) (State run, Russia)
	'news.sky.com', # UK broadcaster
	'slate.com', # US opinion blogs
	'sabc.co.za/news', # South African Broadcasting Corporation
	'sputniknews.com', # Russian news site (State run, Russia)
	'thestar.com/news',
	'thestar.com.my/news',
	'thesun.co.uk/news', # UK tabloid
	'telegraph.co.uk/news', # UK tabloid
	'thetimes.co.uk', # UK newspaper
	'timesofindia.indiatimes.com/', # The Times of India (Indian newspaper)
	'indiatimes.com/news', # Indian news site (not the same as above or just rebranding)
	'news.trust.org', # Thomson Reuters (Wire)
	'unian.info', # Ukrainian Independent Information Agency of News
	'usatoday.com/story/news', # US newspaper (at least at one point it was)
	'voanews.com', # Voice of America (State run, United States of America)
	'vox.com', # US news website
	'wsj.com', # Wall Street Journal (US Financial newspaper)
	'washingtonpost.com', # US newspaper
	'washingtontimes.com/news', # US conservative newspaper
	'washingtontimes.com/opinion',
	'yahoo.com/news' # US ex tech giant (steals content an reruns the AP wire verbatum.  Somehow still alive)
]

# Used to clump multiple word entities into one entity
# Ex: If it finds president and the next word is donald it will clump them.
#     Then it will look at the clump  'president donald' and if the next word is trump it will clump them
ENTITIES = {
	'white':['house'],
	'house':['speaker'],
	'paul':['ryan'],
	'mitch':['mcconell'],
	'nancy':['pelosi'],
	'donald':['trump'],
	'democratic':['party'],
	'republican':['party'],
	'president':['trump','donald'],
	'president donald':['trump'],
	'speaker':['ryan','pual'],
	'speaker pual':['ryan'],
	'house speaker':['ryan','pual'],
	'house speaker paul':['ryan'],
	'antonio':['guterres'],
	'antónio':['guterres'],
	'un':['head', 'high', 'chief', 'secretary-general', 'secretary', 'secretary- '],
	'un secretary':['general', 'guterres', 'antonio', 'antónio'],
	'un secretary-':['general', 'guterres', 'antonio', 'antónio'],
	'un secretary antonio': ['guterres'],
	'un secretary antónio': ['guterres'],
	'un high':['commissioner'],
}

# Converts names and abbreviations to positions
# This ensures that articles talking about the same thing with different names are matched
POSITIONS = {
	'trump':'president',
	'un secretary':'un secretary general',
	'un secretary- general':'un secretary general',
	'un chief':'un secretary general',
	'un secretary guterres':'un secretary general',
	'un secretary antonio':'un secretary general',
	'un secretary antónio':'un secretary general',
	'un secretary antonio guterres':'un secretary general',
	'un secretary antónio guterres':'un secretary general',
	'antonio guterres':'un secretary general',
	'antónio guterres':'un secretary general',
}

NOT_GPE = [
	'Trump'
]

USELESS_VERBS = [
	'has',
	'is'
]
