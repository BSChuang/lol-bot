import sys
import os
from os.path import dirname
from os.path import join

sys.path.insert(0, join(dirname(__file__), 'nextcloud-API\src'))

from nextcloud import NextCloud