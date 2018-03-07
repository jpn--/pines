#!/usr/bin/env python3

__version__ = '2.81'

import sys, os

def info():
    print( f"┌── PINES TOOLKIT {__version__} " + "─"*(57-len(__version__)) )
    v = '\n│'.join(sys.version.split('\n'))
    print(f"│Python {v}")
    print(f"│EXE ─ {sys.executable}")
    print(f"│CWD ─ {os.getcwd()}", )
    for p in sys.path[:1]:
        print(f"│PTH ┬ {p}")
    for p in sys.path[1:-1]:
        print(f"│    ├ {p}")
    for p in sys.path[-1:]:
        print(f"│    └ {p}")
    print("└───────────────────────────────────────────────────────────────────────────")


class Info:

    def __init__(self, appname='Pines Toolkit', extra=True, version=None):
        self.appname = appname
        self.extra = extra
        self.version = version or __version__


    def __repr__(self):
        r = (f"┌── {self.appname.upper()} {self.version} " + "─" * (57 - len(self.version)))
        v = '\n│'.join(sys.version.split('\n'))
        r += (f"\n│Python {v}")
        r += (f"\n│EXE ─ {sys.executable}")
        r += (f"\n│CWD ─ {os.getcwd()}" )
        for p in sys.path[:1]:
            r += (f"\n│PTH ┬ {p}")
        for p in sys.path[1:-1]:
            r += (f"\n│    ├ {p}")
        for p in sys.path[-1:]:
            r += (f"\n│    └ {p}")
        r += ("\n└───────────────────────────────────────────────────────────────────────────")
        return r

    def _repr_html_(self):
        from .xhtml import Elem
        xsign = Elem("div", {'class': 'larch_head_tag'})
        from .img import favicon
        p = Elem('p', {'style': 'float:left;margin-top:6px'})
        p << Elem('img', {
            'width': "32",
            'height': "32",
            'src': "data:image/png;base64,{}".format(favicon),
            'style': 'float:left;position:relative;top:-3px;padding-right:0.2em;'
        }, tail=f" {self.appname} ")
        p << Elem('span', {'class': 'larch_head_tag_ver'}, text=self.version)
        xsign << p
        from .img import camsyslogo_element
        xsign << camsyslogo_element
        if 'larch4' in sys.modules:
            from .img import georgiatechlogo_element
            xsign << georgiatechlogo_element

        if self.extra:
            v = '\n│'.join(sys.version.split('\n'))
            xsign << Elem('br')
            xinfo = Elem('div', {'class': 'larch_head_tag_more', 'style':'margin-top:10px; padding:7px'}, text=f'Python {v}')
            xsign << xinfo
            xinfo << Elem('br', tail=f"EXE - {sys.executable}")
            xinfo << Elem('br', tail=f"CWD - {os.getcwd()}")
            xinfo << Elem('br', tail=f"PATH - ")
            ul = Elem('ul', {'style': 'margin-top:0; margin-bottom:0;'})
            xinfo << ul
            for p in sys.path:
                ul << Elem('li', text=p)
        return xsign.tostring()







def ipython_status(magic_matplotlib=True):
    message_set = set()
    try:
        cfg = get_ipython().config
    except:
        message_set.add('Not IPython')
    else:
        import IPython
        message_set.add('IPython')
        # Caution: cfg is an IPython.config.loader.Config
        if cfg['IPKernelApp']:
            message_set.add('IPython QtConsole')
            try:
                if cfg['IPKernelApp']['pylab'] == 'inline':
                    message_set.add('pylab inline')
                else:
                    message_set.add('pylab loaded but not inline')
            except:
                message_set.add('pylab not loaded')
        elif cfg['TerminalIPythonApp']:
            try:
                if cfg['TerminalIPythonApp']['pylab'] == 'inline':
                    message_set.add('pylab inline')
                else:
                    message_set.add('pylab loaded but not inline')
            except:
                message_set.add('pylab not loaded')
    return message_set



_i = Info()

if 'IPython' in ipython_status():
    from IPython.display import display
    try:
        if 'larch' not in sys.modules and 'larch4' not in sys.modules:
            from .styles import stylesheet
            stylesheet()
            display(_i)
    except:
        if 'larch' not in sys.modules and 'larch4' not in sys.modules:
            print(repr(_i))
        jupyter_active = False
    else:
        jupyter_active = True
else:
    jupyter_active = False
    if 'larch' not in sys.modules and 'larch4' not in sys.modules:
        print(repr(_i))

## most common items here

from .attribute_dict import fdict, quickdot
from .codex import phash
