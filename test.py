import unittest
from unittest.mock import MagicMock
import pytz
from fflogs import *


class TestReport(unittest.TestCase):
    def test(self):
        api = MagicMock()
        api.get.return_value = {'start': 1577969903454}
        report = Report.create(api, 'report_id')

        api.get.assert_called_with('report/fights/report_id')
        dt = datetime(2020, 1, 2, 21, 58, 23, 454000)
        self.assertEqual(pytz.timezone('Asia/Tokyo').localize(dt), report.start)


if __name__ == '__main__':
    unittest.main()
