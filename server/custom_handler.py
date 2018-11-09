from tornado.web import RequestHandler

class SourcesbotHandler(RequestHandler):
	def write_error(self, status_code, **kwargs):
		'''Custom error pages'''
		self.render('error.html', code=status_code, reason=self._reason)
