# Cloud Storage

## Getting started

### Install the App
Clone the repository:

```sh
$ git clone https://github.com/akimovatatiana/CloudStorage.git
$ cd CloudStorage
```
Install `virtualenv` by [following guide](https://gist.github.com/Geoyi/d9fab4f609e9f75941946be45000632b), if you don’t already have it.
Create a virtual environment to install dependencies in and activate it:

```sh
$ virtualenv --no-site-packages env
$ source env/bin/activate
```

Then install the dependencies:

```sh
(venv)$ pip install -r requirements.txt
```
Note the `(venv)` in front of the prompt. This indicates that this terminal
session operates in a virtual environment set up by `virtualenv`.

### Setting up PostgreSQL
Now we need to setup `PostgreSQL`. Download and install from [official download page]((https://gist.github.com/Geoyi/d9fab4f609e9f75941946be45000632b)).

Database already defined in `cloud_storage/settings.py` file:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cloud_storage',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

Setup database by following command (make sure you are at the same level as `manage.py`):
```sh
(venv)$ python manage.py migrate
```

### Setting up the cache
CloudStorage use `Redis` to store application cache.

Download and install `Redis` using the instructions provided in the [documentation](https://redis.io/topics/quickstart). Alternatively, you can install Redis using a package manager such as apt-get or homebrew depending on your OS.

Run the Redis server from a new terminal window.

```sh
$ redis-server
```

Next, start up the Redis command-line interface (CLI) in a different terminal window and test that it connects to the Redis server. We will be using the Redis CLI to inspect the keys that we add to the cache.

```sh
$ redis-cli ping
PONG
```


In Django App cache already definied in `cloud_storage/settings.py`

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": "redis"
    }
}

CACHE_TTL = 60 * 15
```

`CACHE_TTL` -- cache timeout in seconds (60 * 15 sec = 15 minutes)




### Run CloudStorage
Run server by following command:
```sh
(venv)$ python manage.py runserver
```
And navigate to `http://127.0.0.1:8080/home`.
