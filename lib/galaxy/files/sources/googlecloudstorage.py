try:
    from fs_gcsfs import GCSFS
    from google.cloud.storage import Client
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
except ImportError:
    GCSFS = None

import os
from typing import (
    Optional,
    Union,
)

from galaxy.files.models import FilesSourceRuntimeContext
from galaxy.files.sources._fsspec import (
    CacheOptionsDictType,
    FsspecBaseFileSourceConfiguration,
    FsspecBaseFileSourceTemplateConfiguration,
    FsspecFilesSource,
)
from galaxy.util.config_templates import TemplateExpansion
from ._pyfilesystem2 import PyFilesystem2FilesSource


class GoogleCloudStorageFileSourceTemplateConfiguration(BaseFileSourceTemplateConfiguration):
    bucket_name: Union[str, TemplateExpansion]
    root_path: Union[str, TemplateExpansion, None] = None
    project: Union[str, TemplateExpansion, None] = None
    anonymous: Union[bool, TemplateExpansion, None] = True
    service_account_json: Union[str, TemplateExpansion, None] = None
    token: Union[str, TemplateExpansion, None] = None
    token_uri: Union[str, TemplateExpansion, None] = None
    client_id: Union[str, TemplateExpansion, None] = None
    client_secret: Union[str, TemplateExpansion, None] = None
    refresh_token: Union[str, TemplateExpansion, None] = None


class GoogleCloudStorageFileSourceConfiguration(BaseFileSourceConfiguration):
    bucket_name: str
    root_path: Optional[str] = None
    project: Optional[str] = None
    anonymous: Optional[bool] = True
    service_account_json: Optional[str] = None
    token: Optional[str] = None
    token_uri: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None


class GoogleCloudStorageFilesSource(
    PyFilesystem2FilesSource[
        GoogleCloudStorageFileSourceTemplateConfiguration, GoogleCloudStorageFileSourceConfiguration
    ]
):
    plugin_type = "googlecloudstorage"
    required_module = GCSFS
    required_package = "fs-gcsfs"

    template_config_class = GoogleCloudStorageFileSourceTemplateConfiguration
    resolved_config_class = GoogleCloudStorageFileSourceConfiguration

    def _open_fs(self, context: FilesSourceRuntimeContext[GoogleCloudStorageFileSourceConfiguration]):
        if GCSFS is None:
            raise self.required_package_exception

        config = context.config
        if config.anonymous:
            client = Client.create_anonymous_client()
        elif config.service_account_json:
            credentials = service_account.Credentials.from_service_account_file(config.service_account_json)
            client = Client(project=config.project, credentials=credentials)
        elif config.token:
            client = Client(
                project=config.project,
                credentials=Credentials(
                    token=config.token,
                    token_uri=config.token_uri,
                    client_id=config.client_id,
                    client_secret=config.client_secret,
                    refresh_token=config.refresh_token,
                ),
            )

        fs = GCSFileSystem(
            project=config.project,
            token=token,
            **cache_options,
        )
        return fs

    def _to_filesystem_path(self, path: str, config: GoogleCloudStorageFileSourceConfiguration) -> str:
        """Convert an entry path to the GCS filesystem path format."""
        bucket = config.bucket_name
        root = (config.root_path or "").strip("/")
        if path.startswith("/"):
            path = path[1:]
        if root and path:
            return f"{bucket}/{root}/{path}"
        elif root:
            return f"{bucket}/{root}"
        elif path:
            return f"{bucket}/{path}"
        return bucket

    def _adapt_entry_path(self, filesystem_path: str, config: GoogleCloudStorageFileSourceConfiguration) -> str:
        """Remove the GCS bucket name and root_path from the filesystem path."""
        if config.bucket_name:
            bucket = config.bucket_name
            root = (config.root_path or "").strip("/")
            full_prefix = f"{bucket}/{root}" if root else bucket
            if filesystem_path == full_prefix:
                return "/"
            return "/" + filesystem_path.removeprefix(f"{full_prefix}/")
        return "/" + filesystem_path

    def score_url_match(self, url: str):
        bucket_name = self.template_config.bucket_name
        # For security, we need to ensure that a partial match doesn't work
        if bucket_name and (url.startswith(f"gs://{bucket_name}/") or url == f"gs://{bucket_name}"):
            return len(f"gs://{bucket_name}")
        elif bucket_name and (url.startswith(f"gcs://{bucket_name}/") or url == f"gcs://{bucket_name}"):
            return len(f"gcs://{bucket_name}")
        else:
            return super().score_url_match(url)


__all__ = ("GoogleCloudStorageFilesSource",)
