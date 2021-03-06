import unittest
import cobra.postgres.interface as pgi
from cobra.postgres.interface import TableDefinition, FieldDefinition
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

test_db_name = 'testdb'

class TestPgi(unittest.TestCase):

    def test_class_init(self):

        i = pgi.PgInterface()
        self.assertEqual(i.database, 'postgres')
       

    def test_new_db(self):

        db_name = 'testfest'
        schema_name = 'schemama'
        table_name = 'my_table'
        field_name = 'name'
        field_type = 'text'

        i = pgi.PgInterface()

        i.create_database(db_name)

        #Check if new database exists
        self.assertTrue(db_name in i.get_database_list())
        
        i = pgi.PgInterface(database=db_name)

        i.create_schema(schema_name)

        #Check if new schema exists
        self.assertTrue(schema_name in i.get_schema_list())

        i.switch_schema(schema_name)

        #Check if current schema is set
        self.assertTrue(i.current_schema == schema_name)

        td = TableDefinition(table_name)
        fd = FieldDefinition(field_name, field_type)

        td.add_field(fd)
        i.create_table(td)

        self.assertTrue(table_name in i.get_table_list(schema_name=schema_name))

        i.insert_into_table(table_name, ['name'], [['schödinger']])

        i = pgi.PgInterface()
        i.drop_database(db_name)

        self.assertFalse(db_name in i.get_database_list())

    def test_simple_insert(self):

        db_name = 'test'
        table_name = 'my_table'

        i = pgi.PgInterface()
        i.create_database(db_name)
        i = pgi.PgInterface(db_name)

        tb = TableDefinition(table_name)
        fd_str = FieldDefinition('my_string','text')
        fd_num = FieldDefinition('my_num', 'numeric')
        tb.add_field(fd_str)
        tb.add_field(fd_num)

        i.create_table(tb)

        #Insert list of values
        i.insert_into_table('my_table', ['my_string','my_num'],[['cobra','79'],['about','42']])

        self.assertEqual(i.table_row_count('my_table'), 2)

        #Insert single row
        i.insert_into_table('my_table', ['my_string','my_num'],['John', '101'])

        self.assertEqual(i.table_row_count('my_table'), 3)

        i = pgi.PgInterface()
        i.drop_database(db_name)


        


