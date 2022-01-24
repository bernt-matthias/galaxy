from collections import OrderedDict

DEFAULT_DELTA = 10000
DEFAULT_DELTA_FRAC = None


def is_dict(item):
    return isinstance(item, dict) or isinstance(item, OrderedDict)


def _prepare_argument(argument):
    if argument is None:
        return ""
    return argument.lstrip('-').replace("-", "_")


def _parse_name(name, argument):
    """Determine name of an input source from name and argument
    returns the name or if absent the argument property
    In the latter case, leading dashes are stripped and
    all remaining dashes are replaced by underscores.
    """
    if name is None:
        if argument is None:
            raise ValueError("parameter must specify a 'name' or 'argument'.")
        name = _prepare_argument(argument)
    return name
