from syntax import Syntax
from google.cloud.language import enums

class Langtree():
	'''Fully annotated tree representing sentence structure.
	Contains both entities and syntax.'''
	def __get_true_children(self, child, parent, tokens, processed, ref):
		'''Checks that the next nodes are not just chained nouns
		If they are chained then add the chained contents and link the next element'''
		if (token.dependency_edge.label == enums.DependencyEdge.Label.NN or
			token.dependency_edge.label == enums.DependencyEdge.Label.APPOS):
			assert(parent != child, 'Self referential non root node')
			if parent < child:
				self.syntax.content += ' ' + tokens[child].text.content
				self.syntax.simplified += ' ' + tokens[child].lemma
			else:
				self.syntax.content = (
					tokens[t].text.content + ' ' + self.syntax.content
				)
				self.syntax.simplified = (
					tokens[t].lemma + ' ' + self.syntax.simplified
				)
			return(self.__branch(child, tokens, processed, ref))
		else:
			return(Langtree(child, tokens, processed, ref))

	def __branch(self, parent, tokens, processed, ref):
		'''Adds a branch to the tree'''
		t = 0 # iterator for scanning flattened tree
		while False in processed:
			if not processed[t]:
				token = tokens[t]
				if token.dependency_edge.head_token_index == parent:
					self.__get_true_children(t, parent, tokens, processed, ref)
			if t < len(processed) - 1:
				t += 1
			else:
				return(None)

	def __init__(self, parent, tokens, processed, ref):
		'''Initializes a tree based on a provided root'''
		self.processed = False # has this tag been checked?
		self.syntax = Syntax(tokens[parent], parent)
		try:
			self.entity = ref[tokens[parent].text.begin_offset]
		except KeyError:
			self.entity = None
		self.branches = []
		processed[parent] = True
		cont = True
		while cont:
			new_branch = self.__branch(parent, tokens, processed, ref)
			if new_branch is None:
				cont = False
				break
			else:
				self.branches.append(new_branch)

	def __list_add(l, item):
		'''Set like list add function. Allows us to use JSON serializable lists'''
		if item not in l:
			l.add(item)

	def get_simple_parts(self, simplified, dependency):
		'''Function to return sentence components of a subset of the sentence.
		Goes from the root element to the first adapositional clause
		'''
		if self.syntax.dependency == enums.PartOfSpeech.Tag.ADP:
			return(simplified)
		elif self.syntax.dependency == enums.DependencyEdge.Label.ROOT:
			simplified['action'] = self.syntax.simplified
		elif self.syntax.dependency == enums.DependencyEdge.Label.DOBJ:
			if self.entity is not None:
				simplified['target_entity'] = self.entity.id
			simplified['target'] = self.syntax.lemma
		elif self.syntax.dependency == enums.DependencyEdge.Label.NSUBJ:
			if self.entity is not None:
				simplified['actor_entity'] = self.entity.id
			simplified['actor'] = self.syntax.lemma
		elif self.syntax.dependency == enums.DependencyEdge.Label.POSS:
			if dependency == enums.DependencyEdge.Label.DOBJ:
				if self.entity is not None:
					simplified['target_owner_entity'] = self.entity.id
				simplified['target_owner'] = self.syntax.lemma
			elif dependency == enums.DependencyEdge.Label.NSUBJ:
				if self.entity is not None:
					simplified['actor_owner_entity'] = self.entity.id
				simplified['actor_owner'] = self.syntax.lemma
		for branch in self.branches:
			simplified = branch.get_simple_parts(simplified, self.syntax.dependency)
		return(simplified)

	def get_characteristics(self, r):
		'''Get people, places, organizations, actions and other things of signifigance'''
		if self.entity is not None:
			if self.entity.type == enums.Entity.Type.LOCATION:
				if self.syntax.simplified not in r['places']:
					self.__list_add(r['places'], self.syntax.simplified)
					if self.entity.id is not None:
						self.__list_add(r['place_ids'], self.entity.id)
			elif self.entity.type == enums.Entity.Type.ORGANIZATION:
				if self.syntax.simplified not in r['organizations']:
					self.__list_add(r['organizations'], self.syntax.simplified)
					if self.entity.id is not None:
						self.__list_add(r['orgaization_ids'], self.entity.id)
			elif self.entity.type == enums.Entity.Type.PERSON:
				if self.syntax.simplified not in r['people']:
					self.__list_add(r['people'], self.syntax.simplified)
					if self.entity.id is not None:
						self.__list_add(r['person_ids'], self.entity.id)
		else:
			if self.syntax.tag == enums.PartOfSpeech.Tag.NOUN:
				if self.syntax.simplified not in r['things']:
					self.__list_add(r['things'], self.syntax.simplified)
			elif self.syntax.tag == enums.PartOfSpeech.Tag.VERB:
				if self.syntax.simplified not in r['actions']:
					self.__list_add(r['actions'], self.syntax.simplified)
			# needs to be rewritten
			#elif t.syntax.tag == 'PUNCT':
			#	r = find_mandatory_words_end(t, n, r)
		for b in self.branches:
			r = b.get_characteristics(r)
		return(r)

	def __str__(self):
		return("{\n" + str(self.syntax) + "\n" + str(self.entity) + "\n" + str(self.branches) + "\n}")

	def __repr__(self):
		return(str(self))
