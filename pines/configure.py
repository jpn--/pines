
import os.path
import json
from .attribute_dict import quickdot, add_to_quickdot

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

_cached_values = None

def cached(filename=None):
    global _cached_values
    if _cached_values is None:
        _cached_values = load(filename)
    return _cached_values

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


def add(tag, val):
    q = load()
    try:
        val = int(val)
    except ValueError:
        try:
            val = float(val)
        except ValueError:
            pass
    q = add_to_quickdot(q,tag,val)
    save(q)

def print_config(args=None):
    import argparse
    parser = argparse.ArgumentParser(prog='pines_config')
    parser.add_argument('--add', nargs=2, action='append')
    space = parser.parse_args()

    q = load()
    if space.add:
        for tag,val in space.add:
            print('setting',tag,'to',val)
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    pass
            q = add_to_quickdot(q,tag,val)
        save(q)
    print(q)




def check_config(checklist, secrets, window_title="PINES CONFIG"):
    global _top_cfg, _secret_cfg
    _top_cfg = load()
    _secret_cfg = quickdot()

    from tkinter import Tk, Entry, Button, mainloop, END, Label, LEFT, BOTTOM

    master = Tk()
    master.wm_title(window_title)

    def makeentry(parent, caption_, width=None, row=None, **options):
        if row is None:
            Label(parent, text=caption_).pack(side=LEFT)
        else:
            Label(parent, text=caption_).grid(row=row,column=0)
        entry = Entry(parent, **options)
        if width:
            entry.config(width=width)
        if row is None:
            entry.pack(side=LEFT)
        else:
            entry.grid(row=row,column=1)
        return entry

    ents = []
    rownum = 0
    for rownum, check in enumerate(checklist):
        ents.append(makeentry(master, check, width=90, row=rownum))
        ents[-1].delete(0, END)
        if _top_cfg[check] is None or (isinstance(_top_cfg[check], quickdot) and len(_top_cfg[check])==0):
            this_str = "<None>"
        else:
            this_str = str(_top_cfg[check])
        ents[-1].insert(0, this_str)

    secret_ents = []
    for rownum, secret in enumerate(secrets, start=rownum+1):
        secret_ents.append(makeentry(master, secret, width=90, row=rownum, show="\u2022"))
        secret_ents[-1].delete(0, END)
        if secret in _top_cfg:
            if _top_cfg[secret] is None or (isinstance(_top_cfg[secret], quickdot) and len(_top_cfg[secret])==0):
                this_str = "<None>"
            else:
                this_str = str(_top_cfg[secret])
        else:
            this_str = ""
        secret_ents[-1].insert(0, this_str)

    ents[0].focus_set()

    def callback_onetime():
        global _top_cfg, _secret_cfg
        for check, ent in zip(checklist, ents):
            this_str = (ent.get())
            if this_str == "<None>":
                _top_cfg[check] = quickdot()
            else:
                try:
                    this_str = int(this_str)
                except ValueError:
                    try:
                        this_str = float(this_str)
                    except ValueError:
                        pass
                _top_cfg[check] = this_str
        for check, ent in zip(secrets, secret_ents):
            this_str = (ent.get())
            if this_str == "<None>":
                _secret_cfg[check] = quickdot()
            else:
                try:
                    this_str = int(this_str)
                except ValueError:
                    try:
                        this_str = float(this_str)
                    except ValueError:
                        pass
                _secret_cfg[check] = this_str
        master.destroy()

    def callback_save():
        callback_onetime()
        save(_top_cfg)

    b = Button(master, text = "OK - One Time", width = 20, command = callback_onetime)
    b.grid(row=rownum+1,column=0, columnspan=2)
    b2 = Button(master, text = "OK - Save to Config File", width = 20, command = callback_save)
    b2.grid(row=rownum+2,column=0, columnspan=2)
    mainloop()
    return _top_cfg + _secret_cfg

