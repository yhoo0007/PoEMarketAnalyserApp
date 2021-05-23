from config.shared import DATA_DIR
import os


NUM_TRACKING_UNIQUES = 30  # number of uniques to scan for
DUMP_THRESHOLD = 20  # number of items in dict before updating to disk
LISTINGS_DIR = os.path.join(DATA_DIR, 'listings')
UNIQUES_DATA_FILE = os.path.join(DATA_DIR, 'uniques.json')
TRACKING_UNIQUES_FILE = os.path.join(DATA_DIR, 'tracking_uniques.json')

POE_NINJA_WTV = '421b35051547a888e1390ffbd9aa7428'
POE_NINJA_BUILD_OVERVIEW_URL = f'https://poe.ninja/api/data/{POE_NINJA_WTV}/getbuildoverview'
POE_NINJA_ITEM_OVERVIEW_URL = 'https://poe.ninja/api/data/ItemOverview'
POE_NINJA_LADDER = 'exp'
POE_NINJA_LANG = 'en'
POE_NINJA_STATS_URL = 'https://poe.ninja/api/Data/GetStats'

UNIQUES_BLACKLIST = (
    'Watcher\'s Eye',
    'Glorious Vanity',
    'Cinderswallow Urn',
    'Conqueror\'s Efficiency',
    'Essence Worm',
    'Might of the Meek',
    
)

PUBLIC_STASH_URL = 'http://www.pathofexile.com/api/public-stash-tabs'

POE_NINJA_CURRENCY_OVERVIEW_URL = 'https://poe.ninja/api/data/CurrencyOverview'

CURRENCY_KEYS = (
    'alt',
    'fusing',
    'alch',
    'chaos',
    'gcp',
    'exalted',
    'chrome',
    'jewellers',
    'engineers',
    'infused-engineers-orb',
    'chance',
    'chisel',
    'scour',
    'blessed',
    'regret',
    'regal',
    'divine',
    'vaal',
    'annul',
    'orb-of-binding',
    'ancient-orb',
    'orb-of-horizons',
    'harbingers-orb',
    'wisdom',
    'portal',
    'scrap',
    'whetstone',
    'bauble',
    'transmute',
    'aug',
    'mirror',
    'eternal',
    'p',
    'rogues-marker',
    'silver',
    'crusaders-exalted-orb',
    'redeemers-exalted-orb',
    'hunters-exalted-orb',
    'warlords-exalted-orb',
    'awakeners-orb',
    'mavens-orb',
    'facetors',
    'prime-regrading-lens',
    'secondary-regrading-lens',
    'tempering-orb',
    'tailoring-orb',
    'stacked-deck',
    'ritual-vessel',
    'apprentice-sextant',
    'journeyman-sextant',
    'master-sextant',
    'elevated-sextant',
    'orb-of-unmaking',
    'blessing-xoph',
    'blessing-tul',
    'blessing-esh',
    'blessing-uul-netol',
    'blessing-chayula',
    'veiled-chaos-orb',
)

CURRENCY_NAMES = (
    'Orb of Alteration',
    'Orb of Fusing',
    'Orb of Alchemy',
    'Chaos Orb',
    'Gemcutter\'s Prism',
    'Exalted Orb',
    'Chromatic Orb',
    'Jeweller\'s Orb',
    'Engineer\'s Orb',
    'Infused Engineer\'s Orb',
    'Orb of Chance',
    'Cartographer\'s Chisel',
    'Orb of Scouring',
    'Blessed Orb',
    'Orb of Regret',
    'Regal Orb',
    'Divine Orb',
    'Vaal Orb',
    'Orb of Annulment',
    'Orb of Binding',
    'Ancient Orb',
    'Orb of Horizons',
    'Harbinger\'s Orb',
    'Scroll of Wisdom',
    'Portal Scroll',
    'Armourer\'s Scrap',
    'Blacksmith\'s Whetstone',
    'Glassblower\'s Bauble',
    'Orb of Transmutation',
    'Orb of Augmentation',
    'Mirror of Kalandra',
    'Eternal Orb',
    'Perandus Coin',
    'Rogue\'s Marker',
    'Silver Coin',
    'Crusader\'s Exalted Orb',
    'Redeemer\'s Exalted Orb',
    'Hunter\'s Exalted Orb',
    'Warlord\'s Exalted Orb',
    'Awakener\'s Orb',
    'Maven\'s Orb',
    'Facetor\'s Lens',
    'Prime Regrading Lens',
    'Secondary Regrading Lens',
    'Tempering Orb',
    'Tailoring Orb',
    'Stacked Deck',
    'Ritual Vessel',
    'Simple Sextant',
    'Prime Sextant',
    'Awakened Sextant',
    'Elevated Sextant',
    'Orb of Unmaking',
    'Blessing of Xoph',
    'Blessing of Tul',
    'Blessing of Esh',
    'Blessing of Uul-Netol',
    'Blessing of Chayula',
    'Veiled Chaos Orb',
)

class _TwoWayDict:
    def __init__(self, iterable):
        self._dict = {}
        for k, v in iterable:
            self._dict[k] = v
            self._dict[v] = k
    
    def __getitem__(self, key):
        return self._dict[key]
    
    def __setitem__(self, key, obj):
        self._dict[key] = obj
        self._dict[obj] = key
    
    def __contains__(self, key):
        return key in self._dict

CURRENCIES = _TwoWayDict(zip(CURRENCY_KEYS, CURRENCY_NAMES))
