# This is part of the wnframework project at google.
# http://code.google.com/p/wnframework/
#
#


class DbAdministrator(object):
    """
            Basically, a wrapper for oft-used mysql commands. like show tables,databases, variables etc...
            #TODO:
            0.  Simplify / create settings for the restore database source folder
            0a. Merge extract_sql(from webnotes_server_tools).
            1. Setter and getter for different mysql variables.
            2. Setter and getter for mysql variables at global level??
    """

    def __init__(self, conn=None, **kwargs):
        """
        Pass in a dict of the format
            {'db_host':hostname,
                'db_type':'mysql/postgres',
                'db_root_user':username,
                'db_password':password}
        """
        if conn:
            self.conn = conn
        else:
            if not kwargs:
                self.db_host = raw_input("DB Hostname/IP?")
                self.db_type = raw_input("DB type(mysql/postgres)?")
                self.db_root_user = raw_input("DB root user?")
                self.db_password = raw_input("DB password?")
            else:
                self.db_host = kwargs.get('db_host')
                self.db_type = db_type
                self.db_root_user = kwargs.get('db_root_user')
                self.db_password = kwargs.get('db_password')
            if self.db_type == 'mysql':
                import MySQLdb as mq
                self.root_conn = mq.Connect(host=self.db_host,
                                            user=self.db_root_user,
                                            password=self.db_password)
            elif self.db_type == 'postgres':
                import psycopg2 as pg
                self.root_conn = pg.connect("host = %s port = 5432 \
                                             user=%s password=%s" % (self.db_host,
                                                                     self.db_root_user,
                                                                     self.db_password))
            else:
                assert None, 'Unknown db_type'
        self.cursor = self.root_conn.cursor()

    def lock_table(self, table, lock_type):
        return self.cursor.execute("LOCK TABLES %S %S" % (table, lock_type))

    def unlock_tables(self):
        """Just stupid unlock tables"""
        return self.cursor.execute("UNLOCK TABLES;")

    def get_variables(self, regex):
        """
        Get variables that match the passed pattern regex
        """
        print("SHOW VARIABLES LIKE '{0}{1}{2}';".format('%', regex, '%'))
        self.cursor.execute(("SHOW VARIABLES LIKE '{0}{1}{2}'".format('%', regex, '%')))
        return list(self.cursor.fetchall())

    def drop_all_databases(self):
        self.db_list = self.get_database_list()
        for db in self.db_list:
            self.drop_database(db)

    def use(self, db):
        """Use the given db for all further operations."""
        if self.db_type == 'mysql':
            self.cursor.execute("USE %s" % db)
            self.cursor.fetchall()
        elif self.db_type == 'postgres':
            self.cursor.execute("\c %s" % db)
            self.cursor.fetchall()
        else:
            assert self.db_type, "Unknown db type"

    def get_table_schema(self, table):
        """Just returns the output of Desc tables."""
        self.cursor.execute("DESC %s" % table)
        return list(self.cursor.fetchall())

    def get_tables_list(self, target):
        """ """
        try:
            self.use(target)
            if self.db_type == 'mysql':
                self.cursor.execute("SHOW TABLES")
            elif self.db_type == 'postgres':
                self.cursor.execute('\d')
            else:
                assert None, "Don't know which db_type this is"
            res = self.cursor.fetchall()
            if res:
                table_list = []
            for table in res:
                table_list.append(table[0])
            return table_list
        except Exception as e:
            raise e

    def create_user(self, user, password):
        # Create user if it doesn't exist.
        try:
            print("Creating user %s" % user[:16])
            if self.db_type == 'mysql':
                if password:
                    self.cursor.execute("CREATE USER '%s'@'localhost' IDENTIFIED BY '%s';" % (user[:16], password))
                else:
                    self.cursor.execute("CREATE USER '%s'@'localhost';" % user[:16])
            elif self.db_type == 'postgres':
                if password:
                    self.cursor.execute("CREATE USER %s WITH PASSWORD '%s';" % (user, password))
                else:
                    self.cursor.execute("CREATE USER %s;" % user)
        except Exception as e:
            raise e

    def delete_user(self, target):
        # delete user if exists
        try:
            print("Dropping user ", target)
            if self.db_type == 'mysql':
                self.cursor.execute("DROP USER '%s'@'localhost';" % target)
            elif self.db_type == 'postgres':
                self.cursor.execute("DROP USER %s;" % target)
        except Exception as e:
            if e.args[0] == 1396:
                pass
            else:
                raise e

    def create_database(self, target):
        try:
            print("Creating Database", target)
            if self.db_type == 'mysql':
                self.cursor.execute("CREATE DATABASE IF NOT EXISTS `%s` ;" % target)
            elif self.db_type == 'postgres':
                self.cursor.execute("CREATE DATABASE %s ;" % target)
        except Exception as e:
            raise e

    def drop_database(self, target):
        try:
            print("Dropping Database:", target)
            if self.db_type == 'mysql':
                self.cursor.execute("DROP DATABASE IF EXISTS `%s`;" % target)
            elif self.db_type == 'postgres':
                self.cursor.execute("DROP DATABASE %s ;" % target)
        except Exception as e:
            raise e

    def grant_all_privileges(self, target, user):
        try:
            print("Granting all privileges on %s to %s@localhost" % (target, user))
            if self.db_type == 'mysql':
                self.cursor.execute("GRANT ALL PRIVILEGES ON \
                                    `%s` . * TO '%s'@'localhost';" % (target, user))
            elif self.db_type == 'postgres':
                self.cursor.execute("GRANT ALL ON DATABASE %s TO %s;" % (target, user))
        except Exception as e:
            raise e

    def grant_select_privilges(self, db, table, user):
        try:
            if table:
                print("Granting Read privileges on %s.%s to %s@localhost" % (db, table, user))
                self.cursor.execute("GRANT SELECT ON %s.%s to '%s'@'localhost';" % (db, table, user))
            else:
                print("Granting Read privileges on %s.* to %s@localhost" % (db, user))
                self.cursor.execute("GRANT SELECT ON %s.* to '%s'@'localhost';" % (db, user))
        except Exception as e:
            raise e

    def grant_privileges(self, privilege, db, table, user, host):
        try:
            print("Granting %s privilege on %s.%s to %s@%s" % (privilege,
                                                               db, table,
                                                               user, host))
            if self.db_type == 'mysql':
                self.cursor.execute("GRANT %s ON %s.%s to '%s'@'%s';" % (privilege,
                                                                         db, table,
                                                                         user, host))
        except Exception as e:
            raise e

    def flush_privileges(self):
        try:
            print("Flushing privileges")
            self.cursor.execute("FLUSH PRIVILEGES")
        except Exception as e:
            raise e

    def get_database_list(self):
        try:
            db_list = []
            ret_db_list = self.cursor.execute("SHOW DATABASES")
            for db in ret_db_list:
                if db[0] not in ['information_schema', 'mysql', 'test', 'accounts']:
                    db_list.append(db[0])
            return db_list
        except Exception as e:
            raise e

    def restore_database(self,target,source,root_password):
        try:
            ret = os.system("mysql -u root -p%s %s < %s"%(root_password, target, source))
            print("Restore DB Return status:", ret)
        except Exception as e:
            raise e

    def create_table(self,table_query):
        try:
            self.cursor.execute(table_query)
        except Exception as e:
            raise e

    def drop_table(self,table_name):
        try:
            print("Dropping table %s" % (table_name))
            self.cursor.execute("DROP TABLE IF EXISTS %s "%(table_name))
        except Exception as e:
            raise e

    def set_transaction_isolation_level(self,scope='SESSION',level='READ COMMITTED'):
        #Sets the transaction isolation level. scope = global/session
        try:
            self.cursor.execute("SET %s TRANSACTION ISOLATION LEVEL %s"%(scope,level))
            print("Set transaction level ",scope, level)
        except Exception as e:
            raise e


