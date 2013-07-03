import unittest
from couchdb.tests import testutil

from schematics.models import Model
from schematics.types import StringType
from couchdb_schematics.document import SchematicDocument

class User1(SchematicDocument):
    name = StringType()

class TestSchematicDocument(testutil.TempDatabaseMixin, unittest.TestCase):

    def test_user1(self):
        u = User1()
        u.name = "Ryan"
        u.store(self.db)

        assert u.id is not None
        assert u.rev is not None

        fromdb = self.db.get(u.id)
        assert u.name == fromdb['name']

        u2 = User1.wrap(fromdb)
        assert u.name == u2.name

        u3 = User1(**fromdb)
        assert u.name == u3.name

        u4 = User1.load(self.db, u.id)
        assert u.name == u4.name

