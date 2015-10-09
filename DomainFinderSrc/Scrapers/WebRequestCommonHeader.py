class WebRequestCommonHeader:
    acceptTpye_webpage = "text/html,application/xhtml+xml,application/xml;q=0.9"  # note xml order is lower
    acceptTpye_all = "*/*"
    content_type = 'text/plain; charset=utf-8'
    webpage_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 ' \
                    'Safari/537.36'
    crawler_agent = 'ia_archiver'
    langs = 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
    # encoding_accept = 'gzip,deflate,sdch' # ignore this because the returned result will be compressed as those format
    html_headers = {'Accept': acceptTpye_webpage,
                    'Content-Type': content_type,
                    'User-Agent': crawler_agent,
                    'Accept-Language': langs,
                    # 'Accept-Encoding': encoding_accept,
                    # 'Accept': '*/*',
                    }

    common_headers = {'Accept': '*/*',
                      'Content-Type': content_type,
                      'User-Agent': crawler_agent,
                      'Accept-Language': langs,
                      # 'Accept-Encoding': encoding_accept,
                      # 'Accept': '*/*',
                     }

    @staticmethod
    def get_html_header(user_agent='ia_archiver'):
        return WebRequestCommonHeader.html_headers.update({'User-Agent': user_agent})

    @staticmethod
    def get_common_header(user_agent='ia_archiver'):
        return WebRequestCommonHeader.common_headers.update({'User-Agent': user_agent})
