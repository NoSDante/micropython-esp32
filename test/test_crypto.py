from core.crypto import Crypto
import time


print("\n----- TEST Crypto -----")
KEY = b'x!A%D*G-KaNdRgUkXp2s5v8y/B?E(H+M'
VALUE = "secret"

start = time.time()


print('\nTEST: AES-ECB')
crypto = Crypto(key=KEY)
assert crypto.decrypt(VALUE) == b'\xdb\x83 \xb5\xdd:\x95\xf9\xd8\xe1\xd6\x14\x06\xcd/d\x97\xce\xd7\xb3\x116"&\xe0\x99yI\x7fb#\xa5'
assert crypto.encrypt(crypto.decrypt(VALUE)) == "secret", "encrypted value invalid!"
del crypto


print('\nTEST: AES-CBC')
crypto = Crypto(key=KEY,mode=2)
assert crypto.decrypt(crypto.encrypt(VALUE)) == "secret", "encrypted value invalid!"


print("\n----- TEST PASS -----")
print("\nexecution time: " + str(time.time() - start) + " sec")
