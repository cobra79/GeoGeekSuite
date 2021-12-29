import cobra.helper.logging as logging
import cobra.postgres.interface as pgi
import geopandas as gpd


class Geodatamanager():

    def __init__(self):

        self.l = logging.Logger(self)
        self.pg = pgi.PgInterface()

    def get_tables(self):

        self.l.debug('get_tables')

        #TODO: Move relveant methods to this class
        return self.pg.get_tables()

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