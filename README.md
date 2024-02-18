# easy

![CI Workflow](https://github.com/antibagr/easy/actions/workflows/makefile.yml/badge.svg?event=push)![coverage badge](./coverage.svg)

## Table of Contents

- [easy](#easy)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Poetry](#poetry)
    - [Dependencies](#dependencies)
    - [Run](#run)
      - [Dev](#dev)
      - [Production](#production)
  - [Usage](#usage)
  - [Development](#development)
    - [Linting](#linting)
    - [Running the Server](#running-the-server)
    - [Docker Compose](#docker-compose)
  - [Testing](#testing)
    - [Unit Tests](#unit-tests)
    - [Integration Tests](#integration-tests)
    - [All Tests](#all-tests)
  - [License](#license)

## Installation

> **Note for Windows Users:**
>
> If you are using Windows, it's important to ensure that you have Windows Subsystem for Linux (WSL) 2 installed and configured correctly before running the provided commands under a WSL terminal. WSL 2 provides a Linux-compatible environment that can be used for development tasks.
>
> To install and set up WSL 2 on your Windows machine, please follow the official Microsoft documentation: [Install Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install).
>
> Once WSL 2 is set up, make sure to use the WSL terminal for running the commands specified in this documentation for a seamless development experience.
>
> If you encounter any issues related to WSL or need further assistance, please refer to the Microsoft WSL documentation or seek support from the WSL community.

### Poetry

Install poetry using your package manager or [official guide](https://python-poetry.org/docs/#installation). (Project was maintained mostly with `1.6.1`)

### Dependencies

The easiest way to install required and dev dependencies is as follows:

```bash
make install
```

1. **Create a `.env` File:**

    - Create a `.env` file in the root directory of your project if it doesn't already exist.

2. **Open the `.env` File:**

    - Open the `.env` file using a text editor of your choice.

3. **Define Environment Variables:**

    - Inside the `.env` file, define the following environment variables, providing values specific to your project
4. **Save the `.env` File:**

    - Save the changes to the `.env` file.

### Run

#### Dev

To run development server run:

```bash
make run
```

Now you can check your [localhost:8888](http://localhost:8888)

#### Production

To run production server on the local machine:

1. Install Docker Compose following the [official guide](https://docs.docker.com/compose/install/).
2. Build and run all containers locally:

```bash
make compose-up
```

Now you can check your [localhost:8000](http://localhost:8000)

## Usage

Describe how to use your app here.

## Development

Formatting
To format the source code, run:

```bash
make format
```

### Linting

To lint the source code, run:

```bash
make lint
```

### Running the Server

To run the development server, use:

```bash
make run
```

### Docker Compose

To run the development server with Docker Compose, use:

```bash
make compose-up
```

To stop the development server with Docker Compose, use:

```bash
make compose-down
```

## Testing

### Unit Tests

To run unit tests, use:

```bash
make tests-units
```

### Integration Tests

To run integration tests, use:

```bash
make tests-integrations
```

### All Tests

To run all available tests, use:

```bash
make test
```

## License

This project is licensed under the [GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/) License - see the [LICENSE](./LICENCE) file for details.

payment_method
deposit_amount
user_id
