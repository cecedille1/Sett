#!/usr/bin/env python
# -*- coding: utf-8 -*-


DISABLED_LIBS = ['django']

try:
    import sett
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    import sett
