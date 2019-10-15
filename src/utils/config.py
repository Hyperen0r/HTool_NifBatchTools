#!/usr/bin/python3
# -*- coding: utf-8 -*-

import configparser
import os

DEFAULT_CONFIG_FILE = "htool.ini"


def create_config():
    """
    Create default config file
    :return: default config object
    """
    config = configparser.ConfigParser()

    config['DEFAULT'] = {
        "sourceFolder": "",
        "softLimit": "100"
    }

    config["NIF"] = {
        "keywords" : "UUNP, FemaleHead, Hands, Feet, CL0, CL1",
        "glossiness": "450",
        "specularStrength": "3.5"
    }

    config["LOG"] = {
        "enabled": "True",
        "level": "INFO"
    }

    with open(DEFAULT_CONFIG_FILE, 'w') as config_file:
        config.write(config_file)

    return config


def load_config():
    """
    Load config from file. If it does not exist, it creates it.
    :return: config object
    """
    if not os.path.exists(DEFAULT_CONFIG_FILE):
        config = create_config()
    else:
        config = configparser.ConfigParser()
        config.read(DEFAULT_CONFIG_FILE)
    return config


CONFIG = load_config()


def get_config():
    """
    :return: config object
    """
    return CONFIG


def save_config():
    """ Save configuration in a file """
    with open(DEFAULT_CONFIG_FILE, 'w') as config_file:
        get_config().write(config_file)
