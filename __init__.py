#!/usr/bin/env python3


def info():
    import sys, os
    print( "┌── PINES TOOLKIT ──────────────────────────────────────────────────────────")
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


info()
