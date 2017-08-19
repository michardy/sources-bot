import datetime

# News sites I respond to (Sites in this list may not nessisarily be reliable)
# Note: I (the bot) only speak english so this list may be limited
SITES = [
	'abcactionnews.com/news', # Some kind of affilate
	'abcnews.go.com', # ABC news (Disney subdomain)
	'aljazeera.com',
	'ahtribune.com', # "News" also a disturbing combination of hearsay, xenophobia, and bigotry (Probably run by the Assad regime)
	'hosted.ap.org/dynamic/stories', # Associated press site A
	'apnews.com', # Associated press site B (An AJAX catastrophe)
	'aol.com/article/news', # Surprisingly not dead yet
	'theatlantic.com',
	'bbc.com/news',
	'bbc.co.uk/news',
	'theblaze.com',
	'bloomberg.com/news',
	'breitbart.com',
	'cbslocal.com', # * CBS local affiliates
	'cbsnews.com',
	'english.cctv.com', # China Central Telivision
	'news.cgtn.com', # China Global Television Network
	'cnn.com',
	'spiegel.de/international', # Der Spiegel hopefully english version
	'foxnews.com',
	'france24.com/en',
	'theguardian.com',
	'haaretz.com,'
	'thehill.com',
	'huffingtonpost.com',
	'independent.co.uk/news',
	'msnbc.com',
	'nationalreview.com',
	'nbcnews.com',
	'newsweek.com',
	'newyorker.com/news',
	'npr.org',
	'nytimes.com',
	'pbs.org/newshour', # PBS NewsHour
	'en.people.cn', # People's Daily
	'politico.com',
	'reuters.com',
	'www.rt.com', # Russia Today (www. is the English subdomain)
	'sabc.co.za/news', # South African Broadcasting Corporation
	'news.sky.com',
	'slate.com',
	'thesun.co.uk/news',
	'usatoday.com/story/news',
	'voanews.com', # Voice of America
	'vox.com',
	'wsj.com',
	'washingtonpost.com',
	'washingtontimes.com/news',
	'washingtontimes.com/opinion',
	'yahoo.com/news'
]

# News sites I use (I will get banned from /r/the_donald)
SOURCES = [
	'aljazeera.com',
	'bbc.com/news',
	'spiegel.de/international',
	'theguardian.com',
#	'haaretz.com,' Can't use paywalled
	'thehill.com',
#	'npr.org', # Can't use due to force capitalized titles
#	'nytimes.com', # Can't use due to force capitalized titles
	'pbs.org/newshour',
	'washingtonpost.com'
]

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
	'house speaker paul':['ryan']
}
