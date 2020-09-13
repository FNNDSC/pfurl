import unittest
import json
from pfurl import Pfurl


class TestPfurlHelpers(unittest.TestCase):

    def setUp(self):
        self.pfurl = Pfurl()

    def test__remove_misplaced_http_headers(self):
        result = self.pfurl._remove_misplaced_http_headers(
            '200 OK\r\n'
            'Content-Type: text/html; charset=UTF-8\r\n'
            'Content-Length: 52\r\n'
            '{"stdout": "the json stuff that you actually want"}')
        self.assertTrue(
            result.startswith('{'),
            'example body should start with "{"')
        self.assertTrue(
            result.endswith('}'),
            'example body should end with "}"')
        result = json.loads(result)
        self.assertIn(
            'stdout', result,
            'example body should be JSON with a "stdout" key')
        self.assertEqual(
            result['stdout'], 'the json stuff that you actually want',
            'result does not equal example data')

        result = self.pfurl._remove_misplaced_http_headers(
            '200 OK\r\n'
            'Content-Type: application/json; charset=UTF-8\r\n'
            'Content-Length: 23\r\n'
            'Fennel-Seeds: delicious\r\n'
            'Star-Anise: in\r\n'
            '{"gordon": "ramsay"}')
        self.assertDictEqual(
            json.loads(result),
            {'gordon': 'ramsay'},
            'method cannot handle extra (bogus) HTTP headers')

        result = self.pfurl._remove_misplaced_http_headers(
            '200 OK\r\n'
            'Animal: bunny\r\n'
            '["fluffy", 1, "cottontail"]')
        self.assertListEqual(
            json.loads(result),
            ['fluffy', 1, 'cottontail'],
            'method should handle other valid JSON types, such as arrays')
