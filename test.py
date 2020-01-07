import unittest
from unittest.mock import MagicMock
from datetime import timedelta
import pytz
from fflogs import *


def create_dt(*args, **kwargs):
    dt = datetime(*args, **kwargs)
    return pytz.timezone('Asia/Tokyo').localize(dt)


class TestReport(unittest.TestCase):
    def setUp(self):
        self.api = MagicMock()
        self.api.get.return_value = {
            'start': 1577969903454,
            'fights': [{'start_time': 496584, 'end_time': 751596}],
            'friendlies': [{'guid': 1, 'name': 'foo', 'job': 'bar'},
                           {'guid': 2, 'name': 'baz', 'job': 'baaz'}]}
        self.report = Report.create(self.api, 'report_id')

    def test_report(self):
        self.api.get.assert_called_with('report/fights/report_id')
        self.assertEqual(create_dt(2020, 1, 2, 21, 58, 23, 454000), self.report.start)

    def test_fight(self):
        f = self.report.fights[0]
        self.assertEqual(496584, f.ft.start_ms)
        self.assertEqual(create_dt(2020, 1, 2, 22, 6, 40, 38000), f.ft.start_dt)
        self.assertEqual(751596, f.ft.end_ms)
        self.assertEqual(create_dt(2020, 1, 2, 22, 10, 55, 50000), f.ft.end_dt)
        self.assertEqual({1: {'name': 'foo', 'job': 'bar'}, 2: {'name': 'baz', 'job': 'baaz'}},
                         f.players)


class TestFight(unittest.TestCase):
    def test(self):
        api = MagicMock()
        events_0 = [{'timestamp': 100}, {'timestamp': 200}]
        events_1 = [{'timestamp': 300}]
        resp_0 = {'events': events_0}
        resp_1 = {'events': events_1}
        api.get.side_effect = [resp_0, resp_1]
        ft = FightTime(datetime(2019, 1, 1), datetime(2019, 1, 2), start_ms=100, end_ms=500)
        gen = Fight(api, 'report_id', ft, None).gen_events('damage-done', foo='bar')
        ret_0 = next(gen)
        ret_1 = next(gen)

        self.assertEqual('report/events/damage-done/report_id', api.get.call_args_list[0][0][0])
        self.assertEqual({'foo': 'bar', 'start': 100, 'end': 500}, api.get.call_args_list[0][0][1])

        self.assertEqual('report/events/damage-done/report_id', api.get.call_args_list[1][0][0])
        # `start`をインクリメントしないとリストの境界で被りが発生する
        self.assertEqual({'foo': 'bar', 'start': 201, 'end': 500}, api.get.call_args_list[1][0][1])

        # 開始時間に対して相対的なタイムスタンプに変換されてるはず
        self.assertEqual([{'timestamp': 0}, {'timestamp': 100}], ret_0)
        self.assertEqual([{'timestamp': 200}], ret_1)

    def test_repr(self):
        start_dt = datetime(year=2019, month=12, day=31, hour=10, minute=1)
        end_dt = start_dt + timedelta(seconds=63)
        ft = FightTime(start_dt, end_dt, start_ms=100, end_ms=63100)
        self.assertEqual('Fight(start=10:01, duration=01:03)', repr(Fight(None, None, ft, None)))


if __name__ == '__main__':
    unittest.main()
