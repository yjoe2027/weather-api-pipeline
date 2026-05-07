import sys
import unittest
from unittest.mock import patch, MagicMock
import runpy


class TestWeatherAPIErrorHandling(unittest.TestCase):
    def test_exits_on_non_200_response(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = '{"error": {"code": 2006, "message": "API key is invalid."}}'

        with patch('requests.get', return_value=mock_resp):
            with self.assertRaises(SystemExit) as cm:
                runpy.run_path('weather.py', run_name='__main__')

        self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
