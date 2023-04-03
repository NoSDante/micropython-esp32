class Store(object):
    """
    An object that can be used to keep track of state
    """

    def __init__(self, *args, **kwargs):
        self._storage = {}
        for item in args:
            if isinstance(item, dict):
                self._storage.update(item)
        self._storage.update(kwargs)

    def set(self, key, value):
        """
        Set a particular state variable

        :param key: The name of the state variable
        :param value: The value to assign to the variable
        """
        self._storage[key] = value

    def delete(self, key):
        """
        Delete a particular state variable

        :param key: The name of the state variable
        """
        self._storage.pop(key)

    def get(self, key=None, default=None):
        """
        Get a particular stage variable. Defaults to None.

        :param key: The name of the stage variable
        :param default: The default value if there is no variable
        """
        if key:
            return self._storage.get(key, default)
        else:
            storage = {}
            for key in self._storage:
                storage.update({key: self._storage.get(key)})
            if len(storage) == 0: storage = default
            return storage
