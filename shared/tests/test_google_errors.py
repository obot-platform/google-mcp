import json
import unittest

from fastmcp.exceptions import ToolError
from googleapiclient.errors import HttpError
from httplib2 import Response

from obot_mcp_usage.errors import classify_error


class GoogleErrorTests(unittest.TestCase):
    def test_wrapped_google_http_errors(self):
        for status, reason, category in [(401, 'authError', 'authentication'), (403, 'forbidden', 'permission'), (403, 'userRateLimitExceeded', 'rate_limit'), (404, 'notFound', 'not_found')]:
            with self.subTest(status=status, reason=reason):
                error = HttpError(Response({'status': status}), json.dumps({'error': {'code': status, 'message': 'private', 'errors': [{'reason': reason}]}}).encode())
                try:
                    try:
                        raise error
                    except HttpError:
                        raise ToolError('Failed to get file')
                except ToolError as wrapped:
                    self.assertEqual(classify_error(wrapped), category)
