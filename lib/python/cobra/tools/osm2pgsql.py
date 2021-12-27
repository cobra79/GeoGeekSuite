import cobra.helper.logging as logging
import time
import subprocess
import os


class Osm2PgSql():

    '''
    wrapper for osm2pgsql
    '''

    def __init__(self, style="default.style", run_in_loop = False):

        self.l = logging.Logger(self)
        self.l.debug("New osm2pgsql")
        self.style = style
        self.busy = False

        if run_in_loop:
            self._mainloop_()

    def __repr__(self):

        return "osm2pgsql"

    def __str__(self):
        
        return "A wrapper for osm2pgsql"

    def _mainloop_(self):

        while True:
            self.pick_a_job_when_not_busy()
            time.sleep(10)

    def pick_a_job_when_not_busy(self):

        self.l.debug('pick_a_job_when_not_busy')
        if self.busy == False:
            self.pick_a_job()


    def pick_a_job(self):

        self.l.debug('pick_a_job')

        # To be implemented

    def execute_osm2pgsql(self, path_to_pbf, cache=None):

        #TODO: Check if file exists and cache is numeric

        self.l.debug("execute_osm2pgsql")

        try:
            
            #args =['osm2pgsql','-c','-d', self.connection_string, '-S', f'{self.style}', path_to_pbf]
            args =['osm2pgsql','-c','-S', f'{self.style}', path_to_pbf]
            self.l.debug(self.connection_string)
            if cache != None:
                args.append(f'--cache {str(cache)}')

            return_value = subprocess.run(args)
        
        except Exception as e:
            #TODO: self.update_job_status(job_id, 'Failed')
            self.l.error(e)
        finally:
            self.busy = False
