import sys
sys.path.append("..") 

from indexer import indexer

import tornado.ioloop
import tornado.web

def get_query(document):
	query = {
		"query": {
			"bool": {
				"should": []
			}
		}
	}
	keys = [
		'person_ids',
		'organizations',
		'actions',
		'places',
		'thing_ids',
		'place_ids',
		'organization_ids',
		'things',
		'people',
		'speakers'
	]
	for key in keys:
		for component in document[attribute]:
			if attribute in ['people', 'person_ids', 'places', 'place_ids']:
				boost = 2
			else:
				boost = 1
			match = {
				"match": {
					attribute: {
						"query": component,
						"boost": boost
					}
				}
			}
			query["query"]["bool"]["should"].append(match)
	return(query)

def create_display_dict(hit):
	story = {}
	if (
		'/opinion/' in hit['_source']['url'] or
		'/opinions/' in hit['_source']['url'] or
		'/blogs/' in hit['_source']['url'] or
		'/commentisfree/' in hit['_source']['url'] or
		'/posteverything/' in hit['_source']['url']
	):
		story['type'] = 'Opinion'
	else:
		story['type'] = None
	keys = [
		'organizations',
		'actions',
		'places',
		'people',
		'title',
		'description',
		'url'
	]
	for k in keys:
		try:
			story[k] = hit['_source'][k]
		except KeyError:
			story[k] = None
	return(story)

class AnalysisHandler(tornado.web.RequestHandler):
	async def post(self):
		query = self.get_argument('query')
		if self.get_argument('type') == 'url':
			doc_id = await(indexer.index('user-stories', url=query, refresh=True))
		else:
			doc_id = await(indexer.index('user-stories', title=query, refresh=True))
		if doc_id is not None:
			url = '/interactive/search/' + doc_id['index'] + '/' + doc_id['id']
			self.redirect(url, permanent=False)
		else:
			self.send_error(500, reason='Failed to create user story')

class SearchHandler(tornado.web.RequestHandler):
	async def get(self, index, doc_id):
		query = {
			"query": {
				"match": doc_id
			}
		}
		articles = es.search(index=index, body=query)
		if articles['hits']['total'] > 0:
			query_doc = create_display_dict(articles['hits']['hits'][0])
			query = get_query(articles['hits']['hits'][0]['_source'])
			results = es.search(index="stories*", body=query)
			stories = []
			for r in results['hits']['hits']:
				if r['_score'] > 6 and r['_source']['url'] != s.url:
					stories.append(create_display_dict(r))
			self.render('results.html', query=query_doc, results=stories)
		else:
			self.send_error(404, reason='Story Not Found')

def make_app():
	return tornado.web.Application([
		(r"/interactive/analyze", AnalysisHandler),
		(r"/interactive/search/([^/]+)/([^/]+)", SearchHandler)
	], template_path='templates/')

if __name__ == "__main__":
	app = make_app()
	app.listen(8888)
	tornado.ioloop.IOLoop.current().start()