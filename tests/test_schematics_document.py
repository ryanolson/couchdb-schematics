import unittest
from couchdb.tests import testutil

from schematics.models import Model
from schematics.types import StringType, MD5Type
from couchdb_schematics.document import SchematicsDocument

class User1Model(Model):
    name = StringType()

class User2Model(User1Model):
    _password = MD5Type(serialized_name="password")

class User1(User1Model,SchematicsDocument):
    pass 

class User2(User2Model,SchematicsDocument):

    def __init__(self, **kwargs):
        super(User2, self).__init__(**kwargs)
        if 'password' in kwargs and '_rev' not in kwargs:
           self.password = kwargs['password']

    # password property
    def _get_password(self):
        return self._password
    def _set_password(self,passwd):
        self._password = self._salted_password(passwd)
    password = property(_get_password, _set_password)

    def challenge_password(self,passwd):
        if self.password == self._salted_password(passwd): return True
        return False

    def _salted_password(self, passwd):
        s = "salt+{}".format(passwd)
        import hashlib
        val = hashlib.md5(s).hexdigest()
        print val
        return val

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

    def test_model_with_serialized_name(self):
        u = User2()
        u.name = "Ryan"
        u.password = "ChangeMe"
        u.store(self.db)

        print u.password

        fromdb = self.db.get(u.id)
        assert u.password == fromdb['password']

        u2 = User2.wrap(fromdb)
        assert u.password == u2.password

        u3 = User2(**fromdb)
        assert u.password == u3.password

        u4 = User2.load(self.db, u.id)
        assert u.password == u4.password

        assert u4.challenge_password("ChangeMe")
