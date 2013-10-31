import unittest
from couchdb.tests import testutil

from schematics.models import Model
from schematics.transforms import blacklist
from schematics.types import StringType, MD5Type
from couchdb_schematics.document import SchematicsDocument
from couchdb_schematics.document import EmbeddedDocType

class User1Model(Model):
    name = StringType()

class User2Model(User1Model):
    _password = MD5Type(serialized_name="password")

class User1(SchematicsDocument, User1Model):
    pass 

class User2(SchematicsDocument, User2Model):

    def __init__(self, raw_data=None, **kwargs):
        if raw_data is None:
            raw_data = {}
        password = raw_data.pop("password", None)
        super(User2, self).__init__(raw_data=raw_data, **kwargs)
        if password:
            if '_rev' in raw_data:
                self._password = password
            else:
                self.password = password

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

        u3 = User1(fromdb)
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

        u3 = User2(fromdb)
        assert u.password == u3.password

        u4 = User2.load(self.db, u.id)
        assert u.password == u4.password

        assert u4.challenge_password("ChangeMe")


    def test_EmbeddedDocType(self):
        class SuperUser(SchematicsDocument):
            user = EmbeddedDocType(User2)

        u = User2(dict(name="Ryan", password="ChangeMe"))
        u.store(self.db)

        su = SuperUser()
        su.user = u
        assert isinstance(su.user, User2)

        su_native = su.to_native()
        assert 'user' in su_native
        assert 'doc_id' in su_native['user']
        assert '_id' not in su_native['user']
        assert '_rev' not in su_native['user']
        assert 'doc_type' not in su_native['user']
        su.validate()

    def test_EmbeddedDocType_overriding_Options(self):
        class User3(User2):
            class Options:
                roles = {
                    "embedded": (blacklist("_password") +
                        SchematicsDocument.Options.roles['embedded']),
                }
        class SuperUser(SchematicsDocument):
            user = EmbeddedDocType(User3)

        u = User3(dict(name="Ryan", password="ChangeMe"))
        assert 'id' not in u.serialize()
        u.store(self.db)

        su = SuperUser()
        su.user = u
        su.store(self.db)
        assert isinstance(su.user, User3)

        print su.user.Options.roles
        assert '_password' in su.user.Options.roles['embedded']

        su_native = su.to_native()
        assert 'user' in su_native
        assert 'doc_id' not in su_native
        assert 'doc_id' in su_native['user']
        assert '_id' not in su_native['user']
        assert '_rev' not in su_native['user']
        assert 'doc_type' not in su_native['user']
        assert 'password' not in su_native['user']

        fromdb = SuperUser.load(self.db, su.id)
        su_native = fromdb.to_native()
        assert 'user' in su_native
        assert 'doc_id' not in su_native
        assert 'doc_id' in su_native['user']
        assert '_id' not in su_native['user']
        assert '_rev' not in su_native['user']
        assert 'doc_type' not in su_native['user']
        assert 'password' not in su_native['user']

        fromdb.user.reload(self.db)
        assert fromdb.user.password == su.user.password
