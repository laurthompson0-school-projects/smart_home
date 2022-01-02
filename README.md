# Smart Home Dashboard Simulator

This project is a web application using the React framework frontend, Flask backend, and PostgreSQL database. It is meant to simulate a smart-home application interface. The simulation runs 2 months of pre-generated events, as well as handling user-generated events in real time. The user can alter the state of lights, faucets, doors and windows, as well as view power and water usage data.

### Setting Things Up

**Please read [the other README](../README.md) before attempting this!**

#### `make init`

Run `make init` to set up the development environment.

Note: you will have to hit `Ctrl+C` after Docker is finished initializing the database.

### Running The App

#### `make start`

Run `make start` to start the application.

### Database Information

#### Local Development Database

By default, the app is set up to use a local Postgres database within Docker for development and testing purposes.

See the `LOCAL_POSTGRES_URL` variable in [constants.py](public/constants.py) for connection details.

#### Remote Demo Database

A Postgres database has been set up on a remote server to be used during the demo of this project.

See the `REMOTE_POSTGRES_URL` variable in [constants.py](public/constants.py) for connection details.

_Note that connecting to the remote server is only possible on UAB's network or through the UAB VPN._

##### Demo Preparation

Before demoing the project, run `./prepare_for_demo.sh` (see [the script](prepare_for_demo.sh)).

### App Documentation

Documentation about the app is stored under the [docs](docs) directory.
