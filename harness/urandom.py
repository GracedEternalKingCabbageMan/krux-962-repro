"""MicroPython urandom stub for desktop testing."""
import random as _r
import os

def seed(*a, **k):
    pass

def choice(seq):
    return _r.choice(seq)

def getrandbits(n):
    return _r.getrandbits(n)
