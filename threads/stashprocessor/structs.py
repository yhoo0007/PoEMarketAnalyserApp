class Item:
    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type
    
    def __str__(self):
        return f'{self.name} {self.type}'

class ItemUse:
    def __init__(self, num: int, item: Item):
        self.num = num
        self.item = item
    
    def __lt__(self, obj):
        return self.num < obj.num

    def __le__(self, obj):
        return self.num <= obj.num
    
    def __gt__(self, obj):
        return self.num > obj.num
    
    def __ge__(self, obj):
        return self.num >= obj.num
    
    def __str__(self):
        return f'{self.item}: {self.num}'
