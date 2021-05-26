from pyrebase.pyrebase import Firebase
from config.shared import FIREBASE_CONFIG, LEAGUE_CAP
from config.stashprocessor import POE_NINJA_ITEM_OVERVIEW_URL, POE_NINJA_LANG
import re
import requests


class UniquesInfoSvc:
    def __init__(self):
        self.name = 'UniquesInfoSvc'
        self.database = Firebase(FIREBASE_CONFIG).database().child(self.name)
        self._uniques_info = self.get_uniques_info()

    def log(self, msg):
        print(f'[{self.name}]: {msg}')

    def get_uniques_info(self):
        uniques = self.fetch_uniques_data_db()
        if uniques is None:
            self.log('No existing uniques data found in Firebase, fetching from source')
            uniques = self.fetch_uniques_data_src()
            self.database.update(uniques)
        return uniques

    def flatten_lines(self, lines):
        ret = []
        for sublist in lines:
            if not isinstance(sublist, list):
                return lines
            ret += sublist
        return ret

    def extract_ranges(self, string):
        # matches constants and ranges in 4 groups:
        # 1. sign (optional)
        # 2. ignore
        # 3. lower number (possibly a negative number)
        # 4. upper number (optional)
        pattern = '([+-]?)(\()?([+-]?\d+(?:\.\d+)?)(?(2)-(\d+(?:\.\d+)?)|(?!\)))'
        ranges = []
        for match in re.finditer(pattern, string):
            sign, _, lower, upper = match.groups()
            lower = float(lower)
            upper = float(upper) if upper is not None else lower  # empty 'upper' indicates constant
            ranges.append({
                'min': -lower if sign == '-' else lower,
                'max': -upper if sign == '-' else upper,
            })
        return ranges

    def modifier_is_constant(self, ranges):
        constant = all([
            r['min'] == r['max']
        for r in ranges])
        return constant

    def fetch_uniques_data_db(self):
        uniques = self.database.get().val()
        # Re-create fields in case they are empty because FB does not store empty fields -_-
        for category_items in uniques.values():
            for item in category_items.values():
                if 'implicitModifiers' not in item:
                    item['implicitModifiers'] = []
                if 'explicitModifiers' not in item:
                    item['explicitModifiers'] = []
                if 'links' not in item:
                    item['links'] = None
                if 'mapTier' not in item:
                    item['mapTier'] = None
        return uniques

    def fetch_uniques_data_src(self):
        UNIQUE_ITEM_TYPES = {
            'UniqueAccessory': 'accessories',
            'UniqueArmour': 'armour',
            'UniqueFlask': 'flasks',
            'UniqueJewel': 'jewels',
            'UniqueMap': 'maps',
            'UniqueWeapon': 'weapons',
        }
        uniques = {}
        for item_type_poeninja, item_type in UNIQUE_ITEM_TYPES.items():
            self.log(f'Fetching unique items type: {item_type}')
            response_json = requests.get(
                POE_NINJA_ITEM_OVERVIEW_URL,
                params={
                    'league': LEAGUE_CAP,
                    'type': item_type_poeninja,
                    'language': POE_NINJA_LANG,
                }
            ).json()
            items = {}
            for item in self.flatten_lines(response_json['lines']):
                if not item['detailsId'].endswith('-relic'):  # filter out relic items
                    for mod_type in ['explicitModifiers', 'implicitModifiers']:
                        for modifier in item[mod_type]:
                            ranges = self.extract_ranges(modifier['text'])
                            constant = self.modifier_is_constant(ranges)
                            modifier['ranges'] = ranges
                            modifier['constant'] = constant
                    items[item['name']] = {
                        'detailsId': item['detailsId'],
                        'name': item['name'],
                        'explicitModifiers': item['explicitModifiers'],
                        'implicitModifiers': item['implicitModifiers'],
                        'links': item.get('links', None),
                        'mapTier': item.get('mapTier', None),
                    }
            uniques[item_type] = items
        return uniques

    def get_unique_item_info(self, item_category, item_name):
        try:
            return self._uniques_info[item_category][item_name]
        except KeyError:
            return None
