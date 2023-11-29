#!/usr/bin/python
from configparser import ConfigParser


def read_config(filename="config.ini", section="postgresql"):
    """Read config file"""
    config = ConfigParser()
    config.read(filename)

    db = {}
    if config.has_section(section):
        params = config.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f"Section {section} not found in the {filename} file")

    return db


def update_config(key, value, filename="config.ini", section="tracker"):
    """update config file"""
    config = ConfigParser()
    config.read(filename)

    if section not in config:
        config[section] = {}
    config[section][key] = value

    with open(filename, "w") as configfile:
        config.write(configfile)
