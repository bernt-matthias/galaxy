import re


def get_code(tool_xml):
    """get code used in the Galaxy tool"""

    # get code from
    # - command,
    # - configfiles, and
    # - template macros
    # note: not necessary (& possible) for macro tokens which are expanded
    # during loading the xml (and removed from the macros tag)
    code = ""
    for tag in [".//command", ".//configfile", './/macros/macro[@type="template"]']:
        print(f"tag {tag}")
        for cn in tool_xml.findall(tag):
            print(f"node {cn}")
            code += cn.text

    # remove comments,
    # TODO this is not optimal, but strings containing "##"" complicate this quite a bit
    # TODO also this is not complete, e.g. multiline comments are missing
    code = "\n".join([_ for _ in code.splitlines() if not _.lstrip().startswith("##")])

    # get code from output filters
    filtercode = ""
    for cn in tool_xml.findall("./outputs/*/filter"):
        filtercode += cn.text + "\n"

    # get output labels which might contain code
    labelcode = ""
    for cn in tool_xml.findall("./outputs/*[@label]"):
        labelcode + cn.attrib["label"] + "\n"

    # TODO not optimal to mix filter code and the following, since they use cheetah synax, i.e. $param
    for cn in tool_xml.findall("./outputs/*/actions/action[@default]"):
        labelcode += cn.attrib["default"] + "\n"

    for cn in tool_xml.findall("./outputs/*/actions/conditional[@name]"):
        labelcode += cn.attrib["name"] + "\n"

    return code, filtercode, labelcode


def is_datasource(tool_xml):
    """Returns true if the tool is a datasource tool"""
    return tool_xml.getroot().attrib.get("tool_type", "") == "data_source"


def is_valid_cheetah_placeholder(name):
    """Returns true if name is a valid Cheetah placeholder"""
    return not re.match(r"^[a-zA-Z_]\w*$", name) is None
