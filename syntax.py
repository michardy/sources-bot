class Syntax():
	'''Object representing node in syntax tree.
		Has:
			offset: position of word (stored for later display purposes if any)
			content: word tagged
			simplified: simplified word (maps to what Google natural languge calls a lemma)
			dependency: relation to parent (Noun Subject etc.)
			tag: part of speech
			number: is it plural?
			case: grammatical case
			gender: gender of word (Not sure if this aquires meaning in Spanish)
			person: 1st person, 2nd person, 3rd person (note: 3rd person is stored 'THIRD')
	'''
	def __init__(self, token, pos):
		self.offset      = pos
		self.content     = token.text.content
		self.simplified  = token.lemma
		self.dependency  = token.dependency_edge.label
		self.tag         = token.part_of_speech.tag
		self.number      = token.part_of_speech.number
		self.case        = token.part_of_speech.case
		self.gender      = token.part_of_speech.gender
		self.person      = token.part_of_speech.person
		self.aspect      = token.part_of_speech.aspect
		self.form        = token.part_of_speech.form
		self.mood        = token.part_of_speech.mood
		self.proper      = token.part_of_speech.proper
		self.reciprocity = token.part_of_speech.reciprocity
        self.tense       = token.part_of_speech.tense
        self.voice       = token.part_of_speech.voice
