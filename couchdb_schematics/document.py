# -*- coding: utf-8 -*-
"""
    __init__.py
    ~~~~~~~~~~~

    :author: Ryan Olson
    :copyright: (c) 2013 Ryan Olson
    :license: Apache v2, see LICENSE for more details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import couchdb.mapping
from schematics.models import Model, ModelMeta
from schematics.transforms import blacklist
from schematics.types import StringType
from schematics.types.compound import ModelType
from schematics.types.serializable import serializable

class EmbeddedModelType(ModelType):
    """
    Adapation of schematics.types.compound.ModelType that passes the embedded
    role to export_loop if no role is passed.
    """
    def export_loop(self, model_instance, field_converter,
                    role=None, print_none=False):
        if role is None:
            role = "embedded"
        return super(EmbeddedModelType, self).export_loop(model_instance,
            field_converter, role=role, print_none=print_none)


class EmbeddedDocType(EmbeddedModelType):
    """
    Unique field type for embedded SchematicDocuments.  Maybe needed to for
    specializing EmbeddedModelType for SchematicDocuments.
    """
    pass


class DocumentMeta(ModelMeta):
    """
    Extension of schematics.models.ModelMeta to properly initialize a
    couchdb.mapping.ViewField.
    """
    def __new__(mcs, name, bases, attrs):
        for attrname, attrval in attrs.items():
            if isinstance(attrval, couchdb.mapping.ViewField):
                if not attrval.name:
                    attrval.name = attrname
        return ModelMeta.__new__(mcs, name, bases, attrs)


class Document(Model):
    """
    Schematics-based CouchdDB Document class.
    """
    __metaclass__ = DocumentMeta

    class Options(object):
        """Export options for Document."""
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
        super(Document, self).__init__(raw_data=raw_data,
            deserialize_mapping=deserialize_mapping)
        self.doc_type = self.__class__.__name__

    def __repr__(self):
        return '<%s %r@%r %r>' % (type(self).__name__, self.id, self.rev,
                                  dict([(k, v) for k, v in self._data.items()
                                        if k not in ('_id', '_rev')]))
    def _get_id(self):
        """id property getter."""
        return self._id
    def _set_id(self, value):
        """id property setter."""
        if self.id is not None:
            raise AttributeError('id can only be set on new documents')
        self._id = value
    id = property(_get_id, _set_id, doc='The document ID')

    @serializable
    def doc_id(self):
        """A property that is serialized by schematics exports."""
        return self._id

    @property
    def rev(self):
        """A property for self._rev"""
        return self._rev

    @classmethod
    def wrap(cls, data):
        """
        Instantiates an instance of `Document` with data.  Mirrors
        functionality found in a couchdb-python Document.

        :param data: instance or dict of data to be imported.
        :return: new `Document` instance initialized with data.
        """
        instance = cls(data)
        return instance

    @classmethod
    def load(cls, database, doc_id):
        """Load a specific document from the given database.

        :param database: the `Database` object to retrieve the document from
        :param doc_id: the document ID
        :return: the `Document` instance, or `None` if no document with the
                 given ID was found
        """
        doc = database.get(doc_id)
        if doc is None:
            return None
        return cls.wrap(doc)

    def store(self, database, validate=True, role=None):
        """Store the document in the given database.

        :param database: the `Database` object source for storing the document.
        :return: an updated instance of `Document` / self.
        """
        if validate:
            self.validate()
        self._id, self._rev = database.save(self.to_primitive(role=role))
        return self

    def delete_instance(self, database):
        if self._id is None:
            raise ValueError("no valid document id")
        del database[self.id]

    def reload(self, database):
        """
        This function reloads/rehydrates the Document Model.  This
        is especially useful for embedded documents that are stored
        in a dehydrated state.

        :param database: the `Database` object source for reloading the document
        :return: an updated instance of `Document` / self.
        """
        if self.id is None:
            raise ValueError("_id/id property is None")
        self.import_data(database.get(self.id))
        return self

    def hydrate(self, database, recursive=True):
        """
        By default, recursively reloads all instances of Document
        in the model.  Recursion can be turned off.

        :param database: the `Database` object source for rehydrating.
        :return: an updated instance of `Document` / self.
        """
        if isinstance(self, Document):
            self.reload(database)
        for field in self:
            obj = getattr(self, field)
            if isinstance(obj, Document):
                obj.reload(database)
                if recursive:
                    obj.hydrate(database)
        return self

# functions below this point have not been tested

    @classmethod
    def query(cls, database, map_fun, reduce_fun,
              language='javascript', **options):
        """Execute a CouchDB temporary view and map the result values back to
        objects of this mapping.

        Note that by default, any properties of the document that are not
        included in the values of the view will be treated as if they were
        missing from the document. If you want to load the full document for
        every row, set the ``include_docs`` option to ``True``.
        """
        return database.query(map_fun, reduce_fun=reduce_fun, language=language,
                        wrapper=cls._wrap_row, **options)

    @classmethod
    def view(cls, database, viewname, **options):
        """Execute a CouchDB named view and map the result values back to
        objects of this mapping.

        Note that by default, any properties of the document that are not
        included in the values of the view will be treated as if they were
        missing from the document. If you want to load the full document for
        every row, set the ``include_docs`` option to ``True``.
        """
        return database.view(viewname, wrapper=cls._wrap_row, **options)

    @classmethod
    def _wrap_row(cls, row):
        """Wrap ViewField or ViewDefinition Rows."""
        doc = row.get('doc')
        if doc is not None:
            return cls.wrap(doc)
        data = row['value']
        data['_id'] = row['id']
        return cls.wrap(data)


class SchematicsDocument(Document):
    """
    Depreciated class for Document.
    """
    pass
