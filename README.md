# eager_cache

Magical eager caching server.

Powered by fastapi.

Start a project with:

```bash
docker-compose -f deploy/docker-compose.yml --project-directory . up
```

## Pre-commit

To install pre-commit simply run inside the shell:

```bash
pre-commit install
```

## Kubernetes

To run your app in kubernetes
just run:

```bash
kubectl apply -f deploy/kube
```

It will create needed components.

If you haven't pushed to docker registry yet, you can build image locally.

```bash
docker-compose -f deploy/docker-compose.yml --project-directory . build
docker save --output eager_cache.tar eager_cache:latest
```

## Running tests

If you want to run it in docker, simply run:

```bash
docker-compose -f deploy/docker-compose.yml --project-directory . run --rm api pytest -vv .
docker-compose -f deploy/docker-compose.yml --project-directory . down
```

For running tests on your local machine.

2. Run the pytest.

```bash
pytest -vv .
```
