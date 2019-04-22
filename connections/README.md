<h1 align="center">
    Revlibs Connections
</h1>

<h4 align="center">
    Get connected instantly to a predefined set of databases, regardless of their type and nature.
</h4>

## Install

```
pip install revlibs-connections
```

## Usage

```python

from revlibs import connections

with connections.get("sandboxdb") as conn:
    conn.execute(query)
```

### Connections

This connection library will use the 'yaml/json' connections specified in the directory `~/.revconnect/`.
If you would like to specify a different path.

```
- .revconnect/
    ├ connections.yaml
    └ connections.json
```

#### E.g:

You may specify a different config directory by passing it in the `get` method.

```python
path = "/home/sebastien/.connections/"
with connections.get("sandboxdb", config_path=path) as conn:
    conn.execute(query)
```

#### Config

Config parameters prefixed with `_env:TEST_ENV` will use the environment variable
specified, in this case `TEST_ENV`.
A default value can be specified after a second colon, for example:
`_env:TEST_ENV:prod` will use `prod` if `TEST_ENV` is not set.

#### Config parameters

| **Parameter** | **Description** | **example** |
| ------------- | --------------- | ----------- |
| `name` | Unique name identifying database | `sandbox_db` |
| `flavour` | Specifying the DB implementation | `postgres` |
| `dsn` | Data source name | `<host:port>` |
| `user` | Username for the database | `user` |
| `password` | Password to the database | `_env:DATABASE_PASSWORD` |
| `dbname` | Name of database (specific to postgres) | `countries` |
| `schema` | Name of schema (specific to exasol) | `transactions` |
| `params` | Optional parameters to provide the connection. | `params: {timeout: 5}` |

#### An example of this file is provided below

We can have multiple connections in a single file.

*Note:* We have enforced taking the `password` from the environment.

```yaml
# Postgres Example
- name: sandboxdb
  flavour: postgres
  # We can specify multiple <host:port> combinations.
  # To simplfy this you may also provide
  # '127.0.0.1..3:8888' which will attempt sequential
  # connectiosn from '.1' -> '.3'
  dsn: 127.0.0.1:8888,127.0.0.1:8889
  user: postgres
  # Specifying the environment variable
  password: _env:SANDBOXDB_PASSWORD
  dbname: countries

# Exasol example
- name: bigdb
  flavour: exasol
  dsn: _env:BIG_DB_DSN
  user: default_user
  password: _env:BIGDB_PASSWORD
  schema: events
```

Ensure you have no collision with environment variables by prefixing
your environment connection parameters with your connection name. E.g.
the env var for the sandboxdb will be called `SANDBOXDB_PASSWORD`.
