import unittest
from . import gdal

class TestGdal(unittest.TestCase):

    def test_class_init(self):

        gdal_class = gdal.Gdal()
        self.assertEqual(gdal_class.download_folder, './downloads')
        self.assertEqual(gdal_class.host, 'postgres')
        self.assertEqual(gdal_class.database, 'postgres')
        self.assertEqual(gdal_class.user, 'postgres')#
        self.assertEqual(gdal_class.schema, None)

 