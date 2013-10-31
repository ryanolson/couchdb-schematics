import json
import couchdb.mapping
from schematics.models import Model, ModelMeta
from schematics.transforms import blacklist, whitelist
from schematics.types import StringType
from schematics.types.compound import ModelType
from schematics.types.serializable import serializable

class EmbeddedModelType(ModelType):
    def export_loop(self, model_instance, field_converter,
                    role=None, print_none=False):
        if role is None:
            role = "embedded"
        return super(EmbeddedModelType, self).export_loop(model_instance,
            field_converter, role=role, print_none=print_none)


class EmbeddedDocType(EmbeddedModelType):
    pass


class DocumentMeta(ModelMeta):
    def __new__(cls, name, bases, d):
        for attrname, attrval in d.items():
            if isinstance(attrval, couchdb.mapping.ViewField):
                if not attrval.name:
                    attrval.name = attrname
        return ModelMeta.__new__(cls, name, bases, d)


class SchematicsDocument(Model):
    __metaclass__ = DocumentMeta

    class Options:
        serialize_when_none = False
        roles = {
            "default": blacklist("doc_id"),
            "embedded": blacklist("_id", "_rev", "doc_type"),
        }

    _id = StringType(deserialize_from=['id', 'doc_id'])
    _rev = StringType()
    doc_type = StringType()

    def __init__(self, raw_data=None, deserialize_mapping=None):
        if raw_data is None:
            raw_data = { }
        id = raw_data.pop('id', None)
        super(SchematicsDocument, self).__init__(raw_data=raw_data,
            deserialize_mapping=deserialize_mapping)
        if id:
           self.id = id
        self.doc_type = self.__class__.__name__

    def __repr__(self):
        return '<%s %r@%r %r>' % (type(self).__name__, self.id, self.rev,
                                  dict([(k, v) for k, v in self._data.items()
                                        if k not in ('_id', '_rev')]))
    def _get_id(self):
        return self._id
    def _set_id(self, value):
        if self.id is not None:
           raise AttributeError('id can only be set on new documents')
        self._id = value
    id = property(_get_id, _set_id, doc='The document ID')

    @serializable(role="embedded")
    def doc_id(self):
        return self._id

    @property
    def rev(self):
        return self._rev

    def serialize(self,**kwargs):
        retval = super(SchematicsDocument,self).serialize(**kwargs)
        if self.id is None and '_id' in retval: del retval['_id']
        if self.rev is None and '_rev' in retval: del retval['_rev']
        return retval

    @classmethod
    def wrap(cls, data):
        instance = cls(data)
        return instance

    @classmethod
    def load(cls, db, id):
        """Load a specific document from the given database.
        
        :param db: the `Database` object to retrieve the document from
        :param id: the document ID
        :return: the `Document` instance, or `None` if no document with the
                 given ID was found
        """
        doc = db.get(id)
        if doc is None:
            return None
        return cls.wrap(doc)

    def store(self, db, validate=True):
        """Store the document in the given database."""
        if validate:
           self.validate()
        self._id, self._rev = db.save(self.to_native())
        return self

    def reload(self, db):
        """
        This function reloads/rehydrates the Document Model.  This
        is especially useful for embedded documents that are stored
        in a dehydrated state.
        """
        if self.id is None:
            raise ValueError("_id/id property is None")
        self.import_data(db.get(self.id))
        return self

    def hydrate(self, db, recursive=True):
        for field in self._fields:
            obj = getattr(self, field)
            if isinstance(obj, SchematicsDocument):
                obj.reload(db)
                if recursive:
                    obj.hydrate(db)
        return self

# functions below this point have not been tested

    @classmethod
    def query(cls, db, map_fun, reduce_fun, language='javascript', **options):
        """Execute a CouchDB temporary view and map the result values back to
        objects of this mapping.
        
        Note that by default, any properties of the document that are not
        included in the values of the view will be treated as if they were
        missing from the document. If you want to load the full document for
        every row, set the ``include_docs`` option to ``True``.
        """
        return db.query(map_fun, reduce_fun=reduce_fun, language=language,
                        wrapper=cls._wrap_row, **options)

    @classmethod
    def view(cls, db, viewname, **options):
        """Execute a CouchDB named view and map the result values back to
        objects of this mapping.
        
        Note that by default, any properties of the document that are not
        included in the values of the view will be treated as if they were
        missing from the document. If you want to load the full document for
        every row, set the ``include_docs`` option to ``True``.
        """
        return db.view(viewname, wrapper=cls._wrap_row, **options)

    @classmethod
    def _wrap_row(cls, row):
        doc = row.get('doc')
        if doc is not None:
            return cls.wrap(doc)
        data = row['value']
        data['_id'] = row['id']
        return cls.wrap(data)

