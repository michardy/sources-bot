class Entity():
	def __init__(self, e, m):
		self.type = e.type
		self.salience = e.salience
		self.mention_type = m.type
		self.id = None
		for meta in e.metadata:
			if meta == "mid":
				self.id = e.metadata[meta] 
				break
