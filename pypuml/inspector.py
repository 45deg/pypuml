from astroid import manager, modutils
import astroid.nodes as ast_node
from typing import List, Mapping
import os
import filecmp


def is_target_module(mod: ast_node.Module):
    return mod.name != "builtins"


class AstVisitor(object):
    def visit(self, ast):
        if isinstance(ast, ast_node.Module):
            self.visit_module(ast)
        elif isinstance(ast, ast_node.ClassDef):
            self.visit_classdef(ast)

    def visit_module(self, ast: ast_node.Module):
        if not is_target_module(ast):
            return

        print(f"namespace {ast.name} {{")
        for child in ast.get_children():
            self.visit(child)
        print("}")

    def visit_classdef(self, ast: ast_node.ClassDef):
        cls_name = ast.root().name + "." + ast.name

        cls_methods = set()
        cls_attrs = set()
        cls_ancestors = ast.ancestors(recurs=False)

        for method in ast.mymethods():
            cls_methods.add(method.name)

        for instance_attrs in ast.instance_attrs.values():
            for instance_attr in instance_attrs:
                if isinstance(instance_attr, ast_node.AssignAttr):
                    cls_attrs.add(instance_attr.attrname)
                elif isinstance(instance_attr.parent, ast_node.AnnAssign):
                    # cf. astroid/brain/brain_dataclasses.py
                    cls_attrs.add(instance_attr.parent.target.name)

        print(f"  class {cls_name} {{")

        for method in cls_methods:
            print(f"    {method}()")

        for attr in cls_attrs:
            print(f"    {attr}")

        print("  }")

        for anc in cls_ancestors:
            if is_target_module(anc.root()):
                print(f"  {cls_name} <|-- {anc.root().name}.{anc.name}")


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
            AstVisitor().visit_module(mod)
        print("@enduml")

    @classmethod
    def load_from_files(cls, files: List[str]):
        project = cls()
        for file in files:
            project.load_from_file(file)
        return project
