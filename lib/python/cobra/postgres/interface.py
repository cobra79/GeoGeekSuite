import psycopg2
import os
import cobra.helper.logging as logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
# import geopandas as gpd

class FieldDefinition():
    '''
    Class to describe a postgres table field
    '''
    def __init__(self, field_name, field_type, primary_key = False):
        self.l = logging.Logger(self)
        self.l.debug(f'New FieldDefinition for {field_name}')
        self.name = field_name
        self.type = field_type
        self.primary_key = primary_key
        
    def __repr__(self):
        return f'FieldDefinition <name: {self.name}, type: {self.type}>'
    
    def __str__(self):
        return f'FieldDefinition -name: {self.name}, type: {self.type}'


class TableDefinition():
    '''
    Class to describe a postgres table
    '''
    def __init__(self, table_name):
        self.l = logging.Logger(self)
        self.l.debug(f'New TableDefinition for {table_name}')
        self.name = table_name
        self.field_definitions = {}
        
    def add_field(self, field_definition : FieldDefinition):
        
        self.field_definitions[field_definition.name] = field_definition

class DataModelDefinition():
    '''
    Class to describe a collection of tables
    '''
    def  __init__(self, name, schema=None):
        self.l = logging.Logger(self)
        self.l.debug(f'New DataModelDefinition ({name})')
        self.name = name
        if schema == None:
            self.l.debug(f'set DataModelDefinition schema to {name} as no schema name was specified')
            self.schema = name
        else:
            self.l.debug(f'set DataModelDefinition schema to {schema}')
            self.schema = schema
        self.table_definitions = {}

    def __str__(self):

        output = f'Name: {self.name}' + '\n' + f'Schema: {self.schema}' + '\n'
        table_details = ''
        for a_table_key in self.table_definitions:
            table_details = table_details + f' - Table: {self.table_definitions[a_table_key].name} \n'
            for a_field_key in self.table_definitions[a_table_key].field_definitions:
                a_field = self.table_definitions[a_table_key].field_definitions[a_field_key]
                table_details = table_details + f'    - Field: {a_field.name} [{a_field.type}]\n'
        output = output + table_details

        return output
        
    def add_table(self, table_definition : TableDefinition):
        self.l.debug('add_table')
        self.table_definitions[table_definition.name]  = table_definition

