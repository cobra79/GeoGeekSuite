import psycopg2
import os
import cobra.helper.logging as logging

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
    def __init__(self, database='postgres'):
        self.l = logging.Logger(self)
        self.database = database
        self.password = os.environ['POSTGRES_PASSWORD']
        self.conn_string = f"host='postgres' dbname='{self.database}' user='postgres' password='{self.password}'"
    
    def get_connection(self):

        self.l.debug('Provide PG connection')
        return psycopg2.connect(self.conn_string)

    def switch_schema(self, schema_name):

        self.l.debug(f'Switch schema to {schema_name}')
        sql = f"SET search_path TO {schema_name}"
        self.__execute_sql__(sql)

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
                elif fetch == 'none':
                    result = None
                else:
                    self.l.error(f'fetch value {fetch} is unknown')
        return result
    
    def db_version(self):
        
        sql = 'SELECT version()'
        return self.__execute_sql__(sql, fetch='one')
    
    def create_schema(self, schema_name, switch_to_schema = False):
        
        self.l.info(f'create schema {schema_name}')
        sql = f'CREATE SCHEMA IF NOT EXISTS {schema_name.lower()}'
        result = self.__execute_sql__(sql)
        if switch_to_schema:
            self.switch_schema(schema_name)

    def switch_schema(self, schema_name):

        self.l.debug(f'Switch schema to {schema_name}')
        sql = f"SET search_path TO {schema_name}"
        self.__execute_sql__(sql)
        
    def drop_schema(self, schema_name):

        self.l.info(f'drop schema {schema_name}')

        sql = f'DROP SCHEMA IF EXISTS {schema_name} CASCADE'
        self.__execute_sql__(sql)

    def create_table(self, table_definition:TableDefinition, schema=None, if_not_exits=True):
        
        self.l.info(f'create table {table_definition.name}')
        if schema == None:
            schema = 'public'
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


    def insert_into_table(self, schema, table, key_list, value_list):

        self.l.info('insert into table {schema}.{table} ({})')

        key_string = ','.join(key_list)

        
        
        value_string = ''

        for a_value_set in value_list:
            new_val_set = ''
            for a_val in a_value_set:
                new_val_set = new_val_set + "'" +a_val +"'" + ','
            new_val_set = new_val_set[:-1]
            new_val_set = f'({new_val_set})'
            value_string = value_string + ',' + new_val_set
            
        sql = f'INSERT INTO {schema}.{table} ({key_string}) VALUES {value_string[1:]};'

        self.l.debug(sql)

        self.__execute_sql__(sql, fetch='none')

class DataModelManager():
    
    '''
    Class to manage datamodels
    can be used to apply a definition and create tables
    or remove tables from postgres
    '''
    
    def __init__(self):
        
        self.l = logging.Logger(self)
        self.l.info('New DataModelManager')
        self.data_models = {}
        self.db_interface = PgInterface()
     
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

        

        #for a_table_key in dm.table_definitions:
         #   a_table = dm.table_definitions[a_table_key]
          #  self.db_interface.drop_table(a_table)

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



class DataModelManager():
    
    '''
    Class to manage datamodels
    can be used to apply a definition and create tables
    or remove tables from postgres
    '''
    
    def __init__(self):
        
        self.l = logging.Logger(self)
        self.l.info('New DataModelManager')
        self.data_models = {}
        self.db_interface = PgInterface()
     
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








