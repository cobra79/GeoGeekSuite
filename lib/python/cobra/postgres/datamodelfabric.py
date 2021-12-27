import cobra.helper.logging as logging
import cobra.postgres.interface as pgi
import os

class DataModelFabric():
    
    '''
    Class to convert different descriptive formats in a datamodel definition
    '''
    
    def __init__(self):
        
        self.l = logging.Logger(self)
        self.osmExplorer = None #Placehoder for the Cobra OSM Explorer
        
    def create_from_dict(self, dm_dict:dict):
        
        self.l.debug('create from dict')
        dm = pgi.DataModelDefinition(dm_dict['name'])
        for a_table in dm_dict['tables']:
            pg_table = pgi.TableDefinition(a_table['tablename'])
            for a_field in a_table['fields']:
                pg_field = pgi.FieldDefinition(a_field['name'], a_field['type'])
                pg_table.add_field(pg_field)
            dm.add_table(pg_table)
        return dm