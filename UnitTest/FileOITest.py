from DomainFinderSrc.Utilities import FilePath, FileIO
from unittest import TestCase
from collections import deque


text_file_path = '/usr/local/DomainFinder/SpamFilter/Keywords.txt'


class FileIOTest(TestCase):
    def testTxtFileWrite(self):
        keywords = ["aka", "ganster", "ahref", "majestic", "性交"]
        FileIO.FileHandler.append_lines_to_file(text_file_path, keywords, option="wt")

    def testTxtFileRead(self):
        data = FileIO.FileHandler.read_lines_from_file(text_file_path, option="t")
        for item in data:
            print(item)

    def test_dequeue(self):
        queue = deque()
        if len(queue) > 0:
            result = queue.popleft()
        for i in range(100):
            queue.append("domain{0:d}".format(i,))
        # for i in range(100):
        #     print(queue.popleft())
        if "domain10" in queue:
            print("is in")
        else:
            print("is not in")