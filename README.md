# CouchDB + Schematics

Python Structured CouchDB Documents for Humans

[![Build Status](https://travis-ci.org/ryanolson/couchdb-schematics.png)](https://travis-ci.org/ryanolson/couchdb-schematics)

## Here it is!!

You can start with a standalone schematics model

```python
from schematics.models import Model
from schematics.types import StringType

class User(Model):
    name = StringType()
    email = StringType(required=True)
```

and mix in a SchematicsDocument

```python
from couchdb_schematics.document import SchematicsDocument

class UserDocument(SchematicsDocument, User):
   pass
```

or equivalently,

```python
from couchdb_schematics.document import SchematicsDocument
from schematics.types import StringType

class UserDocument(SchematicsDocument):
    name = StringType()
    email = StringType(required=True)
```

Now you are ready to load, store and setup either ViewFields or ViewDefinitions.

```python
from couchdb import Server

server = Server()
if 'test' not in server:
   server.create('test')
db = server['test']

# both forms of initialization are equivalent
user = UserDocument(dict(name='Ryan', email='thedude@gmail.com'))

user.store(db)

# note: SchematicsDocument provides UserDocument with id and rev attirbutes
# that correspond to _id and _rev values of a CouchDB document
# SchematicsDocuments alway set the doc_type attribute to the name of the classs

# read the data back in
u2 = UserDocument.load(db, user.id)

assert u2.email = 'thedude@gmail.com'
assert u2.doc_type == 'UserDocument'
```

## Installation

```bash
$ pip install couchdb-schematics
```

## Tests

```
$ py.test tests/
```
