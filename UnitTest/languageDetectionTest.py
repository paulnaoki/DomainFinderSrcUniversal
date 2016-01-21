from urllib.parse import urlsplit
from DomainFinderSrc.Utilities import FilePath, FileIO
from unittest import TestCase
from DomainFinderSrc.Scrapers.LinkChecker import LinkChecker
import shortuuid
from DomainFinderSrc.Utilities.StrUtility import StrUtility
import langid

# https://zh.wikipedia.org/wiki/ISO_639-1
good_lang_code = ['en', 'de', 'fr', 'es', 'fr', 'it', 'pt', 'ga', 'el', 'da']
bad_lang_code = ['zh', 'ja', 'ko', 'ru', 'vi']

langid.set_languages(langs=good_lang_code+bad_lang_code)


class LanguageTest(TestCase):
    def test_from_text(self):
        result = langid.classify('i made an icecream for you.')
        print(result)

    def test_from_url(self):
        response = LinkChecker.get_page_source(link="http://www.frenchweb.fr/sisense-decroche-50-millions-de-dollars-pour-accelerer-dans-lanalyse-de-donnees/221848")
        print(langid.classify(response.text))

