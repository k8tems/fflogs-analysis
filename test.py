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
            'fights': [{'start_time': 496584, 'end_time': 751596}, {'start_time': 752596, 'end_time': 753596}],
            'friendlies': [
                {'guid': 1, 'name': 'foo', 'type': 'bar', 'id': 0},
                {'guid': 2, 'name': 'baz', 'type': 'baaz', 'id': 0}],
            'friendlyPets': []}
        self.report = Report.create(self.api, 'report_id')

    def test_report(self):
        self.api.get.assert_called_with('report/fights/report_id')
        self.assertEqual(create_dt(2020, 1, 2, 21, 58, 23, 454000), self.report.start)

    def test_first_fight(self):
        f = self.report.fights[0]
        self.assertEqual(496584, f.ft.start_ms)
        self.assertEqual(create_dt(2020, 1, 2, 22, 6, 40, 38000), f.ft.start_dt)
        self.assertEqual(751596, f.ft.end_ms)
        self.assertEqual(create_dt(2020, 1, 2, 22, 10, 55, 50000), f.ft.end_dt)
        self.assertEqual([{'guid': 1, 'name': 'foo', 'class': 'bar', 'id': 0, 'pets': []},
                          {'guid': 2, 'name': 'baz', 'class': 'baaz', 'id': 0, 'pets': []}],
                         f.players)

    def test_second_fight(self):
        # 2つ目の戦闘が処理されてる事実だけテスト
        f = self.report.fights[1]
        self.assertEqual(752596, f.ft.start_ms)
        self.assertEqual(753596, f.ft.end_ms)
        self.assertEqual(f.players, self.report.fights[0].players)


class TestFight(unittest.TestCase):
    def setUp(self):
        self.api = MagicMock()
        self.api.get.side_effect = [{'events': [{'timestamp': 100, 'foo': 'bar'}, {'timestamp': 200, 'baz': 'baaz'}]},
                                    {'events': [{'timestamp': 300, 'qux': 'quux'}]}]
        start_dt = datetime(2019, 12, 31, 10, 1)
        end_dt = start_dt + timedelta(seconds=63)
        ft = FightTime(start_dt, end_dt, start_ms=100, end_ms=63100)
        players = None
        self.f = Fight(self.api, 'report_id', players, ft)

    def test_gen_events(self):
        gen = self.f.gen_events('damage-done', foo='bar')
        ret_0 = next(gen)
        ret_1 = next(gen)

        self.assertEqual('report/events/damage-done/report_id', self.api.get.call_args_list[0][0][0])
        self.assertEqual({'foo': 'bar', 'start': 100, 'end': 63100}, self.api.get.call_args_list[0][0][1])

        self.assertEqual('report/events/damage-done/report_id', self.api.get.call_args_list[1][0][0])
        # `start`をインクリメントしないとリストの境界で被りが発生する
        self.assertEqual({'foo': 'bar', 'start': 201, 'end': 63100}, self.api.get.call_args_list[1][0][1])

        # 開始時間に対して相対的なタイムスタンプ(秒)に変換されてるはず
        # elapsed以外のデータもきちんと保存されてるか確認
        self.assertEqual([{'timestamp': 0, 'foo': 'bar'},
                          {'timestamp': 100, 'baz': 'baaz'}], ret_0)
        self.assertEqual([{'timestamp': 200, 'qux': 'quux'}], ret_1)

    def test_repr(self):
        self.assertEqual('Fight(ft=FightTime(start=10:01, duration=01:03))', repr(self.f))


class TestPlayerPool(unittest.TestCase):
    def test_search_by_class_and_name(self):
        fixture = [{'class': 'DarkKnight', 'id': 1, 'name': 'Yoshida'},
                   {'class': 'WhiteMage', 'id': 2, 'name': 'Yoshida'},
                   {'class': 'DarkKnight', 'id': 3, 'name': 'Oshida'}]
        self.assertEqual(fixture[0], PlayerPool(fixture).search(class_='DarkKnight', name='Yoshida'))

    def test_search_by_class(self):
        fixture = [{'class': 'DarkKnight', 'id': 1, 'name': 'Yoshida'},
                   {'class': 'WhiteMage', 'id': 2, 'name': 'Yoshida'}]
        self.assertEqual(fixture[0], PlayerPool(fixture).search(class_='DarkKnight'))

    def test_search_by_name(self):
        fixture = [{'class': 'DarkKnight', 'id': 1, 'name': 'Yoshida'},
                   {'class': 'DarkKnight', 'id': 2, 'name': 'Oshida'}]
        self.assertEqual(fixture[0], PlayerPool(fixture).search(name='Yoshida'))

    def test_multiple_results(self):
        fixture = [{'class': 'DarkKnight', 'id': 1, 'name': 'Yoshida'},
                   {'class': 'WhiteMage', 'id': 2, 'name': 'Yoshida'}]
        self.assertRaises(PlayerPool.MultipleMatches, PlayerPool(fixture).search, name='Yoshida')

    def test_return_none_for_no_matches(self):
        fixture = [{'class': 'DarkKnight', 'id': 1, 'name': 'Yoshida'}]
        self.assertIsNone(PlayerPool(fixture).search(name='Oshida'))


if __name__ == '__main__':
    unittest.main()
