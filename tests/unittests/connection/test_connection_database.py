import sys
from unittest import TestCase


class TestConnectionDatabase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        return super().tearDown()

    # def test_database_context_postgres_connect(self):
    #     self.database_context = DatabaseProvider().get_context(connection_type=ConnectionTypes(1),
    #                                                            connector_type=ConnectorTypes(3),
    #                                                            host='localhost', port='5432', user='postgres',
    #                                                            password='123456', database='test_pdi')
    #     self.database_context.connector.connect()
