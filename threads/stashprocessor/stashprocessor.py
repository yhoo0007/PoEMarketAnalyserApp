from threads.stashprocessor.uniquesinfosvc import UniquesInfoSvc
from threads.stashprocessor.currencyexchange import CurrencyExchange
from threads.stashprocessor.structs import Item, ItemUse
from config.shared import DEFAULT_POE_HEADERS, LEAGUE
from config.stashprocessor import DUMP_THRESHOLD, LISTINGS_DIR, NUM_TRACKING_UNIQUES, POE_NINJA_BUILD_OVERVIEW_URL, POE_NINJA_LADDER, POE_NINJA_LANG, POE_NINJA_STATS_URL, PUBLIC_STASH_URL, TRACKING_UNIQUES_FILE, UNIQUES_BLACKLIST, UNIQUES_DATA_FILE
from threading import Thread
import requests
import heapq
import os
import json
import time
import itertools
import re
import pathlib


class StashProcessor(Thread):
    def __init__(self):
        super().__init__()
        self.name = 'Stash Processor'
        self.currency_exchange = CurrencyExchange()
        self.uniques_data_svc = UniquesInfoSvc()

    def fetch_tracking_uniques(self, n=NUM_TRACKING_UNIQUES):
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
        item_uses = heapq.nlargest(n, heap) if n >= 0 else heapq.nsmallest(n, heap)
        uniques = [item_use.item.name for item_use in item_uses]
        return uniques

    def get_tracking_uniques(self, use_cache=True):
        '''
        Gets the tracking uniques from cache or poeninja. Returns a list of item names.
        '''
        if not os.path.exists(TRACKING_UNIQUES_FILE) or use_cache:
            uniques = self.fetch_tracking_uniques()
            pathlib.Path(os.path.split(TRACKING_UNIQUES_FILE)[0]).mkdir(parents=True, exist_ok=True)
            with open(TRACKING_UNIQUES_FILE, 'w+') as tracking_uniques_file:
                json.dump(uniques, tracking_uniques_file, indent=2)
        else:
            with open(TRACKING_UNIQUES_FILE) as tracking_uniques_file:
                uniques = json.load(tracking_uniques_file)
        return uniques

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
                item_info_mod['text']: sum(self.extract_modifier_values(item_mod))
            }
            for item_mod, item_info_mod in zip(
                explicitModifiers, item_info['explicitModifiers']
            ) if not item_info_mod['constant']]
        implicitModifiers = item.get('implicitMods', [])
        if len(implicitModifiers) > 0:
            implicitModifiers = [{
                item_info_mod['text']: sum(self.extract_modifier_values(item_mod))
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
    
    def update_file(self, name, listings):
        file_path = os.path.join(LISTINGS_DIR, f'{name}.json')

        # Update existing file if possible, else write instances as new file
        if os.path.exists(file_path):
            with open(file_path) as json_file:
                json_obj = json.load(json_file)
            json_obj.update(listings)
        else:
            json_obj = listings

        # Dump to file
        if not os.path.exists(file_path):
            pathlib.Path(os.path.split(file_path)[0]).mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w+') as json_file:
            json.dump(json_obj, json_file, indent=2)

    def log(self, msg):
        print(f'[{self.name}]: {msg}')

    def run(self):
        self.log('Starting')
        tracking_uniques = self.get_tracking_uniques()
        listings = {unique: {} for unique in tracking_uniques}
        next_change_id = self.fetch_next_change_id()
        try:
            while True:
                next_request_time = time.time() + 0.51
                stash_data = self.fetch_stash_data(next_change_id)

                accepted_items = 0
                dumps = 0
                processing_time = time.time()
                for item in filter(
                    lambda item: self.item_is_acceptable(item, tracking_uniques),
                    itertools.chain.from_iterable(map(lambda stash: stash['items'], stash_data))
                ):
                    if (price := self.extract_price(item['note'])) is not None:
                        cleaned_item = self.clean_item(item, price)
                        item_name = item['name']
                        listings[item_name][item['id']] = cleaned_item
                        if len(listings[item_name]) > DUMP_THRESHOLD:
                            self.update_file(item_name, listings[item_name])
                            listings[item_name] = {}
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
        except Exception as e:
            self.log(e)
        self.log('Terminating')
