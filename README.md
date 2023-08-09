## Test task: "JSON-objects storage service designed to work in Kubernetes cloud environment"

## Problem statement:

Develop a service designed to work in a cloud environment (Kubernetes). The service is a storage of JSON-objects with HTTP-interface. Stored objects are placed in RAM, it is possible to set object lifetime.

## Service features:

* Writing objects to the storage
* Reading objects from storage
* Support for standard HTTP liveness and readiness validation methods for integration with k8s
* Obtaining metrics in prometheus format
* Storing data on disc and restoring the storage state from a file when the application is started


## Building and running

There are a total of three quick ways to get your project up and running:

1. Using the Poetry package manager
2. Using docker-compose
3. Using k8s

### Method 1. Poetry

1. Use the commands:

    ```> cp example.env .env```

    ```> poetry install```

    ```> poetry shell```
   
    ```> poetry run start```

3. Go to ```http://localhost:8000/docs``` to view and use the endpoints

### Method 2. Docker Compose

1. Use the command

    ```> cp example.env .env```

2. Use docker compose to build an image

    ```> docker-compose build```

3. Run docker compose up to start the application

    ```> docker-compose up```

4. Go to ```http://localhost:8000/docs``` to view and use the endpoints

### Method 3. k8s

1. Use the commands:

    ```> cd k8s/```

    ```> kubectl apply -f namespace```

    ```> kubectl apply -f fastapi```

2. Make sure that pod has been started with the command

    ```> kubectl get pods -n fastapi-storage-service```

3. Go to ```http://localhost:31001/docs``` to view and use the endpoints


## Tests:

To run the tests, load the dependencies using the poetry package manager and run the command `> pytest`
