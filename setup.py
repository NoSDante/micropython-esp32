try:
    from app.database import Database
except ImportError as e:
    raise ImportError("cannot import module", e)

# setup
def setup():     
    """
    Get data from JSON-File
    Save data to DB-File
    """
    def setConfig(database, json_file, path="/config/", delete=False):
        database = Database(database=database, create=True)
        database.clear()
        json_data = database.get_json_data(json_file, path)
        for key, value in json_data.items():
            database.save(key=key, value=value)
        if delete:
            import os
            os.remove(path+json_file)
    
    # boot config
    setConfig("/boot.db", "boot.json")
    
    # network config
    setConfig("/network.db", "network.json", delete=False)
    
    # app config(s)
    setConfig("/app/app.db", "app.json",     delete=False)
    setConfig("/app/app.db", "tft.json",     delete=False)
    setConfig("/app/app.db", "sensors.json", delete=False)

if __name__ == '__main__':
     setup()
