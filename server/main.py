import sys
sys.path.append("..")

from indexer import indexer

from elasticsearch import Elasticsearch
import tornado.ioloop
import tornado.web

es = Elasticsearch()


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
		for component in document[key]:
			if key in ['people', 'person_ids', 'places', 'place_ids']:
				boost = 2
			else:
				boost = 1
			match = {
				"match": {
					key: {
						"query": component,
						"boost": boost
					}
				}
			}
			query["query"]["bool"]["should"].append(match)
	return(query)


def get_graph_query(document):
	query = {
		"size": 0,
		"query": {
			"bool": {
				"should": []
			}
		},
		"aggs": {
			"time": {
				"date_histogram": {
					"field": "timestamp",
					"interval": "day"
				}
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
		for component in document[key]:
			if key in ['people', 'person_ids', 'places', 'place_ids']:
				boost = 2
			else:
				boost = 1
			match = {
				"match": {
					key: {
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
		hit['_source']['url'] is not None and
		(
			'/opinion/' in hit['_source']['url'] or
			'/opinions/' in hit['_source']['url'] or
			'/blogs/' in hit['_source']['url'] or
			'/commentisfree/' in hit['_source']['url'] or
			'/posteverything/' in hit['_source']['url']
		)
	):
		story['type'] = 'Opinion'
	else:
		story['type'] = None
	keys = [
		'organizations',
		'actions',
		'places',
		'people',
		'things',
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
			self.send_error(
				500,
				reason='Failed to index remote site. (Remote site probably returned an error)'
			)


class SearchHandler(tornado.web.RequestHandler):
	async def get(self, index, doc_id):
		query = {
			"query": {
				"match": {
					"_id": doc_id
				}
			}
		}
		articles = es.search(index=index, body=query)
		if articles['hits']['total'] > 0:
			query_doc = create_display_dict(articles['hits']['hits'][0])
			query = get_query(articles['hits']['hits'][0]['_source'])
			results = es.search(index="stories*", body=query)
			stories = []
			for r in results['hits']['hits']:
				if r['_score'] > 6 and r['_source']['url'] != query_doc['url']:
					stories.append(create_display_dict(r))
			self.render(
				'results.html',
				query=query_doc,
				results=stories,
				index=index,
				doc=doc_id
			)
		else:
			self.send_error(404, reason='Story Not Found')


class SearchGraphHandler(tornado.web.RequestHandler):
	async def get(self, index, doc_id):
		query = {
			"query": {
				"match": {
					"_id": doc_id
				}
			}
		}
		articles = es.search(index=index, body=query)
		if articles['hits']['total'] > 0:
			query = get_graph_query(articles['hits']['hits'][0]['_source'])
			response = es.search(index="stories*", body=query)
			graph = [
				{
					'x': [],
					'y': [],
					'type': 'timeseries'
				}
			]
			for bucket in response['aggregations']['time']['buckets']:
				graph[0]['x'].append(bucket['key_as_string'])
				graph[0]['y'].append(bucket['doc_count'])
			self.write(graph)
		else:
			self.send_error(404, reason='Story Not Found')


class TagHandler(tornado.web.RequestHandler):
	async def get(self, field, tag):
		if field not in ['people', 'places', 'things', 'organizations', 'actions']:
			self.send_error(400, reason='Invalid tag field')
		query = {
			"query": {
				"match": {
					field: tag
				}
			}
		}
		articles = es.search(index="stories*", body=query)
		if articles['hits']['total'] == 0:
			self.send_error(404, reason='Tag not found')
		display_mapping = {
			'people': 'Person',
			'places': 'Place',
			'things': 'Thing',
			'organizations': 'Organization',
			'actions': 'Action'
		}
		results = []
		for article in articles['hits']['hits']:
			results.append(create_display_dict(article))
		self.render(
			'tag_search.html',
			tag_type=display_mapping[field],
			tag_field=field,
			tag=tag,
			results=results
		)


class TagGraphHandler(tornado.web.RequestHandler):
	async def get(self, field, tag):
		if field not in ['people', 'places', 'things', 'organizations', 'actions']:
			self.send_error(400, reason='Invalid tag field')
		query = {
			"size": 0,
			"query": {
				"match": {
					field: tag
				}
			},
			"aggs": {
				"time": {
						"date_histogram": {
						"field": "timestamp",
						"interval": "day"
					}
				}
			}
		}
		graph = [
			{
				'x': [],
				'y': [],
				'type': 'timeseries'
			}
		]
		response = es.search(index="stories*", body=query)
		for bucket in response['aggregations']['time']['buckets']:
			graph[0]['x'].append(bucket['key_as_string'])
			graph[0]['y'].append(bucket['doc_count'])
		self.write(graph)


def make_app():
	return tornado.web.Application([
		(r"/interactive/analyze", AnalysisHandler),
		(r"/interactive/search/([^/]+)/([^/]+)", SearchHandler),
		(r"/interactive/search/([^/]+)/([^/]+)/graph", SearchGraphHandler),
		(r"/interactive/tag/([^/]+)/([^/]+)", TagHandler),
		(r"/interactive/tag/([^/]+)/([^/]+)/graph", TagGraphHandler)
	], template_path='templates/')

if __name__ == "__main__":
	app = make_app()
	app.listen(8888)
	tornado.ioloop.IOLoop.current().start()
