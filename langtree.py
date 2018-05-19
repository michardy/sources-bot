import syntax.Syntax as Syntax

class Langtree():
	'''Fully annotated tree representing sentence structure.
	Contains both entities and syntax.'''
	def __branch(self, parent, tokens, processed, ref):
		'''Adds a branch to the tree'''
		t = 0 # iterator for scanning flattened tree
		while False in processed:
			if not processed[t]:
				token = tokens[t]
				print('\tsearching child: {t} for {parent}: {out}'.format(t=t, parent=parent, out=(token.dependency_edge.head_token_index == parent)))
				if token.dependency_edge.head_token_index == parent:
					return(Langtree(t, annotate.tokens, processed, ref))
			if t < len(processed) - 1:
				t += 1
			else:
				return(None)

	def __init__(self, parent, tokens, processed, ref):
		'''Initializes a tree based on a provided root'''
		self.syntax = Syntax(tokens[parent], parent)
		try:
			self.entity = ref[tokens[parent].text.begin_offset]
		except KeyError:
			self.entity = None
		self.branches = []
		print('found parent: {parent}'.format(parent=parent))
		processed[parent] = True
		cont = True
		while cont:
			new_branch = self.__branch(parent, tokens, processed, ref)
			if new_branch is None:
				cont = False
				break
			else:
				self.branches.append(new_branch)

	def __str__(self):
		return("{\n" + str(self.syntax) + "\n" + str(self.entity) + "\n" + str(self.branches) + "\n}")

	def __repr__(self):
		return(str(self))
