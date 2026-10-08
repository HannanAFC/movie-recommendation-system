# Python Movie Recommendation System

## Table of Contents
- [Introduction](#introduction)
- [Setting up the development environemnt](#setting-up-the-development-environemnt)
    - [Prerequisites](#prerequisites)
    - [Cloning the repository](#cloning-the-repository)
        - [Without Git](#without-git)
        - [With Git](#with-git)
    - [Run docker compose](#run-docker-compose)
    - [Adding dependencies](#adding-dependencies)

## Introduction
The aim of this project is to develop a system which utilises machine learning to provide users with movie recommendations based on their preferences and historical movie ratings.

## Setting up the development environemnt
This section will act as a guide for setting up the development environment.

### Prerequisites
- WSL installed if on Windows.
- Docker installed.
- uv (if you want to add dependencies).

### Cloning the repository
To clone the repository, you have two options:

#### Without Git:
1. Click the green `<> Code` button and click `Download ZIP`.
2. Once downloaded, extract the file contents into the desired location.
3. Open the folder in your code editor of choice to view the code if desired.

#### With Git:
```shell
# Open the terminal for MacOS or Linux, or the Command Prompt or PowerShell for Windows.

# Navigate to the directory you want the project folder to be contained in

# MacOS and Linux
cd a_folder/path_to_parent_folder

# Windows
cd a_folder\path_to_parent_folder

# Clone the repository
git clone https://github.com/HannanAFC/movie-recommendation-system
```

### Run docker compose
Open the project in VS Code, then open a terminal window. Here you can type `docker compose up` which will start the compose stack. This will setup the application and download any required dependencies. Once the build finishes, you can access the application at http://localhost:5173

### Adding dependencies
If you need to add dependencies, navigate to the `api` directory and simply run:
```shell
uv add <package name>
```
This will install the dependency locally and also add it to ```pyproject.toml```, you may need to rebuild the docker container using `docker compose up --build`.