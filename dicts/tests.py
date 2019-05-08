from pathlib import Path
import tempfile
import json
import pytest
from ruamel.yaml import YAML
from revlibs.dicts import PATH_KEY, DEFAULT_PATH_KEY, Dicts

yaml = YAML()


class Animal:
    def __init__(self, config):
        self.animal = config.get("animal")
        self.size = config.get("size")

    def __repr__(self):
        return f"Animal('A {self.animal} who weighs {self.size}kg')"

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.animal == other.animal and self.size == other.size
        return False


def create_dir(num_files, dict_generator, extensions):
    tmp_dir = tempfile.mkdtemp()
    p = Path(tmp_dir)
    for i in range(0, num_files):
        d = dict_generator(i)
        # last one should cause problems
        for extension, op in extensions:
            f_name = f"file_{i}.{extension}"
            with open(p / f_name, "w") as f:
                op(d, f)
    return p


@pytest.mark.parametrize(
    "generator,num_files,expected_size,extensions",
    [
        pytest.param(
            lambda i: {"a": i},
            5,
            2 * 5,
            [("yaml", yaml.dump), ("json", json.dump), ("txt", json.dump)],
            id="Test loading both json and yaml",
        ),
        pytest.param(
            lambda i: {"a": i},
            0,
            0,
            [("yaml", yaml.dump), ("json", json.dump), ("txt", json.dump)],
            id="Test with empty directory",
        ),
        pytest.param(
            lambda i: [{"a": i}, {"a": i}],
            5,
            4 * 5,
            [("yaml", yaml.dump), ("json", json.dump), ("txt", json.dump)],
            id="Test loading arrays of dicts",
        ),
        pytest.param(
            lambda i: [{"a": i}, {"a": i}],
            5,
            0,
            [("json", yaml.dump), ("txt", json.dump)],
            id="Test loading invalid json",
        ),
        pytest.param(
            lambda i: [{"a": i}, {"a": i}],
            5,
            2 * 5,
            [("yaml", yaml.dump_all)],
            id="Test loading multi part yaml",
        ),
    ],
)
def test_load_dicts(generator, num_files, expected_size, extensions):
    tmp_dir = create_dir(num_files, generator, extensions)
    loader = Dicts.from_path(tmp_dir, skip_errors=True)
    dicts = list(loader.items)
    assert len(dicts) == expected_size, "number of loaded files matches"
    for d in dicts:
        assert isinstance(d, dict)
        assert d, "loaded dict is not empty"
        assert "a" in d, "dict loaded correctly"
        assert d["a"] < num_files
    for f in tmp_dir.iterdir():
        f.unlink()
    tmp_dir.rmdir()


def test_to_dict_simple():
    a = [{"a": 1, PATH_KEY: "x"}]
    loader = Dicts.from_dicts(a)
    out = loader.map_by(key="a", default="_")
    assert isinstance(out, dict), "to_dict returns a dict"
    assert len(out) == 1
    assert out[a[0]["a"]] == a[0]


def test_to_dict_transform():
    a = [{"a": "aa", "b": "bb", PATH_KEY: "x"}]
    loader = Dicts.from_dicts(a)
    pick_b = lambda d: {"b": d["b"]}
    out = loader.items_as(pick_b).map_by(key="b", default="_")
    assert isinstance(out, dict), "to_dict returns a dict"
    assert len(out) == 1
    assert out == {"bb": {"b": "bb"}}


def test_group_by_unordered():
    a = [{PATH_KEY: "a"}, {PATH_KEY: "c"}, {PATH_KEY: "b"}, {PATH_KEY: "a"}]
    loader = Dicts.from_dicts(a)
    out = loader.key_by_file()
    assert len(out["a"]) == 2


def test_duplicate():
    a = [{"name": 1, PATH_KEY: "x"}, {"name": 1, PATH_KEY: "y"}]
    loader = Dicts.from_dicts(a)
    with pytest.raises(ValueError):
        loader.map_by(key="name", default="_")


def test_filter():
    loader = Dicts.from_dicts(
        [
            {"animal": "cat", "size": 100},
            {"animal": "dog", "size": 100},
            {"animal": "rat", "size": 1},
        ]
    )

    animal = loader.filter(lambda d: d["animal"] == "rat").map_by("animal", "_")
    assert animal == {"rat": {"animal": "rat", "size": 1}}


def test_cast_then_key():

    data = [
        {"animal": "cat", "size": "100"},
        {"animal": "dog", "size": "100"},
        {"animal": "rat", "size": "1"},
        {"animal": "bat", "size": "5", "disabled": True},
    ]

    def animal_size(animal: Animal):
        return animal.size

    result = Dicts.from_dicts(data).items_as(Animal).key_by(animal_size, "_")
    assert result["1"] == [Animal({"animal": "rat", "size": "1"})]
    assert result["100"] == [
        Animal({"animal": "cat", "size": "100"}),
        Animal({"animal": "dog", "size": "100"}),
    ]


def test_group_by_file():
    a = [
        {"name": 1, PATH_KEY: "x"},
        {"name": 1, PATH_KEY: "y"},
        {"name": 2, PATH_KEY: "y"},
        {"name": 2},
    ]
    loader = Dicts.from_dicts(a)
    out = dict(loader.key_by_file())
    assert out == {
        "x": [{"name": 1, PATH_KEY: "x"}],
        "y": [{"name": 1, PATH_KEY: "y"}, {"name": 2, PATH_KEY: "y"}],
        DEFAULT_PATH_KEY: [{"name": 2}],
    }
