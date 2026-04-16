import os

import pymysql

# Only install the MySQLdb shim when MySQL is enabled. SQLite does not need PyMySQL.
if os.getenv("USE_MYSQL", "0").lower() in {"1", "true", "yes"}:
    # Django's MySQL backend validates the mysqlclient version exposed by the MySQLdb shim.
    # PyMySQL reports a lower version number even though it is compatible for local development.
    pymysql.version_info = (2, 2, 1, "final", 0)
    pymysql.install_as_MySQLdb()