class PgInterface():
    '''
    Base class to interact with the Postgres Database
    '''
    def __init__(self, database='postgres', schema='public'):
        self.l = logging.Logger(self)
        self.database = database
        self.password = os.environ['PGPASSWORD']
        self.current_schema = schema
        if database != 'postgres':
            self.create_db_when_required(database)
        self.conn_string = f"host='postgres' dbname='{self.database}' user='postgres' password='{self.password}'"
        self.check_extensions()

    def create_db_when_required(self, database):

        self.conn_string = f"host='postgres' dbname='postgres' user='postgres' password='{self.password}'"
        if database in self.get_database_list():
            return
        else:
            self.create_database(database)

    def get_connection(self):

        self.l.silly('Provide PG connection')
        return psycopg2.connect(self.conn_string)

    def check_extensions(self):
        
        self.l.debug('check_extensions')
        extensions_to_install = ['postgis','pgrouting']

        for an_ext in extensions_to_install:

            sql = f'CREATE EXTENSION IF NOT EXISTS {an_ext}'
            self.__execute_sql__(sql)


    def switch_schema(self, schema_name):

        self.l.debug(f'Switch schema to {schema_name}')
        #TODO: Check if Schema exists
        self.current_schema = schema_name
        #sql = f"SET search_path TO {schema_name}"
        #self.__execute_sql__(sql)

    def __execute_sql__(self, sql, fetch='none'):
        '''
        Execute SQL
        
        Params:
        - sql: SQL command to execute
        - fetch:
          none = nothing returned
          one = one value returned
        
        '''
        self.l.debug(f'execute SQL: {sql}')
        with psycopg2.connect(self.conn_string) as conn:
            conn.autocommit = True
            with conn.cursor() as curs:
                try:
                    curs.execute(sql)
                except Exception as error:
                    self.l.error(error)
                if fetch=='one':
                    result = curs.fetchone()
                elif fetch == 'all':
                    result = curs.fetchall()
                elif fetch == 'none':
                    result = None
                else:
                    self.l.error(f'fetch value {fetch} is unknown')
        return result
    
    def db_version(self):
        
        sql = 'SELECT version()'
        return self.__execute_sql__(sql, fetch='one')
    
    def create_database(self, database_name):

        self.l.info(f'create database {database_name}')
        res = self.__execute_sql__(f"SELECT datname FROM pg_catalog.pg_database WHERE datname='{database_name}'",fetch="one")
        if res == None:

            con = self.get_connection()
            con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = con.cursor()
            try:
                cur.execute(f"CREATE DATABASE {database_name}")
            finally:
                cur.close()
                con.close()

        else:

            self.l.error(f'Database {database_name} already exists')

    def drop_database(self, database_name):

        self.l.info(f'drop database {database_name}')
        res = self.__execute_sql__(f"SELECT datname FROM pg_catalog.pg_database WHERE datname='{database_name}'",fetch="one")
        if res == None:

            self.l.error(f'Database {database_name} can not be dropped as it does not exist')

        else:

            con = self.get_connection()
            con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = con.cursor()
            try:
                cur.execute(f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname='{database_name}' AND pid<>pg_backend_pid();")
                cur.execute(f"DROP DATABASE {database_name} WITH (FORCE);")
            finally:
                cur.close()
                con.close()
    
    def get_database_list(self):

        self.l.debug('get_database_list')

        res = self.__execute_sql__('SELECT datname FROM pg_catalog.pg_database', fetch='all')
        return [db[0] for db in res]

    def create_schema(self, schema_name, switch_to_schema = False):
        
        self.l.info(f'create schema {schema_name}')
        sql = f'CREATE SCHEMA IF NOT EXISTS {schema_name.lower()}'
        result = self.__execute_sql__(sql)
        if switch_to_schema:
            self.switch_schema(schema_name)

    def drop_schema(self, schema_name):

        self.l.info(f'drop schema {schema_name}')

        sql = f'DROP SCHEMA IF EXISTS {schema_name} CASCADE'
        self.__execute_sql__(sql)

    def get_schema_list(self):

        self.l.debug('get_schema_list')

        res = self.__execute_sql__('SELECT schema_name FROM information_schema.schemata', fetch='all')
        return [schema[0] for schema in res]

    def create_table(self, table_definition:TableDefinition, schema=None, if_not_exits=True):
        
        self.l.info(f'create table {table_definition.name}')
        if schema == None:
            schema = self.current_schema
        field_string = ''
        
        for a_field_key in table_definition.field_definitions:
        
            a_field = table_definition.field_definitions[a_field_key]

            if a_field.primary_key == True:
                field_string += f'{a_field.name} {a_field.type} PRIMARY KEY, '
            else:
                field_string += f'{a_field.name} {a_field.type}, '

            
        field_string = field_string[:-2]
        
        if if_not_exits:
            sql = f'CREATE TABLE IF NOT EXISTS {schema}.{table_definition.name} ({field_string});'
        else:
            sql = f'CREATE TABLE {schema}.{table_definition.name} ({field_string});'
        self.l.debug(sql)
        self.__execute_sql__(sql, fetch='none')
                
    def drop_table(self, table_definition:TableDefinition):
        
        self.l.info(f'drop table {table_definition.name}')
        
        sql = f'DROP TABLE IF EXISTS {table_definition.name}'
        self.l.debug(sql)
        self.__execute_sql__(sql, fetch='none')

    def get_table_list(self, schema_name):

        self.l.debug('get_table_list')
        res = self.__execute_sql__(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema_name}'", fetch='one')
        return [table for table in res]

    def insert_into_table(self, table, key_list, value_list, schema=None):

        self.l.info('insert into table {schema}.{table} ({})')

        value_list = self._value_list_shape_correction_(value_list)

        if schema == None:

            schema = self.current_schema

        key_string = ','.join(key_list)
  
        value_string = ''

        for a_value_set in value_list:
            new_val_set = ''
            for a_val in a_value_set:
                a_val = a_val.replace("'", "''")
                new_val_set = new_val_set + "'" +a_val +"'" + ','
            new_val_set = new_val_set[:-1]
            new_val_set = f'({new_val_set})'
            value_string = value_string + ',' + new_val_set
            
        sql = f'INSERT INTO {schema}.{table} ({key_string}) VALUES {value_string[1:]};'

        self.l.debug(sql)

        self.__execute_sql__(sql, fetch='none')

    def _value_list_shape_correction_(self, value_list):

        if len(value_list) > 0:

            if type(value_list[0]) == list:

                return value_list
            
            else:

                return [value_list]
        
        else:

            return [[]]

    def table_row_count(self, table, schema=None):

        if schema == None:

            schema = self.current_schema

        res = self.__execute_sql__(f'SELECT COUNT(*) FROM {schema}.{table}', fetch='one')
        return res[0]

#    def get_gdf(self, sql):
#
#        self.l.debug('get_gdf')
#        conn = self.get_connection()
#        res = gpd.GeoDataFrame.from_postgis(sql, conn)
#        conn.close()
#        return res


class DataModelManager():
    
    '''
    Class to manage datamodels
    can be used to apply a definition and create tables
    or remove tables from postgres
    '''
    
    def __init__(self, database=None):
        
        self.l = logging.Logger(self)
        self.l.info('New DataModelManager')
        self.data_models = {}
        if database == None:
            self.db_interface = PgInterface()
        else:
            self.db_interface = PgInterface(database)
     
    def add_datamodel(self, datamodel:DataModelDefinition):
        
        self.l.info(f'add datamodel {datamodel.name}')
        
        self.data_models[datamodel.name] = datamodel
        
    def get_datamodel_names(self):
        
        return self.data_models.keys()
        
    def apply_datamodel(self, name):
        '''
        Create all tables defined in the datamodel
        '''
        self.l.info(f'apply datamodel {name}')
        
        dm = self.data_models[name]

        self.l.debug(f'schema: {dm.schema}')
        self.db_interface.create_schema(dm.schema)

        for a_table_key in dm.table_definitions:
            a_table = dm.table_definitions[a_table_key]
            self.db_interface.create_table(a_table, schema=dm.schema)
            
            #print(dm.table_definitions[a_table].name)
            #for a_field_key in dm.table_definitions[a_table].field_definitions:
            #    a_field = dm.table_definitions[a_table].field_definitions[a_field_key]
            #    print(f' - {a_field.name}  {a_field.type}')
            
    def remove_datamodel(self, name):
        '''
        Removes all tables from the database that are defined in the datamodel
        '''
        self.l.info(f'Remove datamodel {name}')
        dm = self.data_models[name]
        self.db_interface.drop_schema(dm.schema)

class DataModelFabric():
    
    '''
    Class to convert different descriptive formats in a datamodel definition
    '''
    
    def __init__(self):
        
        self.l = logging.Logger(self)
        
    def create_from_dict(self, dm_dict:dict):
        
        self.l.debug('create from dict')
        dm = DataModelDefinition(dm_dict['name'])
        for a_table in dm_dict['tables']:
            pg_table = TableDefinition(a_table['tablename'])
            for a_field in a_table['fields']:
                
                if 'primary_key' in a_field.keys() and a_field['primary_key'] == True:
                    pg_field = FieldDefinition(a_field['name'], a_field['type'], primary_key=True)
                else:
                    pg_field = FieldDefinition(a_field['name'], a_field['type'])
                
                pg_table.add_field(pg_field)
            dm.add_table(pg_table)
        return dm

class DataLoader():
    
    '''
    Class to load content into an existing table
    '''
    def __init__(self, schema, tablename):
        
        self.schema = schema
        self.tablename = tablename
        self.db_interface = PgInterface()
            
    def load_from_dict(self, data_dict):
        
        self.db_interface.insert_into_table(data_dict['schema'],data_dict['table'],data_dict['keys'],data_dict['values'])






