import btree, json


class Database():
    
    class NotFoundException(Exception):
        pass
    
    class NotDefinedException(Exception):
        pass
    
    def __init__(self, database="/micro.db", pagesize=1024, delete=False, create=False):
        self.btree = None
        self.create = create
        self.database = database
        self.pagesize = pagesize
        if delete: self.drop()
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

    def get(self, key=None, default=None, as_json=True):
        """
        Get value by key
        """
        if self.btree is None: raise self.NotDefinedException("database undefined")
        if isinstance(key, str): key = key.encode('utf8')
        self._open()
        if key:
            value = self.btree.get(key)
            if value and as_json:
                try: value = json.loads(value.decode('utf8'))
                except ValueError: value = value.decode('utf-8')
            elif not value: value = default
        else:
            value = {}
            for key in self.btree:
                value.update( {key.decode('utf8') : self.btree.get(key).decode('utf8')} )
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
        from os import remove, listdir
        path = self.database.replace("/", "", 1).split("/")[0] if len(self.database.replace("/", "", 1).split("/")) > 1 else ""        
        file = self.database.replace("/", "", 1).split("/")[1] if len(self.database.replace("/", "", 1).split("/")) > 1 else self.database.replace("/", "", 1)
        if file in listdir(path): remove(self.database)
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
        if not isinstance(file, str): raise ValueError('file is not defined')
        from os import listdir
        if not file in (listdir(path)): raise self.NotFoundException("file '{}' does not exist".format(file))
        with open(path+file) as json_file:
            try: json_data = json.load(json_file)
            except: json_data = None
        return json_data
