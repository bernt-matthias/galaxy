"""This module describes the :class:`ExplicitContainerResolver` ContainerResolver plugin."""
import logging

from ..container_resolvers import (
    ContainerResolver,
    CliContainerResolver,
    SingularityCliContainerResolver,
)
from ..requirements import ContainerDescription

log = logging.getLogger(__name__)

DEFAULT_SHELL = "/bin/bash"


class ExplicitContainerResolver(CliContainerResolver):
    """Find explicit containers referenced in the tool description (e.g. tool XML file) if present."""

    resolver_type = "explicit"

    def resolve(self, enabled_container_types, tool_info, **kwds):
        """Find a container explicitly mentioned in tool description.

        This ignores the tool requirements and assumes the tool author crafted
        a correct container.
        """
        log.error("ExplicitContainerResolver.resolve")
        for container_description in tool_info.container_descriptions:
            if self._container_type_enabled(container_description, enabled_container_types):
                container_description.explicit = True
                return container_description

        return None


# TODO is it correct to change class hierarcy (i.e. not to derive from ExplicitContainerResolver)
class ExplicitSingularityContainerResolver(SingularityCliContainerResolver):

    resolver_type = 'explicit_singularity'
    container_type = 'singularity'

    def resolve(self, enabled_container_types, tool_info, install=False, **kwds):
        """Find a container explicitly mentioned in tool description.

        This ignores the tool requirements and assumes the tool author crafted
        a correct container. We use singularity here to fetch docker containers,
        hence the container_description hack here.
        """
        log.error("ExplicitSingularityContainerResolver.resolve")
        for container_description in tool_info.container_descriptions:
            if container_description.type == 'docker':
                desc_dict = container_description.to_dict()
                desc_dict['type'] = self.container_type
                desc_dict['identifier'] = "docker://%s" % container_description.identifier
                container_description = container_description.from_dict(desc_dict)
            if self.cli_available:
                if install: # TODO cache check
                    destination_info = {}
                    destination_for_container_type = kwds.get('destination_for_container_type')
                    if destination_for_container_type:
                        destination_info = destination_for_container_type(self.container_type)
                    container = CONTAINER_CLASSES[self.container_type](container_description.identifier,
                                                                       self.app_info,
                                                                       tool_info,
                                                                       destination_info,
                                                                       {},
                                                                       container_description)
                    pass
                # TODO if not self.auto_install:

            if self._container_type_enabled(container_description, enabled_container_types):
                return container_description

        return None


class BaseAdminConfiguredContainerResolver(ContainerResolver):

    def __init__(self, app_info=None, shell=DEFAULT_SHELL, **kwds):
        super().__init__(app_info, **kwds)
        self.shell = shell

    def _container_description(self, identifier, container_type):
        container_description = ContainerDescription(
            identifier,
            type=container_type,
            shell=self.shell,
        )
        return container_description


class FallbackContainerResolver(BaseAdminConfiguredContainerResolver):
    """Specify an explicit, identified container as a Docker container resolver."""

    resolver_type = "fallback"
    container_type = 'docker'

    def __init__(self, app_info=None, identifier="", **kwds):
        super().__init__(app_info, **kwds)
        assert identifier, "fallback container resolver must be specified with non-empty identifier"
        self.identifier = identifier

    def _match(self, enabled_container_types, tool_info, container_description):
        if self._container_type_enabled(container_description, enabled_container_types):
            return True
        return False

    def resolve(self, enabled_container_types, tool_info, **kwds):
        container_description = self._container_description(self.identifier, self.container_type)
        if self._match(enabled_container_types, tool_info, container_description):
            return container_description


class FallbackSingularityContainerResolver(FallbackContainerResolver):
    """Specify an explicit, identified container as a Singularity container resolver."""

    resolver_type = "fallback_singularity"
    container_type = 'singularity'


class FallbackNoRequirementsContainerResolver(FallbackContainerResolver):

    resolver_type = "fallback_no_requirements"

    def _match(self, enabled_container_types, tool_info, container_description):
        type_matches = super()._match(enabled_container_types, tool_info, container_description)
        return type_matches and (tool_info.requirements is None or len(tool_info.requirements) == 0)


class FallbackNoRequirementsSingularityContainerResolver(FallbackNoRequirementsContainerResolver):

    resolver_type = "fallback_no_requirements_singularity"
    container_type = 'singularity'


class RequiresGalaxyEnvironmentContainerResolver(FallbackContainerResolver):

    resolver_type = "requires_galaxy_environment"

    def _match(self, enabled_container_types, tool_info, container_description):
        type_matches = super()._match(enabled_container_types, tool_info, container_description)
        return type_matches and tool_info.requires_galaxy_python_environment


class RequiresGalaxyEnvironmentSingularityContainerResolver(RequiresGalaxyEnvironmentContainerResolver):

    resolver_type = "requires_galaxy_environment_singularity"
    container_type = 'singularity'


class MappingContainerResolver(BaseAdminConfiguredContainerResolver):
    resolver_type = "mapping"

    def __init__(self, app_info=None, **kwds):
        super().__init__(app_info, **kwds)
        mappings = self.resolver_kwds["mappings"]
        assert isinstance(mappings, list), "mapping container resolver must be specified with mapping list"
        self.mappings = mappings

    def resolve(self, enabled_container_types, tool_info, **kwds):
        tool_id = tool_info.tool_id
        # If resolving against dependencies and not a specific tool, skip over this resolver
        if not tool_id:
            return

        tool_version = tool_info.tool_version

        for mapping in self.mappings:
            if mapping.get("tool_id") != tool_id:
                continue

            mapping_tool_version = mapping.get("tool_version")
            if mapping_tool_version is not None and tool_version != mapping_tool_version:
                continue

            container_description = self._container_description(mapping["identifier"], mapping.get("container_type"))
            if not self._container_type_enabled(container_description, enabled_container_types):
                continue
            return container_description


__all__ = (
    "ExplicitContainerResolver",
    "ExplicitSingularityContainerResolver",
    "FallbackContainerResolver",
    "FallbackSingularityContainerResolver",
    "FallbackNoRequirementsContainerResolver",
    "FallbackNoRequirementsSingularityContainerResolver",
    "MappingContainerResolver",
    "RequiresGalaxyEnvironmentContainerResolver",
    "RequiresGalaxyEnvironmentSingularityContainerResolver",
)
