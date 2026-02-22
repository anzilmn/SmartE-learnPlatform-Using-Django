import pymysql

# 1. Start the PyMySQL engine
pymysql.version_info = (2, 2, 1, 'final', 0)
pymysql.install_as_MySQLdb()

# 2. Import Django base AFTER PyMySQL is ready
from django.db.backends.mysql import base
from django.db.backends.mysql.features import DatabaseFeatures

# 3. Bypass the version check (for 10.4 compatibility)
base.DatabaseWrapper.check_database_version_supported = lambda self: None

# 4. Disable the 'RETURNING' feature (Fixes the syntax error)
DatabaseFeatures.has_returning_fields = property(lambda self: False)
DatabaseFeatures.can_return_columns_from_insert = property(lambda self: False)