import btree, json


class Database():
    
    class NotFoundException(Exception):
        pass
    
    class NotDefinedException(Exception):
        pass
    
    def __init__(self, database="/micro.db", pagesize=1024, create=False):
        self.btree = None
        self.create = create
        self.database = database
        self.pagesize = pagesize
        self._open()
        
    def _open(self):
        """
        Open or make db-file
        """
        try:
            self.file = open(self.database, "r+b")
        except OSError:
            if self.create: self.file = open(self.database, "w+b")
            else: raise self.NotFoundException("database '{}' does not exist".format(self.database))
        self.btree = btree.open(self.file, pagesize=self.pagesize)

    def _close(self):
        """
        Close db-file and btree
        """
        self.file.close()
        self.btree.close()

    def keys(self):
        """
        Return keys
        """
        if self.btree is None: raise self.NotDefinedException("database undefined")
        self._open()
        keys = []
        for key in self.btree: keys.append(key.decode('utf8'))
        self._close()
        return keys

    def get(self, key, default=None, as_json=True):
        """
        Get value by key
        """
        if self.btree is None: raise self.NotDefinedException("database undefined")
        if isinstance(key, str): key = key.encode('utf8')
        self._open()    
        value = self.btree.get(key)
        if value and as_json:
            try: value = json.loads(value.decode('utf8'))
            except ValueError: value = value.decode('utf-8')
        elif not value: value = default
        self._close()
        return value

    def save(self, key, value):
        """
        Save value by key
        """
        if self.btree is None: raise self.NotDefinedException("database undefined")
        self._open()
        self.btree[self.encode(key)] = self.encode(value)
        self.btree.flush()
        self._close()

    def delete(self, key):
        if self.btree is None: raise self.NotDefinedException("database undefined")
        """
        Delete key in tree
        """
        if self.get(key):
            self._open()   
            del self.btree[key]
            self.btree.flush()
        self._close()
    
    def drop(self):
        """
        Delete db-file
        """
        from os import remove
        remove(self.database)
        self.btree = None
        
    def clear(self):
        """
        Delete all keys
        """
        for key in self.keys(): self.delete(key)
    
    def update(self, key=None, **kwargs):
        """
        Update json value
        """
        value = self.get(key)
        if isinstance(value, dict):
            value.update(kwargs)
            self.save(key, value)

    def encode(self, value):
        """
        Encoding value
        """
        if   isinstance(value, str):  value = value.encode('utf8')
        elif isinstance(value, bool): value = str(value).lower()
        elif isinstance(value, int):  value = str(value)
        elif isinstance(value, dict): value = json.dumps(value).encode('utf8')
        return value

    def get_json_data(self, file, path=""):
        """
        Get data from JSON-File
        """
        if len(file) == 0: raise ValueError('filename undefined')
        from os import listdir
        if not file in (listdir(path)): raise self.NotFoundException("file '{}' does not exist".format(file))
        file = path + file
        with open(file) as json_file: json_data = json.load(json_file)
        return json_data
