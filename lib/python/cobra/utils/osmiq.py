import cobra.helper.logging as logging
from cobra.postgres.interface import PgInterface

class OsmIq():

    def __init__(self, database = 'postgres'):

        self.l = logging.Logger(self)
        self.i = PgInterface(database)

    def osm_tag_stats(self, schema, key, value):
    
        response = {}

        types = ['point','line','polygon','roads']
        for a_type in types:

            sql = f"SELECT COUNT(osm_id) FROM {schema}.planet_osm_{a_type} WHERE {key}='{value}'"
            res = self.i.__execute_sql__(sql, fetch='one')
            response[a_type] = res[0]

        return response