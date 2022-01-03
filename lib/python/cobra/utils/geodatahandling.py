import cobra.helper.logging as logging
import cobra.postgres.interface as pgi
import geopandas as gpd
import pandas as pd


class Geodatamanager():

    def __init__(self):

        self.l = logging.Logger(self)
        self.pg = pgi.PgInterface()

    def get_schemas(self):
 
         self.l.debug('get_schemas')
 
         schemas = self.pg.__execute_sql__('SELECT schema_name FROM information_schema.schemata',fetch='all')
         schemas = schemas = [x[0] for x in schemas]
 
         schemas_to_remove = ['pg_toast','pg_catalog','information_schema','topology','tiger','tiger_data','jobs','public']
 
         for a_schema_to_remove in schemas_to_remove:
             
             schemas.remove(a_schema_to_remove)
 
         return schemas
 
    def get_tables(self):

        self.l.debug('get_tables')
        schemas = self.get_schemas()
        table_list = []
        for a_schema in schemas:
    
            sql = f"select table_name from information_schema.tables WHERE table_schema = '{a_schema}'"
            result = self.pg.__execute_sql__(sql,fetch='all')
            result = [x[0] for x in result]
            for a_table in result:
                estimate = self.estimate_table_size(a_schema, a_table)
                geom_columns = self.get_geometry_columns(a_schema, a_table)
                table_list.append([a_schema, a_table, estimate, geom_columns])

        return pd.DataFrame(table_list, columns=['schema','table','estimate rows', 'geom columns'])

    def estimate_table_size(self, schema, table):

        self.l.debug('estimate table size')
        sql = f"SELECT reltuples::bigint AS estimate FROM pg_class WHERE oid = '{schema}.{table}'::regclass;"
        res = self.__execute_sql__(sql, fetch='one')
        return res[0]

    def get_geometry_columns(self, schema, table):

        self.l.debug('get_geomentry_columns')

        sql = f"SELECT column_name  FROM information_schema.columns WHERE table_schema='{schema}' AND table_name='{table}' AND data_type='USER-DEFINED'"
        res = self.pg.__execute_sql__(sql,fetch='all')
        col_list = [x[0] for x in res]
        return ",".join(col_list)

    def simple_sql_for_geopandas(self, table_details):

        self.l.debug('simple_sql_for_geopandas')
    
        schema = table_details.schema
        table = table_details.table
        geom_column = table_details['geom columns'].split(',')[0]
    
        sql = f"SELECT {geom_column} as geom FROM {schema}.{table}"

        return sql

    def simple_plot(self, table_details):

        self.l.debug('simple_plot')
        sql = self.simple_sql_for_geopandas(table_details)
        with self.pg.get_connection() as conn:
            geodata = gpd.GeoDataFrame.from_postgis(sql, conn)
        geodata.plot()