import sys
import os

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
            
    def error(self, message, error_object=None):

        print(f'ERROR [{self.classname}] {message}')

    def info(self, message):

        if self.level == 'INFO' or self.level == 'DEBUG':
            print(f'INFO [{self.classname}] {message}')

    def debug(self, message):
        if self.level == 'DEBUG':
            print(f'DEBUG [{self.classname}] {message}')

