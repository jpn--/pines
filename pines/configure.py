
import os.path
import json
from .attribute_dict import quickdot

def add_directory(filepath):
    """
    Add '~/.pines' in a platform independent way.
    """
    if os.path.isabs(filepath):
        return filepath
    return os.path.join(os.path.expanduser('~'), '.pines', filepath)


def load(filename=None):
    """
    Load configuration from a JSON file.
    If filename is None, ~/.pines/configure.json will be loaded.
    If filename is not an absolute path, it will be prefixed with ~/.pines/
    Returns loaded config as a dictionary on success and {} on failure.
    """
    filename = add_directory(filename or 'configure.json')
    try:
        with open(filename, "r") as f:
            return quickdot(json.load(f))
    except IOError:
        pass
    return quickdot()


def save(config, filename=None):
    """
    Save configuration to a JSON file.
    If filename is not an absolute path, it will be prefixed with ~/.pines/
    """
    filename = add_directory(filename or 'configure.json')
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory, 0o700)
    with open(filename, "w") as f:
        json.dump(config, f, indent=2, sort_keys=True)
