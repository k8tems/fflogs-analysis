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
        self.assertEqual(751596, report.fights[0].ft.end_ms)
        self.assertEqual(create_dt(2020, 1, 2, 22, 10, 55, 50000), report.fights[0].ft.end_dt)


class TestFight(unittest.TestCase):
    def test(self):
        api = MagicMock()
        api.get.return_value = {
            'events': [{'timestamp': 0}]
        }
        start_dt = datetime(2019, 1, 1)
        end_dt = datetime(2019, 1, 2)
        ft = FightTime(start_dt, end_dt, 0, 0)
        fight = Fight(api, ft, 'report_id')
        gen = fight.gen_events('damage-done', foo='bar')

        next(gen)
        api.get.assert_called_with('report/events/damage-done/report_id', {'foo': 'bar', 'start': 0, 'end': 0})
        print(api.get.call_args_list[0])


if __name__ == '__main__':
    unittest.main()
