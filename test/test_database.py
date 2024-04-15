from core.database import Database
from os import listdir
import time

db = "/test.db"

start = time.time()

print("\n----- TEST Database -----")
database = Database(db, delete=True, create=True)
database = Database(db)


print("\nTEST: save data types")
database.save("DICTIONARY", {"boolean": "true", "integer": 31, "string": "json"})
database.save("STRING", "Test")
database.save("BOOLEAN", True)
database.save("INTEGER", 42)
assert len(database.keys()) >= 4, "4 keys saved!"
assert database.get("STRING") == "Test", "value must be Test!"
assert database.get("BOOLEAN") == True, "value must be True!"
assert database.get("INTEGER") == 42, "value must be 42!"
assert database.get("DICTIONARY") == {"boolean": "true", "integer": 31, "string": "json"}, "value must be a jsonObject!"
assert type(database.get("STRING")) is str, "Variable is not of type str!"
assert type(database.get("INTEGER")) is int, "Variable is not of type int!"
assert type(database.get("BOOLEAN")) is bool, "Variable is not of type bool!"
assert type(database.get("DICTIONARY")) is dict, "Variable is not of type dict!"
# return object as json
assert type(database.get()) is dict, "database returns not a dict!"


print("\nTEST: update")
database.update(key="DICTIONARY", **{"boolean": "false", "integer": 42, "string": "update"})
assert database.get("DICTIONARY") == {"boolean": "false", "integer": 42, "string": "update"}, "update failed!"


print("\nTEST: delete")
database.save("DELETE", "delete value")
assert database.get("DELETE") == "delete value", "delete value"
database.delete("DELETE")
assert database.get("DELETE") is None, "key not deleted"


print("\nTEST: clear")
assert len(database.keys()) > 0
database.clear()
assert len(database.keys()) == 0, "database not cleared!"


print("\nTEST: drop")
database.drop()
assert (db in listdir()) == False, "database not dropped!"


print("\nTEST: not found exception")
try:
    Database("/test.db", create=False)
except Exception as e:
    exception = True
    assert "database '/test.db' does not exist" in str(e), "exception not occured!"
assert exception == True, "exception not occured!"


print("\n----- TEST PASS -----")
print("\nexecution time: " + str(time.time() - start) + " sec")
