"""
You can add categories as much as you can
"""

from enum import IntEnum


class ExceptionCategory(IntEnum):
    # generic
    GENERIC = 1

    # exceptions related to the endpoints
    ENTITY = 100

    # exceptions related to the validation
    VALIDATION = 101

    # users
    USERS = 200

    # Clients
    CLINTS = 300

    # Services
    QGIS_SERVICE = 400

    # DB
    DB = 500

    # Storage
    STORAGE = 600
