from astroid import modutils, node_classes
from astroid.manager import AstroidManager
import astroid.nodes as ast_node
import os
import sys

def is_target_module(mod_name: str):
    return mod_name != "builtins"


class ModuleVisitor(object):
    def __init__(self):
        self._manager = AstroidManager()
        self._manager._transform.transforms = []
        self.output = []
        self.child_modules = []
        self.indent = 0
        self.file = None
        self.blacklist = []

    def exec(self, file):
        self.file = file
        print("@startuml")
        self.load_module().accept(self)
        print("@enduml")

    def walk_child_modules(self):
        for child_path in modutils.get_module_files(self.file, self.blacklist):
            if child_path.endswith("__init__.py"):
                continue
            orig_file = self.file
            self.file = child_path
            yield self.load_module()
            self.file = orig_file

    def load_module(self):
        if os.path.isdir(self.file):
            fpath = os.path.join(self.file, "__init__.py")
        elif os.path.exists(self.file):
            fpath = self.file
        else:
            fpath = modutils.file_from_modpath(self.file.split("."))

        return self._manager.ast_from_file(fpath)

    def write(self, line: str):
        print("    " * self.indent + line)

    def visit_module(self, ast: ast_node.Module):
        self.write("namespace %s {" % ast.name)
        self.indent += 1

        for child in ast.body:
            if isinstance(child, ast_node.ClassDef):
                child.accept(self)

        if ast.package:
            for child_mod in self.walk_child_modules():
                child_mod.accept(self)

        self.indent -= 1
        self.write("}")

    def visit_classdef(self, ast: ast_node.ClassDef):

        self.write("class %s {" % ast.name)
        self.indent += 1

        for instance_attrs in ast.instance_attrs.values():
            for attr in instance_attrs:
                if isinstance(attr, ast_node.AssignAttr):
                    attr.accept(self)
                    break

        for local in ast.values():
            local.accept(self)

        self.indent -= 1
        self.write("}")

        for anc in ast.ancestors(recurs=False):
            cls = next(anc.infer())
            if isinstance(cls, ast_node.ClassDef):
                module = cls.root().name
                if is_target_module(module):
                    self.write("%s <|- %s.%s" % (ast.name, cls.root().name, cls.name))

    def visit_functiondef(self, ast: ast_node.FunctionDef):
        args = ast.argnames()
        ret_type = " -> %s" % ast.returns.as_string() if ast.returns else ""
        modifier = ""
        if ast.is_abstract():
            modifier += "{abstract} "
        if ast.type in {"classmethod", "staticmethod"}:
            modifier += "{static} "
        self.write("%s%s(%s)%s" % (modifier, ast.name, ','.join(args), ret_type))

    def visit_asyncfunctiondef(self, ast: ast_node.AsyncFunctionDef):
        self.visit_functiondef(ast)

    def visit_assignname(self, ast: ast_node.AssignName):
        ast.assign_type().accept(self)

    def visit_assign(self, ast: ast_node.Assign):
        for target in ast.targets:
            self.write("{static} %s" % target.name)

    def visit_annassign(self, ast: ast_node.AnnAssign):
        self.write("{static} %s : %s" % (ast.target.name, ast.annotation.as_string()))

    def visit_assignattr(self, ast: ast_node.AssignAttr):
        parent = ast.parent
        if isinstance(parent, ast_node.Assign):
            self.write("%s" % ast.attrname)
        elif isinstance(parent, ast_node.AnnAssign):
            self.write("%s : %s" % (ast.attrname, parent.annotation.as_string()))

    def __getattr__(self, item):
        def _missing(*args, **kwargs):
            # print("\u001b[31m", item, args, kwargs, "\u001b[0m")
            return None
        return _missing

def main():
    a = ModuleVisitor()
    a.exec(sys.argv[1])
