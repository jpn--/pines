

import pickle, base64, zlib, hashlib



def squeeze(item):
    return base64.standard_b64encode(zlib.compress(pickle.dumps(item)))


def inflate(squeezed):
    return pickle.loads(zlib.decompress(base64.standard_b64decode(squeezed)))


def phash(x):
    return hashlib.sha256(pickle.dumps(x)).hexdigest()

