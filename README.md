# Eager Cache

![Magic Shia Labeouf GIF](https://c.tenor.com/tvjxNL7PwHUAAAAC/magic-shia-labeouf.gif)al eager caching server.

Powered by [FastAPI](https://fastapi.tiangolo.com).

# Deploying

There is a dockerfile, dockercompose and k8s yamls.

Make sure you have a running [redis](https://redis.io) deployment, set to notify keyspace events:

```cmd
redis-cli config set notify-keyspace-events Ex
```

# What is eager caching?

Say you have some data that you need to serve to your users.
You decide to use a cache, but then you realise you need also to invalidate the cache after some time.
Another consideration you tak into account is serving your users with fresh information every time they want to access the data, using the cache.

Introducing eager-cache:
In its base, it's a FastAPI server that uses supplied fetchers in order to serve users with information they need.
It's actually a key-value store, storing cache in redis for each request (path+query) the value retrieved from the appropriate fetcher.

The magic is in the caching mechanism.
It uses redis in order to store the cached responses, and sets ttl for every cache record [using a shadow key](https://stackoverflow.com/a/28647773/938227) for each record.

There is a microservice that subscribes to keyspace events from the redis deployment and refetches the expired value using the fetcher.

# `DataItem`

In addition to storing the data, `DataItem` does two important things:

First, it stores the time the data itself was _fetched_ (this is `last_retrieved`).

Second, it stores the time the data itself was _changed_ (this is `last_modified`).

This way, you can always know when was the data fetched, but also when was it changed (the comparison is done using [deepdiff](https://pypi.org/project/deepdiff/))

![eager_cache_uml](https://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/liorp/eager_cache/master/uml/eager_cache.iuml)
