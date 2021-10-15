"""This module contains a linting function for a tool's configfiles section.
"""


def lint_configfiles(tool_xml, lint_ctx):
    """"""
    root = tool_xml.getroot()
    configfiles = root.findall("configfiles")
    if len(configfiles) > 1:
        lint_ctx.error("More than one configfiles tag found, behavior undefined.")
        return
    elif len(configfiles) == 0:
        return
    configfiles = configfiles[0]

    configfile = configfiles.findall("configfile|inputs")
    for cf in configfile:
        if not ("name" in cf.attrib or "filename" in cf.attrib):
            lint_ctx.error("Configfile needs to define name or filename.")
        if cf.tag == "inputs":
            if "data_style" in cf.attribs and cf.attribs["data_style"] in ["paths", "staging_path_and_source_path"]:
                lint_ctx.error(f"Unknown data_style {cf.attribs['data_style']}for inputs configfile.")
