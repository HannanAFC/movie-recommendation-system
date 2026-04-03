# Python Movie Recommendation System

## Table of Contents
- [Introduction](#introduction)
- [Setting up the development environemnt](#setting-up-the-development-environemnt)
    - [Prerequisites](#prerequisites)
    - [Cloning the repository](#cloning-the-repository)
        - [Without Git](#without-git)
        - [With Git](#with-git)
    - [Open in Dev Container](#open-in-dev-container)
    - [Adding dependencies](#adding-dependencies)
- [Usage](#usage)

## Introduction
The aim of this project is to develop a system which utilises machine learning to provide users with movie recommendations based on their preferences and historical movie ratings.

## Setting up the development environemnt
This section will act as a guide for setting up the development environment.

### Prerequisites
- WSL installed if on Windows.
- Docker installed.
- Dev Containers VS Code extension installed.

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

### Open in Dev Container
Open the project in VS Code, it should prompt you to "Reopen in Dev Container" which you should select, if the option doesn't appear, click the icon in the bottom left of the window.

Once the project is opened in the Dev Container, it will automatically install any dependencies needed via the Poetry package manager. Just make sure to select the Python environment in Poetry as the interpreter, this can be done by searching ```>Python: Select Interpreter``` in the search bar at the top of the VS Code window and selecting the Python 3.14.0 option which has ```pypoetry``` in its path. Once this is done you can run the code.

### Adding dependencies
If you need to add dependencies, simply run:
```shell
poetry add <package name>
```
This will install the dependency locally and also add it to ```pyproject.toml```, remember to push the update of this file as it contains the dependencies that need to be installed on subsequent Dev Container start ups.

## Usage

To run the application, you will need to open a terminal instance. Before running any commands, make sure that the python env has been automatically set to the one inside the project. before the ```root``` text in the terminal, you should see ```(movie-recommendation-system-py3.14)```. If this isn't here wait up to 30 seconds and it should eventually appear. If not type ```cd api``` then ```poetry env activate```. This will ouput a command you can use to set the env manually.

In the terminal, inside of the api folder, run ```pnpm run db```, this will initialise the database.

In another terminal window, from the root (not inside ```api/```), run the command ```pnpm run api```. This will start the flask backend, make sure the env is also set in this terminal.

Inside another terminal window, run ```pnpm run dev```, this will start the frontend. You should see an output in the terminal with a URL address. Open this address in your browser and you should be greeted with the application. You can start using the application from here!

If you need to clean the application so you can start fresh, run ```pnpm run clean```, this will delete the datasets, database, remove the trained collaborative model and also remove the search index.