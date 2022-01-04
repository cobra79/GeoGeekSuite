import cobra.helper.logging as logging
import os
from urllib import request
import zipfile
import pandas as pd

class Filemanager():

    '''
    Class to start downloads and manage GIS files available on the system
    '''
    def __init__(self):

        self.l = logging.Logger(self)

    def download_plain_file(self, url_to_download, dataset_name):

        '''
        Download a geospataial dataset that consists of a single file.
        '''
        self.l.debug(f'download_plain_file {dataset_name} from {url_to_download}')
        
        filename=url_to_download.split('/')[-1]
        location_exist = os.path.exists(f'/download/{dataset_name}')

        if not location_exist:
            os.makedirs(f'/download/{dataset_name}')
            
        request.urlretrieve(url_to_download, f'/download/{dataset_name}/{filename}')

    
    def download_shape_archive(self, url_to_download, dataset_name):

        '''
        Download and unpack an archive with several shape files.
        E.g. as provided by Geofabric

        dataset_name: Set a name for the dataset
        '''

        self.l.debug(f'download_shape_archive {dataset_name} from {url_to_download}')
        
        filename=url_to_download.split('/')[-1]
        location_exist = os.path.exists(f'/download/{dataset_name}')

        if not location_exist:
            os.makedirs(f'/download/{dataset_name}')
        request.urlretrieve(url_to_download, f'/download/{dataset_name}/{filename}')
        
        with zipfile.ZipFile(f'/download/{dataset_name}/{filename}', 'r') as zip_ref:
            zip_ref.extractall(f'/download/{dataset_name}')
            
    def get_data(self, datatype=None):
    
        '''
        Get a table of datasets present on the system
        '''

        self.l.debug('get_data')

        data_list = []
        for name, folder in self.get_datasets():
            files = self.get_files(name)
            for a_file in files:
                data_type = self.get_type(a_file)
                if data_type == 'Shape':
                    geom_size = self.get_size(f'{folder}/{a_file}')
                    attribute_size = self.get_size(f'{folder}/{a_file[:-4]}.dbf')
                    size = geom_size + attribute_size
                else:
                    size = self.get_size(f'{folder}/{a_file}')
                data_list.append([data_type, name, a_file, folder, size])
                
        df = pd.DataFrame(data_list, columns=['Type','Dataset','File','Path','Size (MB)'])

        if datatype == None:

            return df
        
        else:

            return df[df['Type'] == datatype]
        
            
    def get_datasets(self):

        '''
        A "Dataset" is a folder in the download section and can contain one or many files.
        '''

        self.l.debug('get_datasets')
        
        dataset_list = []
        subfolders = [ f.path for f in os.scandir('/download') if f.is_dir() ]
        for a_subfolder in subfolders:
            name = a_subfolder[10:]
            dataset_list.append([name, a_subfolder])
        return dataset_list
    
    
    def get_size(self, path_to_file):
        
        self.l.debug(f'get_size of {path_to_file}')

        try:
            return round(os.path.getsize(path_to_file) / 1048576, 2)
        except:
            return 0
    
    def get_files(self, dataset):

        self.l.debug('get_files for {dataset}')
        
        dataset_list = []
        for a_file in os.listdir(f'/download/{dataset}'):
            
            extension = a_file.split('.')[-1]
            if extension not in ['prj','shx','dbf','cpg']:
                dataset_list.append(a_file)
        return dataset_list
    
    def get_type(self, file):

        self.l.debug('get_type for {file}')
    
        if len(file.split('.')) < 2:
            return "Unknown"
    
        e1 = file.split('.')[-1]
        e2 = file.split('.')[-2]
    
        if e1 == 'shp':
        
            return 'Shape'
    
        if e2 == 'shp' and e1 == 'zip':
        
            return 'Shape archive'
    
        if e1 == 'pbf' and e2 == 'osm':
        
            return 'OSM PBF'