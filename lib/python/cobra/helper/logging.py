import sys
import os
import logging
import requests
import datetime
import socket
class Logger(object):
    '''
    Logging class for Python
    Mid-term intend is to steam logs to the ELK stack
    '''

    def __init__(self, parent_class):

        '''
        PARAMETER:
        - parent_class: class object in which the logger is used
        '''
        if type(parent_class).__name__ != 'str':
            self.classname = type(parent_class).__name__
        else:
            self.classname = parent_class

        self.level = os.environ["LOG_LEVEL"]

    def _get_timestamp_(self):

        return str(datetime.datetime.utcnow().isoformat())

    def _get_base_body_(self):

        log_body = {
            '@timestamp': self._get_timestamp_(),
            'pod': socket.gethostname(),
            'class': self.classname
        }

        return log_body

    def _send_log_(self, log_body):

        response = requests.post('http://elastic:9200/python_logs/_doc',json=log_body)

        if response.status_code >= 300:
            print(f'Could not create log. Status code: {response.status_code}')
            
    def error(self, message, error_object=None):

        log_body = self._get_base_body_()
        log_body['type'] = 'ERROR'
        log_body['message'] = message
        log_body['error'] = str(error_object)

        self._send_log_(log_body)


    def info(self, message):

        if self.level == 'INFO' or self.level == 'DEBUG' or self.level == 'SILLY':

            log_body = self._get_base_body_()
            log_body['type'] = 'INFO'
            log_body['message'] = message
  
            self._send_log_(log_body)

    def debug(self, message):

        if self.level == 'DEBUG' or self.level == 'SILLY':

            log_body = self._get_base_body_()
            log_body['type'] = 'DEBUG'
            log_body['message'] = message
  
            self._send_log_(log_body)

    def silly(self, message):

        if self.level == 'SILLY':

            log_body = self._get_base_body_()
            log_body['type'] = 'SILLY'
            log_body['message'] = message
  
            self._send_log_(log_body)

            
        
