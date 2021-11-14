from os import remove
try:
    from core.database import Database
except ImportError as e:
    raise ImportError("cannot import module", e)

# setup
def setup():
    """
    Get data from JSON-File
    Save data to DB-File
    """
    def setConfig(db_file, json_files, path="/config/", delete_json=False, delete_db=False):
        database = Database(database=db_file, pagesize=1024, delete=delete_db, create=True)
        database.clear()
        for json_file in json_files:
            json_data = database.get_json_data(json_file, path)
            if json_data is None: continue
            for key, value in json_data.items(): database.save(key=key, value=value)
            if delete_json: remove(path+json_file)
        if len(database.keys()) == 0: database.drop()
        else: print("{} keys saved in database '{}'".format(len(database.keys()), db_file))
    
    # boot config
    setConfig("/boot.db", ["boot.json"])
    
    # network config
    setConfig("/network.db", ["network.json"], delete_json=False, delete_db=True)
    
    # app config(s)
    setConfig("/app/app.db", ["app.json", "tft.json", "sensors.json"], delete_json=False, delete_db=True)
    

if __name__ == '__main__':
     setup()
