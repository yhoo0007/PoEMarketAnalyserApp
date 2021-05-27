from pyrebase.pyrebase import Firebase
from threads.stashprocessor.uniquesinfosvc import UniquesInfoSvc
from threads.stashprocessor.currencyexchange import CurrencyExchange
from threads.stashprocessor.structs import Item, ItemUse
from config.shared import DEFAULT_POE_HEADERS, FIREBASE_CONFIG, LEAGUE
from config.stashprocessor import DUMP_THRESHOLD, NUM_TRACKING_UNIQUES, POE_NINJA_BUILD_OVERVIEW_URL, POE_NINJA_LADDER, POE_NINJA_LANG, POE_NINJA_STATS_URL, PUBLIC_STASH_URL, UNIQUES_BLACKLIST
from threading import Thread
import requests
import heapq
import time
import itertools
import re
import traceback
import signal


class StashProcessor(Thread):
    def __init__(self):
        super().__init__()
        signal.signal(signal.SIGTERM, self.terminate)
        self.name = 'StashProcessor'
        self.database = Firebase(FIREBASE_CONFIG).database().child(self.name)
        self.currency_exchange = CurrencyExchange()
        self.uniques_data_svc = UniquesInfoSvc()
        self.tracking_uniques = self.get_tracking_uniques()
        self.listings = {unique: {} for unique in self.tracking_uniques}

    def fetch_tracking_uniques_src(self):
        '''
        Fetch n most or least used unique items from poeninja. Returns a list of item names.
        '''
        response_json = requests.get(
            POE_NINJA_BUILD_OVERVIEW_URL,
            params={
                'overview': LEAGUE,
                'type': POE_NINJA_LADDER,
                'language': POE_NINJA_LANG
            }
        ).json()
        unique_items = response_json['uniqueItems']
        unique_item_use = response_json['uniqueItemUse']
        heap = []
        for index, item in enumerate(unique_items):
            if item['name'] not in UNIQUES_BLACKLIST:
                heapq.heappush(
                    heap,
                    ItemUse(len(unique_item_use[str(index)]), Item(item['name'], item['type']))
                )
        item_uses = heapq.nlargest(NUM_TRACKING_UNIQUES, heap) if NUM_TRACKING_UNIQUES >= 0 else heapq.nsmallest(NUM_TRACKING_UNIQUES, heap)
        uniques = [item_use.item.name for item_use in item_uses]
        return uniques

    def fetch_tracking_uniques_db(self):
        '''
        Fetch tracking uniques from Firebase. Returns a list of item names.
        '''
        uniques = self.database.child('trackingUniques').get().val()
        return uniques

    def get_tracking_uniques(self):
        '''
        Gets the tracking uniques from cache or poeninja. Returns a list of item names.
        '''
        tracking_uniques = self.fetch_tracking_uniques_db()
        if tracking_uniques is None:
            self.log('No existing tracking uniques found in Firebase, fetching from source')
            tracking_uniques = self.fetch_tracking_uniques_src()
            self.database.child(self.name).child('trackingUniques').set(tracking_uniques)
        return tracking_uniques

    def fetch_next_change_id(self):
        return requests.get(POE_NINJA_STATS_URL).json()['next_change_id']

    def fetch_stash_data(self, id):
        return requests.get(
                PUBLIC_STASH_URL,
                params={'id': id},
                headers=DEFAULT_POE_HEADERS
            ).json()['stashes']

    def clean_currency(self, currency):
        if currency == 'exa':
            return 'exalted'
        return currency

    def extract_price(self, note):
        pattern = '^~(?:price|b\/o) (\d+(?:\.\d+)?) (\w+)$'
        match = re.search(pattern, note)
        if match:
            amount, currency = match.groups()
            currency = self.clean_currency(currency)
            try:
                return round(float(amount) * self.currency_exchange.get_exchange_rate(currency, 'chaos'), 2)
            except Exception as e:
                self.log(e)
                self.log(note)
        return None

    def item_is_acceptable(self, item, acceptable_items):
        return (
            item['league'].casefold() == LEAGUE.casefold() and
            'note' in item and
            item['identified'] and
            item['name'] in acceptable_items
        )

    def extract_modifier_values(self, modifier):
        pattern = '([+-]?)(\d+(?:\.\d+)?)'
        values = []
        for match in re.finditer(pattern, modifier):
            sign, value = match.groups()
            values.append(-float(value) if sign == '-' else float(value))
        return values

    def clean_item(self, item, price):
        item_info = self.uniques_data_svc.get_unique_item_info(item['extended']['category'], item['name'])
        explicitModifiers = item.get('explicitMods', [])
        if len(explicitModifiers) > 0:
            explicitModifiers = [{
                item_info_mod['text'].replace('\n', ' '): sum(self.extract_modifier_values(item_mod))
            }
            for item_mod, item_info_mod in zip(
                explicitModifiers, item_info['explicitModifiers']
            ) if not item_info_mod['constant']]
        implicitModifiers = item.get('implicitMods', [])
        if len(implicitModifiers) > 0:
            implicitModifiers = [{
                item_info_mod['text'].replace('\n', ' '): sum(self.extract_modifier_values(item_mod))
            }
            for item_mod, item_info_mod in zip(
                implicitModifiers, item_info['implicitModifiers']
            ) if not item_info_mod['constant']]
        return {
            'corrupted': item.get('corrupted', False),
            'explicitMods': explicitModifiers,
            'implicitMods': implicitModifiers,
            'price': price,
        }

    def save_listings_to_db(self, item):
        self.database.child(self.name).child('listings').child(item).update(self.listings[item])

    def log(self, msg):
        print(f'[{self.name}]: {msg}')

    def terminate(self):
        self.log('Terminating')
        for item in self.tracking_uniques:
            self.save_listings_to_db(item)

    def run(self):
        self.log('Starting')
        self.log(f'Num tracking uniques: {len(self.tracking_uniques)}; Dump threshold: {DUMP_THRESHOLD}')
        self.listings = {unique: {} for unique in self.tracking_uniques}
        next_change_id = self.fetch_next_change_id()
        while True:
            try:
                next_request_time = time.time() + 0.51
                stash_data = self.fetch_stash_data(next_change_id)

                accepted_items = 0
                dumps = 0
                processing_time = time.time()
                items = filter(
                    lambda item: self.item_is_acceptable(item, self.tracking_uniques),
                    itertools.chain.from_iterable(map(lambda stash: stash['items'], stash_data))
                )
                for item in items:
                    if (price := self.extract_price(item['note'])) is not None:
                        cleaned_item = self.clean_item(item, price)
                        item_name = item['name']
                        self.listings[item_name][item['id']] = cleaned_item
                        if len(self.listings[item_name]) > DUMP_THRESHOLD:
                            self.save_listings_to_db(item_name)
                            self.listings[item_name] = {}
                            dumps += 1
                        accepted_items += 1
                processing_time = time.time() - processing_time
                self.log(f'Processed: ({accepted_items};{dumps}) items in {round(processing_time * 1000, 2)}ms')

                current_time = time.time()
                if next_request_time <= current_time:
                    next_change_id = self.fetch_next_change_id()
                else:
                    next_change_id = stash_data['next_change_id']
                    delay = next_request_time - current_time
                    time.sleep(max(delay, 0))
            except Exception:
                self.log(item)
                self.log(traceback.format_exc())
                self.log('Saving listings to Firebase')
                for item in self.tracking_uniques:
                    self.save_listings_to_db(item)
