import cobra_logging
import cobra_postgres as pg
import os

class DataModelFabric():
    
    '''
    Class to convert different descriptive formats in a datamodel definition
    '''
    
    def __init__(self):
        
        self.l = cobra_logging.Logger(self)
        self.osmExplorer = None #Placehoder for the Cobra OSM Explorer
        
    def create_from_dict(self, dm_dict:dict):
        
        self.l.debug('create from dict')
        dm = pg.DataModelDefinition(dm_dict['name'])
        for a_table in dm_dict['tables']:
            pg_table = pg.TableDefinition(a_table['tablename'])
            for a_field in a_table['fields']:
                pg_field = pg.FieldDefinition(a_field['name'], a_field['type'])
                pg_table.add_field(pg_field)
            dm.add_table(pg_table)
        return dm