import pymysql.cursors
import json

class MariaSQL(object):

    def __init__(self, host = 'localhost', port = 3306, user = 'root', password = 'password', db = 'mysql', charset = 'utf8mb4'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = db
        self.charset = charset
        self.db = self.connect()

    def connect(self):
        return pymysql.connect(
            host = self.host,
            port = self.port,
            user = self.user,
            password = self.password,
            db = self.dbname,
            charset = self.charset,
            cursorclass = pymysql.cursors.DictCursor,
            autocommit = True)

    def use(self, dbname):
        self.dbname = dbname
        self.db = self.connect()

    def show_tables(self):
        return self.query('show tables')

    def query(self, sql):
        with self.db.cursor() as cursor:
            cursor.execute(sql)
            retval = cursor.fetchall()
        return retval

    def create_db(self, dbname):
        sql = """
            create database if not exists {dbname};
        """
        return self.query(sql.format(dbname = dbname))

    def create_table(self, name, tabledef = None):
        sql = """
            create table if not exists {name} ({columns}) ENGINE=InnoDB CHARACTER SET %s;
        """ % self.charset

        if type(tabledef) is dict:
            columns = list()
            for key in tabledef.items():
                if key[1] is int:
                    columns.append("`{col}` INT".format(col = key[0]))
                elif key[1] is str:
                    columns.append("`{col}` varchar(255)".format(col = key[0]))
                elif key[1] is float:
                    columns.append("`{col}` double".format(col = key[0]))
                elif key[1] is dict:
                    columns.append("`{col}` json".format(col = key[0]))
            sql = sql.format(name = name, columns = ", ".join(columns))
            retval = self.query(sql)
        else:
            retval = self.query(name)
            
        self.db.commit()
        return retval

    def type_handling(self, value):
        if type(value) is dict:
            tmpl = "'{value}'".format(value = json.dumps(value))
        elif type(value) is int or type(value) is float:
            tmpl = "{value}".format(value = value)
        elif type(value) is str:
            tmpl = "'{value}'".format(value = value)
        elif type(value) is bytes:
            tmpl = "'{value}'".format(value = value.decode())
        else:
            tmpl = "NULL"
        return tmpl

    def insert(self, table, data, on_duplicate = False):
        sql = """
            insert into `{table}` ({columns}) values ({values}){ending}
        """
        columns, values, duplicate = list(), list(), list()
        for key, value in data.items():
            columns.append(key)
            values.append(self.type_handling(value))
            duplicate.append("`{key}` = {value}".format(key = key, value = self.type_handling(value)))
        
        columns = "`" + "`,`".join(columns) + "`"
        values = str(values).strip('[]').replace('None', 'NULL')

        if on_duplicate:
            ending = " ON DUPLICATE KEY UPDATE "
            ending += ", ".join(duplicate) 
            ending += ";"
        else:
            ending = ";"

        retval = self.query(sql.format(table = table, columns = columns, values = values, ending = ending).strip())
        self.db.commit()
        return retval

    def insert_on_duplicate(self, table, data):
        return self.insert(table, data, True)
