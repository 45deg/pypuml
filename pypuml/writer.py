from pypuml.entity import ClassDef, Module


def is_target_module(mod_name: str):
    return mod_name != "builtins"


class UmlWriter(object):
    def write_module(self, module: Module):
        for definition in module.definitions:
            if isinstance(definition, ClassDef):
                self.write_classdef(definition)

    def write_classdef(self, cls: ClassDef):
        print(f"class {cls.root}.{cls.name} {{")

        for method in cls.methods:
            print(f"  {method.name}()")

        for attr in cls.attributes:
            print(f"  {attr.name}")

        print("}")

        for anc in cls.ancestors:
            if is_target_module(anc.root):
                print(f"  {cls.root}.{cls.name} <|-- {anc.root}.{anc.name}")
