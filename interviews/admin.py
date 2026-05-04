# Django only autodiscovers admin.py, not admins.py
from .admins import *  # noqa: F401,F403