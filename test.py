import unittest
from unittest.mock import MagicMock
import pytz
from fflogs import *


def create_dt(*args, **kwargs):
    dt = datetime(*args, **kwargs)
    return pytz.timezone('Asia/Tokyo').localize(dt)


class TestReport(unittest.TestCase):
    def test(self):
        api = MagicMock()
        api.get.return_value = {
            'start': 1577969903454, 'fights': [{'start_time': 496584, 'end_time': 751596}]}
        report = Report.create(api, 'report_id')

        api.get.assert_called_with('report/fights/report_id')
        self.assertEqual(create_dt(2020, 1, 2, 21, 58, 23, 454000), report.start)
        self.assertEqual(496584, report.fights[0].ft.start_ms)
        self.assertEqual(create_dt(2020, 1, 2, 22, 6, 40, 38000), report.fights[0].ft.start_dt)
        # TODO: end


if __name__ == '__main__':
    unittest.main()
