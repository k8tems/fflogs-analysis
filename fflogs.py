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
    def __init__(self, api, ft, report_id):
        self.api = api
        self.ft = ft
        self.report_id = report_id

    def get_tables(self, view, **params):
        # TODO: merge with events
        params = params or dict()
        params = {**params, **{'start': self.ft.start_ms, 'end': self.ft.end_ms}}
        return self.api.get(f'report/tables/{view}/{self.report_id}', params)

    def gen_events(self, view, **params):
        start = self.ft.start_ms

        params = params or dict()
        params = {**params, **{'end': self.ft.end_ms}}

        while 1:
            params['start'] = start
            result = self.api.get(f'report/events/{view}/{self.report_id}', params)['events']
            if not result:  # いつかレスポンスの仕様変更があるかもしれない
                break
            yield result
            if len(result) == 1:  # 追加しておきたいので上の条件と別扱い
                break
            start = result[-1]['timestamp']
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


class Report(object):
    def __init__(self, report_id, fights, start):
        self.report_id = report_id
        self.fights = fights
        self.start = start

    @classmethod
    def create(cls, api, report_id):
        resp = api.get(f'report/fights/{report_id}')

        def create_ft(f):
            start_dt = epoch_to_dt(resp['start'] + f['start_time'])
            end_dt = epoch_to_dt(resp['start'] + f['end_time'])
            return FightTime(start_dt, end_dt, f['start_time'], f['end_time'])

        fights = [Fight(api, create_ft(f), report_id) for f in resp['fights']]
        return Report(report_id, fights, start=epoch_to_dt(resp['start']))

