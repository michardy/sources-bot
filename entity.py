class Entity():
	def __init__(self, e, m):
		self.type = e.type
		self.salience = e.salience
		self.mention_type = m.type
		for meta in e.metadata:
			if meta.key = "mid":
				self.id = meta.value
				break
			else:
				self.id = None
