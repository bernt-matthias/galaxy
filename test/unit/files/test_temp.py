import tempfile
from typing import List

import pytest

from galaxy.files.plugins import FileSourcePluginsConfig
from galaxy.files.sources.temp import TempFilesSource
from galaxy.files.unittest_utils import (
    setup_root,
    TestConfiguredFileSources,
)
from ._util import (
    assert_realizes_contains,
    user_context_fixture,
)

ROOT_URI = "temp://test1"
TEMP_PLUGIN = {
    "type": "temp",
    "id": "test1",
    "doc": "Test temporal file source",
    "writable": True,
}


@pytest.fixture(scope="session")
def file_sources() -> TestConfiguredFileSources:
    file_sources = _configured_file_sources()
    return file_sources


@pytest.fixture(scope="session")
def temp_file_source(file_sources: TestConfiguredFileSources) -> TempFilesSource:
    file_source_pair = file_sources.get_file_source_path(ROOT_URI)
    file_source = file_source_pair.file_source
    return file_source


def test_file_source(file_sources: TestConfiguredFileSources):
    assert_realizes_contains(file_sources, f"{ROOT_URI}/a", "a")
    assert_realizes_contains(file_sources, f"{ROOT_URI}/b", "b")
    assert_realizes_contains(file_sources, f"{ROOT_URI}/c", "c")
    assert_realizes_contains(file_sources, f"{ROOT_URI}/dir1/d", "d")
    assert_realizes_contains(file_sources, f"{ROOT_URI}/dir1/e", "e")
    assert_realizes_contains(file_sources, f"{ROOT_URI}/dir1/sub1/f", "f")


def test_list(temp_file_source: TempFilesSource):
    assert_list_names(temp_file_source, "/", recursive=False, expected_names=["a", "b", "c", "dir1"])
    assert_list_names(temp_file_source, "/dir1", recursive=False, expected_names=["d", "e", "sub1"])


def test_list_recursive(temp_file_source: TempFilesSource):
    expected_names = ["a", "b", "c", "dir1", "d", "e", "sub1", "f"]
    assert_list_names(temp_file_source, "/", recursive=True, expected_names=expected_names)


def test_pagination(temp_file_source: TempFilesSource):
    # Pagination is only supported for non-recursive listings.
    recursive = False
    root_lvl_entries = temp_file_source.list("/", recursive=recursive)
    assert len(root_lvl_entries) == 4

    # Get first entry
    result = temp_file_source.list("/", recursive=recursive, limit=1, offset=0)
    assert len(result) == 1
    assert result[0] == root_lvl_entries[0]

    # Get second entry
    result = temp_file_source.list("/", recursive=recursive, limit=1, offset=1)
    assert len(result) == 1
    assert result[0] == root_lvl_entries[1]

    # Get second and third entry
    result = temp_file_source.list("/", recursive=recursive, limit=2, offset=1)
    assert len(result) == 2
    assert result[0] == root_lvl_entries[1]
    assert result[1] == root_lvl_entries[2]

    # Get last three entries
    result = temp_file_source.list("/", recursive=recursive, limit=3, offset=1)
    assert len(result) == 3
    assert result[0] == root_lvl_entries[1]
    assert result[1] == root_lvl_entries[2]
    assert result[2] == root_lvl_entries[3]


def test_search(temp_file_source: TempFilesSource):
    # Search is only supported for non-recursive listings.
    recursive = False
    root_lvl_entries = temp_file_source.list("/", recursive=recursive)
    assert len(root_lvl_entries) == 4

    result = temp_file_source.list("/", recursive=recursive, query="a")
    assert len(result) == 1
    assert result[0]["name"] == "a"

    result = temp_file_source.list("/", recursive=recursive, query="b")
    assert len(result) == 1
    assert result[0]["name"] == "b"

    result = temp_file_source.list("/", recursive=recursive, query="c")
    assert len(result) == 1
    assert result[0]["name"] == "c"

    # Searching for 'd' at root level should return the directory 'dir1' but not the file 'd'
    # as it is not a direct child of the root.
    result = temp_file_source.list("/", recursive=recursive, query="d")
    assert len(result) == 1
    assert result[0]["name"] == "dir1"

    # Searching for 'e' at root level should not return anything.
    result = temp_file_source.list("/", recursive=recursive, query="e")
    assert len(result) == 0

    result = temp_file_source.list("/dir1", recursive=recursive, query="e")
    assert len(result) == 1
    assert result[0]["name"] == "e"


def _populate_test_scenario(file_source: TempFilesSource):
    """Create a directory structure in the file source."""
    user_context = user_context_fixture()

    _upload_to(file_source, "/a", content="a", user_context=user_context)
    _upload_to(file_source, "/b", content="b", user_context=user_context)
    _upload_to(file_source, "/c", content="c", user_context=user_context)
    _upload_to(file_source, "/dir1/d", content="d", user_context=user_context)
    _upload_to(file_source, "/dir1/e", content="e", user_context=user_context)
    _upload_to(file_source, "/dir1/sub1/f", content="f", user_context=user_context)


def _upload_to(file_source: TempFilesSource, target_uri: str, content: str, user_context=None):
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(content)
        f.flush()
        file_source.write_from(target_uri, f.name, user_context=user_context)


def assert_list_names(file_source: TempFilesSource, uri: str, recursive: bool, expected_names: List[str]):
    result = file_source.list(uri, recursive=recursive)
    assert sorted([entry["name"] for entry in result]) == sorted(expected_names)
    return result


def _configured_file_sources() -> TestConfiguredFileSources:
    tmp, root = setup_root()
    file_sources_config = FileSourcePluginsConfig()
    plugin = TEMP_PLUGIN
    plugin["root_path"] = root
    file_sources = TestConfiguredFileSources(file_sources_config, conf_dict={TEMP_PLUGIN["id"]: plugin}, test_root=root)
    _populate_test_scenario(file_sources.get_file_source_path(ROOT_URI).file_source)
    return file_sources
