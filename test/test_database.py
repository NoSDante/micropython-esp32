from core.database import Database
import time

start = time.time()

db = "/test.db"

print("----- Test Database -----")
print(db)

print("----- INIT -----")
database = Database(db, delete=True, create=True)
print(database)
database = Database(db)
print(database)

print("----- SAVE -----")
"""
save different data types
"""
database.save("DICTIONARY", {"boolean": "true", "integer": 31, "string": "json"})
database.save("STRING", "Test")
database.save("BOOLEAN", True)
database.save("INTEGER", 42)
print("save DICTIONARY:", {"boolean": "true", "integer": 31, "string": "json"})
print("save STRING:", "Test")
print("save BOOLEAN:", True)
print("save STRING:", 42)

print("----- GET KEY -----")
"""
return value by key
"""
print("keys found:", len(database.keys()))
print(database.get("STRING"))
print(database.get("BOOLEAN"))
print(database.get("INTEGER"))
print(database.get("DICTIONARY"))

print("----- GET ALL -----")
"""
return object as json
"""
print(database.get())

print("----- TYPES -----")
"""
get correct data type
"""
if isinstance(database.get("STRING"), str): print("STRING:PASS")
if isinstance(database.get("INTEGER"), int): print("INTEGER:PASS")
if isinstance(database.get("BOOLEAN"), bool): print("BOOLEAN:PASS")
if isinstance(database.get("DICTIONARY"), dict): print("DICTIONARY:PASS")

print("----- UPDATE -----")
"""
update a dictionary
"""
database.update(key="DICTIONARY", **{"boolean": "false", "integer": 42, "string": "update"})
print(database.get("DICTIONARY"))

print("----- DELETE -----")
"""
delete key
"""
database.save("DELETE", "delete value")
print("saved to delete:", database.get("DELETE"))
database.delete("DELETE")
print("None if deleted:", database.get("DELETE"))

print("----- KEYS -----")
"""
returns all keys
"""
keys = database.keys()
for key in keys:
    print("key:", key)

print("----- CLEAR -----")
"""
clear all keys
"""
if len(keys) != 0:
    print("keys before:", len(keys))
    print("clear...")
    database.clear()
    keys = database.keys()
    print("keys after:", len(keys))

print("----- DROP -----")
"""
delete db-file
"""
print("drop database")
database.drop()
del database

print("----- EXCEPTION -----")
"""
not found exception
"""
try:
    Database("/test.db", create=False)
except Exception as e:
    print(e)

print("\n----- TEST FINISHED -----")
print("execution time: " + str(time.time() - start) + " sec")
