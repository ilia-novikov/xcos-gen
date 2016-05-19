class SafeDict(dict):
    def __init__(self, d, **kwargs):
        super().__init__(**kwargs)
        for key in d.keys():
            self[key] = d[key]

    def __missing__(self, key):
        return '{' + key + '}'
