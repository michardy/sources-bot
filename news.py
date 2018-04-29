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
	'businessinsider.com',
	'cbc.ca/news', # Canadian Broadcasting Service
	'cbslocal.com', # * CBS local affiliates
	'cbsnews.com',
	'english.cctv.com', # China Central Telivision
	'news.cgtn.com', # China Global Television Network
	'chron.com/news',
	'cnn.com',
	'spiegel.de/international', # Der Spiegel hopefully english version
	'foxnews.com',
	'france24.com/en',
	'theguardian.com',
	'haaretz.com,'
	'thehill.com',
	'huffingtonpost.com',
	'independent.co.uk/news',
	'infowars.com/news/', # This is so far gone I am not sure this software will even work. (The headlines contain too much opinion to reasonably find alternate sourcing)
	'miamiherald.com/news',
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
	'thestar.com/news',
	'thestar.com.my/news',
	'thesun.co.uk/news',
	'telegraph.co.uk/news',
	'news.trust.org', # Thomson Reuters
	'unian.info', # Ukrainian Independent Information Agency of News
	'usatoday.com/story/news',
	'voanews.com', # Voice of America
	'vox.com',
	'wsj.com',
	'washingtonpost.com',
	'washingtontimes.com/news',
	'washingtontimes.com/opinion',
	'yahoo.com/news'
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
