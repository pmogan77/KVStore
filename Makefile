# KVStore Makefile

# Build the Docker image
build:
	docker build -t kvstore-app .

# Run the Flask API
run:
	docker run -d -p 5000:5000 --name kvstore-app kvstore-app

# Stop and remove the running container
stop:
	docker stop kvstore-app || true
	docker rm kvstore-app || true

# Run unit tests inside Docker
test:
	docker run --rm kvstore-app pytest test_store.py -v

# Run a shell inside the container (for debugging)
shell:
	docker run --rm -it kvstore-app /bin/bash
