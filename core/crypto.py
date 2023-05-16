from cryptolib import aes


class Crypto():
    
    MODE_ECB = 1
    MODE_CBC = 2
    MODE_CTR = 6
    BLOCK_SIZE = 32
    
    class ValueErrorException(Exception):
        pass
    
    def __init__(self, key, mode=1, blocksize=32, debug=False):
        self.key = key  # key size must be 16 or 32
        self.mode = mode
        self.debug = debug
        self.blocksize = self.BLOCK_SIZE
        if blocksize is not None: self.blocksize = blocksize
        if self.mode == self.MODE_CBC:
            self.blocksize = 16

    def _init(self, iv=None):
        if self.mode == self.MODE_ECB:
            self.aes = aes(self.key, self.mode)
        if self.mode == self.MODE_CBC:
            self.aes = aes(self.key, self.mode, iv)

    # decrypt
    def decrypt(self, value):
        if self.mode == self.MODE_ECB:
            self._init()
            return self.aes.decrypt(self._padding(value))
        if self.mode == self.MODE_CBC:
            iv = value[:self.blocksize]
            self._init(iv)
            value = self.aes.decrypt(value)[self.blocksize:]
            value = value.decode('utf-8')
            return value.split(" ")[0]

    # encrypt
    def encrypt(self, value):
        if self.mode == self.MODE_ECB:
            self._init()
            value = self.aes.encrypt(value)
            value = value.decode('utf-8')
            return value.split(" ")[0]
        if self.mode == self.MODE_CBC:
            # Generate iv with HW random generator
            iv = uos.urandom(self.blocksize)
            self._init(iv)
            return iv + self.aes.encrypt(self._padding(value))

    # padding value with space
    def _padding(self, value): 
        pad = self.blocksize - len(value) % self.blocksize
        return value + " "*pad
