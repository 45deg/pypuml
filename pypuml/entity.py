import typing
from typing import List


class PythonType(object):
    def __init__(self, raw_type: typing.Type):
        self.raw_type = raw_type


class Method(object):
    def __init__(self, name: str, ret_type: PythonType):
        self.name = name
        self.type = ret_type


class Attribute(object):
    def __init__(self, name: str, attr_type: PythonType):
        self.name = name
        self.attr_type = attr_type


class Definition(object):
    pass


class ClassDef(Definition):
    def __init__(self, name: str, root: str):
        self.name = name
        self.root = root
        self.methods: List[Method] = []
        self.attributes: List[Attribute] = []
        self.ancestors: List[ClassDef] = []


class TypeDef(Definition):
    def __init__(self, name: str, alias: PythonType):
        self.name = name
        self.alias = alias


class Module(object):
    def __init__(self, name: str):
        self.name = name
        self.definitions: List[Definition] = []
        self.children: List[Module] = []
