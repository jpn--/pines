

import pickle, base64, zlib



def squeeze(item):
    return base64.standard_b64encode(zlib.compress(pickle.dumps(item)))


def inflate(squeezed):
    return pickle.loads(zlib.decompress(base64.standard_b64decode(squeezed)))


