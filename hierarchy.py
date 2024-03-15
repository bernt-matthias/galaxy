import importlib
import inspect
import os
import yaml

from galaxy.datatypes.data import Data


def submodules(package_name):
    submodules = []
    package_path = importlib.util.find_spec(package_name).submodule_search_locations[0]
    for item in os.listdir(package_path):
        if os.path.isfile(os.path.join(package_path, item)) and item.endswith(".py"):
            submodule_name = f"{package_name}.{item[:-3]}"
            if importlib.util.find_spec(submodule_name):
                submodule = importlib.import_module(submodule_name)
                submodules.append(submodule)
    return submodules


def get_subclasses(base_class, modules):
    subclasses = set()
    for module in modules:
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, base_class) and cls != base_class and base_class == cls.__bases__[0]:
                # if issubclass(cls, base_class) and cls != base_class:
                subclasses.add(cls)
    return subclasses


def get_property(cls, property_name, allow_inherited):
    if allow_inherited:
        return getattr(cls, property_name, None)
    elif property_name in cls.__dict__:
        return cls.__dict__[property_name]
    else:
        return None


def get_hierarchy(root_class, modules, all_classes):
    name = root_class.__name__
    assert root_class not in all_classes, name
    all_classes.add(root_class)

    hierarchy = {}
    hierarchy["name"] = name
    hierarchy["ext"] = get_property(root_class, "file_ext", False)
    hierarchy["edam_format"] = get_property(root_class, "edam_format", False)
    hierarchy["edam_data"] = get_property(root_class, "edam_data", False)
    hierarchy["subclasses"] = []
    subclasses = get_subclasses(root_class, modules)
    for subclass in subclasses:
        # print(f"subclass {root_class} {subclass}")
        hierarchy["subclasses"].append(get_hierarchy(subclass, modules, all_classes))
    return hierarchy


datatype_modules = submodules("galaxy.datatypes")

all_classes = set()
hierarchy = get_hierarchy(Data, datatype_modules, all_classes)

print(yaml.dump(hierarchy))
