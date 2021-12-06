import os
import cobra_logging
import os.path

class cobra_gdal:
    '''
    Wrapper for GDAL
    '''
    def __init__(self, download_folder='./downloads', host='postgres', database='postgres',user='postgres',password=None):
        if password == None:
            password = os.environ['POSTGRES_PASSWORD']
        self.connection_string = f'host={host} dbname={database} user={user} password={password}'
        self.download_folder = download_folder
        self.l = cobra_logging.Logger(self)
    def __repr__(self):
        return "cobra_gdal"
    def __str__(self):
        return "A wrapper for GDAL"
    def shape2pg(self, path_to_shape, skip_failures=True):
        self.l.debug('shape2pg')     
        if os.path.isfile(path_to_shape) == False:
            self.l.error(f'File {path_to_shape} does not exist')
        command = f'ogr2ogr -f "PostgreSQL" PG:"{self.connection_string}" "{path_to_shape}"'
        if skip_failures:
            command = f'{command} -skip-failures'
        self.l.debug(f'ogr2ogr -f "PostgreSQL" PG:"..." "{path_to_shape}"')
        try:
            os.system(command)
        except Exception as e:
            self.l.error(e)

