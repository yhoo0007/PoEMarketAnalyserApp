from config.shared import LEAGUE, LEAGUE_CAP
from config.stashprocessor import CURRENCIES, POE_NINJA_CURRENCY_OVERVIEW_URL, POE_NINJA_LANG
from datetime import date, datetime, timedelta
import requests


class CurrencyExchange:
    def __init__(self, cache_expiry=timedelta(days=1)):
        self.name = 'Currency Exchange'
        self.cache_expiry = cache_expiry
        self.last_refresh = datetime.now()
        self.exchange_rates = self.fetch_exchange_rates()

    def flatten_lines(self, lines):
        ret = []
        for sublist in lines:
            if not isinstance(sublist, list):
                return lines
            ret += sublist
        return ret

    def log(self, msg):
        print(f'[{self.name}]: {msg}')

    def fetch_exchange_rates(self):
        self.log('Fetching exchange rates')
        self.last_refresh = datetime.now()
        response_json = requests.get(
            POE_NINJA_CURRENCY_OVERVIEW_URL,
            params={
                'league': LEAGUE_CAP,
                'type': 'Currency',
                'language': POE_NINJA_LANG,
            }
        ).json()
        currencies_chaos_val = {}
        for currency in self.flatten_lines(response_json['lines']):
            currency_type_name = currency['currencyTypeName']
            if currency_type_name in CURRENCIES:
                currency_key = CURRENCIES[currency_type_name]
                currencies_chaos_val[currency_key] = float(currency['chaosEquivalent'])
            else:
                self.log(f'{currency_type_name} is not a recognized currency')
        currencies_chaos_val['chaos'] = 1.0
        return currencies_chaos_val

    def is_cache_expired(self):
        return datetime.now() > (self.last_refresh + self.cache_expiry)

    def get_exchange_rate(self, have, want):
        if have == want:
            return 1.0
        if self.is_cache_expired():
            self.exchange_rates = self.fetch_exchange_rates()
        return self.exchange_rates[have] / self.exchange_rates[want]
