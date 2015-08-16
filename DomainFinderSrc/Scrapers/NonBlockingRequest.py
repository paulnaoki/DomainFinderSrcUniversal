from tornado.httpclient import *
from tornado.simple_httpclient import SimpleAsyncHTTPClient
#from tornado.curl_httpclient import CurlAsyncHTTPClient
from DomainFinderSrc.Scrapers import WebRequestCommonHeader
from tornado import gen
from tornado.ioloop import IOLoop


class AsyncHandler:
    def __init__(self, link: str, loop: IOLoop=None, timeout: int=50):
        self.link = link
        self.client = SimpleAsyncHTTPClient(loop)
        self.timeout = timeout
        if loop is None:
            self.loop = IOLoop.current(False)
        else:
            self.loop = loop
        self.header_only = False

    def get_response(self, header_only=False):
        self.header_only = header_only
        #result = self.inner_get_response()
        result = self.loop.run_sync(self.inner_get_response)
        self.client.close()
        return result

    @gen.coroutine
    def inner_get_response(self) -> (int, dict, str):
        method = "GET"
        if self.header_only:
            method = "HEAD"
        try:
            req = HTTPRequest(self.link, headers=WebRequestCommonHeader.get_html_header(),
                              request_timeout=self.timeout, follow_redirects=True, method=method)
            response = yield self.client.fetch(req)
            #self.client.close()
            return response.code, response.headers, response.body
        except HTTPError as ex:
            result = ex.response
            #self.loop.stop()
            return result.code, None, ""
        except:
            #self.loop.stop()
            return 999, None, ""
        finally:
            pass
            #self.client.close()

