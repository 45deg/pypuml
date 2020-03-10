from astroid import manager, modutils, node_classes
import astroid.nodes as ast_node
import pypuml.entity as ent
from typing import List, Mapping
import os
import filecmp

from pypuml.writer import UmlWriter


class AstAnalyzer(object):
    def visit_module(self, ast: ast_node.Module) -> ent.Module:
        module = ent.Module(ast.name)
        for child in ast.get_children():
            if isinstance(child, ast_node.ClassDef):
                module.definitions.append(self.visit_class_def(child))
        return module

    def visit_class_def(self, ast: ast_node.ClassDef) -> ent.ClassDef:
        cls = ent.ClassDef(ast.name, ast.root().name)

        for method in ast.mymethods():
            cls.methods.append(ent.Method(method.name, method.type_annotation))

        for instance_attrs in ast.instance_attrs.values():
            for instance_attr in instance_attrs:
                cls.attributes.append(self.visit_instance_attr(instance_attr))

        for anc in ast.ancestors(recurs=False):
            cls.ancestors.append(self.visit_class_def(anc))

        return cls

    def visit_instance_attr(self, instance_attr: node_classes.NodeNG) -> ent.Attribute:
        if isinstance(instance_attr, ast_node.AssignAttr):
            return ent.Attribute(instance_attr.attrname, None)
        elif isinstance(instance_attr.parent, ast_node.AnnAssign):
            # cf. astroid/brain/brain_dataclasses.py
            return ent.Attribute(
                instance_attr.parent.target.name, instance_attr.parent.annotation
            )


class Project(object):
    def __init__(self):
        self._modules: Mapping[str, ast_node.Module] = {}
        self._manager = manager.AstroidManager()
        self._locals = {}

    def add_module(self, name: str, node: ast_node.Module):
        self._modules[name] = node

    def load_from_file(self, file: str, blacklist: List[str] = []):
        if os.path.isdir(file):
            fpath = os.path.join(file, "__init__.py")
        elif os.path.exists(file):
            fpath = file
        else:
            fpath = modutils.file_from_modpath(file.split("."))

        ast = self._manager.ast_from_file(fpath)
        self.add_module(ast.name, ast)

        if ast.package:
            for child_path in modutils.get_module_files(file, blacklist):
                if not filecmp.cmp(child_path, fpath):
                    self.load_from_file(child_path, blacklist)

    def generate(self):
        print("@startuml")
        for name, mod in self._modules.items():
            UmlWriter().write_module(AstAnalyzer().visit_module(mod))
        print("@enduml")
