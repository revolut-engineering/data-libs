# Dicts

An API for manipulating `Dicts` where `Dicts = List[dict]`

`Dicts` assumes you have a set of dictionaries which share a structure, such as a `jsonschema`.
This library aims to simplify common operations that might need to be performed on lists of dictionaries.

`Dicts` doesn't care where your data is your sourced from. You can load from

 - A `json` or `yaml` file
 - A directory
 - An object of `List[dict]`

## Usage

Say we have a configuration file `animals.yaml`

```yaml
- name: Zebra
  speed: 13
  lifespan: 20
  diet: grass

---

- name: Lion
  speed: 23
  lifespan: 32
  diet: meat
```

Then, with `revlibs.dicts` we can load the config as

```python
from pathlib import Path
from revlibs.dicts import Dicts

loader = Dicts.from_path(Path("connections.yaml"))
list(loader.items)
```

This outputs

```python
[{'__PATH__': '/resolved/path/to/animals.yaml',
  'diet': 'grass',
  'lifespan': 20,
  'name': 'Zebra',
  'speed': 13},
 {'__PATH__': '/resolved/path/to/animals.yaml',
  'diet': 'meat',
  'lifespan': 32,
  'name': 'Lion',
  'speed': 23}]
```

## Options

The loader can be configured, and the items can be manipulated in a variety of ways.

```python
> data = [
    {"animal": "cat", "size": 100},
    {"animal": "dog", "size": 100},
    {"animal": "rat", "size": 1},
    {"animal": "pig", "colour": "pink"},
    {"animal": "bat", "size": 5, "disabled": True},
]
```

Normal usage

```python
> Dicts.from_dicts(data).items
[{'animal': 'cat', 'size': 100},
 {'animal': 'dog', 'size': 100},
 {"animal": "pig", "colour": "pink"},
 {'animal': 'rat', 'size': 1}]
```

The loader can be forced to load disabled entries. 

```python
> Dicts.from_dicts(data, load_disabled=True).items
[{'animal': 'cat', 'size': 100},
 {'animal': 'dog', 'size': 100},
 {'animal': 'rat', 'size': 1},
 {'animal': 'pig', 'colour': 'pink'},
 {'animal': 'bat', 'size': 5, 'disabled': True}]
```

Disabled entries are specified in the config file via the `disabled_key` argument.

```python
> Dicts.from_dicts(data, disabled_key='colour').items
[{'animal': 'cat', 'size': 100},
 {'animal': 'dog', 'size': 100},
 {'animal': 'rat', 'size': 1},
 {'animal': 'bat', 'size': '5', 'disabled': True}]
```

The data can be filtered by some arbitrary predicate function

```python
> def colourless(d):
>     return "colour" not in d

> Dicts.from_dicts(data).filter(colourless).items
[{'animal': 'cat', 'size': 100},
 {'animal': 'dog', 'size': 100},
 {'animal': 'rat', 'size': 1}]
```

The items can be cast by a function or class

```python
> class Animal:
>     def __init__(self, kwargs):
>         for k, v in kwargs.items():
>             setattr(self, k, v)
>
>     def __repr__(self):
>         return f"Animal('A {self.animal} who weighs {self.size}kg')"

> Dicts.from_dicts(data).filter(colourless).items_as(Animal).items
[Animal('A cat who weighs 100kg'),
 Animal('A dog who weighs 100kg'),
 Animal('A rat who weighs 1kg')]
```

## Keying

Mapping and keying should be the last step in a pipeline, and is a substitute to calling `.items`, to signal the end of the loader method chaining.

 - A key results in a `Dict[str, List[Any]]`
 - A map results in a `Dict[str, Any]`

This means that a map is a 1 - 2 - 1 mapping, between keys and objects, whilst keying a `Dicts` object will return a collection of objects that fit the key.

For example

```python
> def animal_size(animal: Animal):
>     return animal.size

> Dicts.from_dicts(data) \
>     .filter(colourless) \
>     .items_as(Animal) \
>     .key_by(animal_size, default="_")

{
    1: [
        Animal('A rat who weighs 1kg')
    ],
    100: [
        Animal('A cat who weighs 100kg'), 
        Animal('A dog who weighs 100kg')
    ]
}
```

And to enforce mapping

```python
> def light_animals(d):
>     return d.get("size", 100) < 100

> Dicts.from_dicts(data, load_disabled=True) \ 
>     .filter(light_animals) \ 
>     .items_as(Animal) \ 
>     .map_by(animal_size, default="_")

{
    1: Animal('A rat who weighs 1kg'), 
    5: Animal('A bat who weighs 5kg')
}
```
