import time
import requests
from datetime import datetime
from pytz import timezone


class APIError(RuntimeError):
    pass


class API(object):
    def __init__(self, api_key):
        self.api_key = api_key

    def get(self, path, params=None):
        params = params or dict()
        params = {**params, **{'api_key': self.api_key}}
        resp = requests.get(f'https://www.fflogs.com:443/v1/{path}', params=params)

        if resp.status_code != 200:
            raise APIError(resp.status_code)

        return resp.json()

    def test(self):
        return 'page' in self.get(f'rankings/encounter/66').keys()


class FightTime(object):
    def __init__(self, start_dt, end_dt, start_ms, end_ms):
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.start_ms = start_ms
        self.end_ms = end_ms

    def __repr__(self):
        return f'FightTime(start={self.start_fmt}, duration={self.duration_fmt})'

    @property
    def start_fmt(self):
        return '%02d:%02d' % (self.start_dt.hour, self.start_dt.minute)

    @property
    def duration_fmt(self):
        return '%02d:%02d' % (self.duration_s // 60, self.duration_s % 60)

    @property
    def duration_ms(self):
        return self.end_ms - self.start_ms

    @property
    def start_s(self):
        return self.start_ms / 1000

    @property
    def end_s(self):
        return self.end_ms / 1000

    @property
    def duration_s(self):
        return self.end_s - self.start_s


class Fight(object):
    def __init__(self, api, report_id, players, ft):
        self.api = api
        self.report_id = report_id
        self.players = players
        self.ft = ft

    def __repr__(self):
        return f'Fight(ft={self.ft})'

    def fix_timestamp(self, e):
        # メソッド内でミューテートしたくない
        e = e.copy()
        e['timestamp'] -= self.ft.start_ms
        return e

    def get_tables(self, view, **params):
        params = params or dict()
        params = {**params, **{'start': self.ft.start_ms, 'end': self.ft.end_ms}}
        return self.api.get(f'report/tables/{view}/{self.report_id}', params)

    def gen_events(self, view, **params):
        start = self.ft.start_ms

        params = params or dict()
        params = {**params, **{'end': self.ft.end_ms}}

        while 1:
            # パラメータ使いまわしてるとテストのアサーションがうまく行かないのでコピー必須
            p = params.copy()
            p['start'] = start
            events = self.api.get(f'report/events/{view}/{self.report_id}', p)['events']
            # 現時点では最後のデータに到達すると要素が1つの配列が返される仕様だが、
            # 今後どうなるかわからないので一応空のチェックも行う
            if not events:
                break
            # 下で生のタイムスタンプが参照されてるので`events`を変えてはならない
            yield [self.fix_timestamp(e) for e in events]
            # 最期のデータに到達して返された要素が1つの配列も結果に追加したいので、
            # `yield`の後にチェックしてループを抜ける
            if len(events) == 1:
                break
            start = events[-1]['timestamp']  # ここで生のタイムスタンプが参照されてる事に注意
            start += 1  # 境界の被り防止

    def get_events(self, *args, **kwargs):
        # ジェネレータと分けた方がテストしやすいし、
        # レート制限対策も呼び出し元で出来る
        events = []
        for chunk in self.gen_events(*args, **kwargs):
            events += chunk
            time.sleep(1)
        return events


def epoch_to_dt(epoch):
    """epochはms単位を想定"""
    dt = datetime.fromtimestamp(epoch/1000)
    return timezone('Asia/Tokyo').localize(dt)


class PlayerPool(list):
    class MultipleMatches(RuntimeError):
        pass

    def search(self, class_=None, name=None):
        matches = []
        for p in self:
            match = False
            if class_ and name:
                match = p['class'] == class_ and p['name'] == name
            elif class_:
                match = p['class'] == class_
            elif name:
                match = p['name'] == name
            if match:
                matches.append(p)
        if len(matches) >= 2:
            raise self.MultipleMatches('')
        if len(matches):
            return matches[0]

    def search_by_class(self, c):
        for p in self:
            if p['class'] == c:
                return p

    def search_by_id(self, id):
        for p in self:
            if p['id'] == id:
                return p


def parse_players(resp):
    ret = PlayerPool()
    for f in resp['friendlies']:
        ret.append({'name': f['name'], 'class': f['type'],
                     'guid': f['guid'], 'id': f['id'], 'pets': []})
    for f in resp['friendlyPets']:
        ret.search_by_id(f['petOwner'])['pets'].append(f['guid'])
    return ret


class Report(object):
    def __init__(self, report_id, fights, start):
        self.report_id = report_id
        self.fights = fights
        self.start = start

    @staticmethod
    def create_ft(report_start, fight_start, fight_end):
        """
        :param report_start: レポートの作成時間
        :param fight_start: 戦闘の開始時間(`report_start`相対ms)
        :param fight_end: 戦闘終了時間
        ※`report_start`は`Report`の範疇なので当関数を`Fight`に移動したくない
        """
        start_dt = epoch_to_dt(report_start + fight_start)
        end_dt = epoch_to_dt(report_start + fight_end)
        return FightTime(start_dt, end_dt, fight_start, fight_end)

    @classmethod
    def create(cls, api, report_id):
        resp = api.get(f'report/fights/{report_id}')
        players = parse_players(resp)

        fights = [Fight(api, report_id, players,
                        cls.create_ft(resp['start'], f['start_time'], f['end_time']))
                  for f in resp['fights']]
        return Report(report_id, fights, start=epoch_to_dt(resp['start']))
