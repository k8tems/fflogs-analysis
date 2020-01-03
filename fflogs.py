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
    def __init__(self, start_ms, end_ms):
        self.start_ms = start_ms
        self.end_ms = end_ms

    @property
    def duration_ms(self):
        return self.end_ms - self.start_ms

    @property
    def start(self):
        return self.start_ms / 1000

    @property
    def end(self):
        return self.end_ms / 1000

    @property
    def duration(self):
        return self.end - self.start


def epoch_to_dt(epoch):
    dt = datetime.fromtimestamp(epoch)
    return timezone('Asia/Tokyo').localize(dt)


class Report(object):
    def __init__(self, api, report_id, start):
        self.api = api
        self.report_id = report_id
        self.start = start

    @classmethod
    def create(cls, api, report_id):
        resp = api.get(f'report/fights/{report_id}')
        return Report(api, report_id, epoch_to_dt(resp['start']/1000))

    def get_fights(self):
        fights = self.api.get(f'report/fights/{self.report_id}')
        return [Fight(self.api, FightTime(f['start_time'], f['end_time']), self.report_id)
                for f in fights['fights']]


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
