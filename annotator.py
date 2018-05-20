from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

import datetime
import time

from entity import Entity
from langtree import Langtree # syntax is used here

client = language.LanguageServiceClient()

class Annotator:
	'''Provides and regulates (rate limits) access to Google Cloud Natural Language API'''
	def __init__(self, features=None, encoding='UTF8'):
		self.__lastcall = datetime.datetime.min # Something small
		self.encoding = encoding
		if features is None:
			self.features = {
				"extract_syntax":				True,
				"extract_entities":				True,
				"extract_document_sentiment":	False,
				"extract_entity_sentiment":		False,
			}
		else:
			self.features = features

	def __make_trees(annotated, ref):
		'''Finds all sentence roots in all annotated sentences and makes and array of trees with them'''
		processed = [False for i in annotated.tokens]
		t = 0 # iterator for scanning flattened tree
		trees = []
		while False in processed:
			if not processed[t]:
				token = annotated.tokens[t]
				if token.dependency_edge.head_token_index == t:
					#print(str(token.dependency_edge.head_token_index) + ' == ' + str(t))
					trees.append(Langtree(t, annotated.tokens, processed, ref))
			if t < len(processed) - 1:
				t += 1
			else:
				break
		return(trees)

	def __make_reference_table(annotated):
		'''Makes a temporary reference dictionary containing all tagged entities.
		The keys in the dictionary are the charater offsets'''
		table = {}
		for e in annotated.entities:
			for m in e.mentions:
				table[m.text.begin_offset] = Entity(e, m)
		return(table)

	def annotate(self, text):
		'''Gets Google Natural Language API to annotate a sentence and then converts it to a tree which is returned'''
		document = types.Document(
			content=text,
			type=enums.Document.Type.PLAIN_TEXT
		)
		while datetime.datetime.utcnow()-self.__lastcall < datetime.timedelta(seconds=1):
			time.sleep(1) # Need to find a better way of doing this
		self.__lastcall = datetime.datetime.utcnow()
		annotated = client.annotate_text(
			document=document,
			features=self.features,
			encoding_type=self.encoding
		)
		return(__make_trees(
			annotated, __make_reference_table(annotated)
		))
