#!/usr/bin/env python3
"""Compatibility entry point for the maintained, network-free PairAtlas auditor."""
from pairatlas.audit import *  # noqa: F401,F403
from pairatlas.audit import main

if __name__ == '__main__':
    raise SystemExit(main())
