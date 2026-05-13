# Program to build deb.ini config file
# The deb.ini file is utilized by all eclipse code
############################################################

from pathlib import Path
import sys
# Add this directory to python path
filedir = str(Path(__file__).parent)
if not filedir in sys.path:
    sys.path.append(filedir)

import configparser
import os

import unittest

# TODO versioning
DEBCONF_VERSION = 2
DC_DEBCONF_VERSION = 'debconf_version'
DC_PYTHON_VERSION = 'python_version'
DC_SEARCH_PATH = 'search_path'
DC_SIU_FOLDER = 'site_siu_folder'
DC_SIU_KEY = 'site_siu_ssh_key'
DC_SIU_HOST = 'siu_upload_host'
DC_SITE = 'SITE'

default_debconf_path = Path(os.getenv('USERPROFILE', os.getenv('HOME'))) / 'deb.ini'

class DebConfig(object):
    """Handle parameters for the DEB Initiative.

    The deb.ini consists of two required sections: DEFAULT and SITE
    The DEFAULT section contains the default values for the parameters.
    The SITE section provides a location for site specific parameters.

    The SITE section can specify

    XXX Would it be better to make this a superclass of configparser.ConfigParser?
    """
    def __init__(self, path=None, generate=True):
        """Read the deb.ini file and return a config object.

        If the file does not exist, and generate is true create it and add a default section.

        TODO How to make something which is relatively foolproof, i.e. can be changed?
        """
        self.config = configparser.ConfigParser()
        self.path = None

        path = path or str(default_debconf_path)
        config_path = self.config.read([str(path)])
        if config_path:
            self.path = config_path[0]
            if self.validate():
                return
            print(f'Bad config in {path}')
        self.set_config_to_default()
        self.path = path
        # We tried loading the path but it didn't exist, so generate a new one.
        self.save_config()


    def validate(self):
        config_version = self.getint(DC_DEBCONF_VERSION)
        if config_version < DEBCONF_VERSION:
            print(f'Found {DC_DEBCONF_VERSION} {config_version} wanted {DEBCONF_VERSION} in {self.path}')
            return False
        return True

    def set_config_to_default(self):
        self.config['DEFAULT'] = {
            DC_PYTHON_VERSION: 'python',
            'search_path': r'C:\Users',
            'filename': 'planetary_system_stacker.py',
            'output_format': 'png',
            'partial_ser_time': '15',
            'partial_interval_sec': '60',
            'down_size': 'True',
            'down_size_percent': '60',
            'deb_path': r'C:\DEB',
            'deb_programs': r'C:\DEB\Programs',
            DC_DEBCONF_VERSION : str(DEBCONF_VERSION),
            'siu_upload_host': '131.230.106.9'
            }
        self.config['SITE'] = {
            'comment': 'The "site" field can be used to point to persistent customizations.',
            'site': 'SITE',
            DC_SIU_FOLDER: 'xxxdeb',
            DC_SIU_KEY: 'DEB1_rsa',
        }
        self.config['FU_deb_test'] = {
            'site': 'FU_53',
            'site_id': '53',
            'site_name':'Castor Fu deb test',
            'deb_programs': r'C:\Users\Casto\src\debi-private',
            DC_SIU_FOLDER: '004deb',
            DC_SIU_KEY: 'id_deb004',
        }
        self.config['FU_deb_prod'] = {
            'site': 'FU_53',
            'site_id': '53',
            'site_name':'Castor Fu deb prod',
            DC_SIU_FOLDER: '004deb',
            DC_SIU_KEY: 'id_deb004',
        }
        self.config['FU_53_test'] = {
            'site': 'FU_53',
            'site_id': '53',
            'site_name':'Castor Fu home test',
            'deb_path' : r'D:\DEB',
            DC_SIU_FOLDER: '004deb',
            DC_SIU_KEY: 'id_deb004',
        }

    def get(self, option, site=None):
        site = site or self.config['SITE']['site']
        return self.config[site][option]

    def set_value(self, option, value, site=None):
        site = site or self.config['SITE']['site']
        self.config[site][option] = str(value)

    
    def generate_backup_name(self, path: Path) -> str:
        backups = [p for p in path.parent.glob(path.name + '.[0-9]')]
        vals = sorted([int(p.suffix[1:]) for p in backups])
        if vals:
            n = vals[-1] + 1
        else:
            n = 1
        newpath = f'{str(path)}.{n}'
        if Path(newpath).exists():
            raise NotImplemented(f'Too many backups for {path}')
        return newpath

    def save_config(self):
        """move existing config to deb.ni.n, and save"""
        p = Path(self.path)
        if p.exists():
            pnew = self.generate_backup_name(p)
            print(f'backing up {self.path} to {pnew}')
            p.rename(pnew) # TODO improve this
        print(f'Saving config: {self.path}')
        with open(self.path, 'w') as configfile:
            self.config.write(configfile)

    def getboolean(self, option, site=None):
        site = site or self.config['SITE']['site']
        return self.config[site].getboolean(option)

    def getfloat(self, option, site=None, default=None):
        site = site or self.config['SITE']['site']
        value = self.config[site].getfloat(option)
        if value is None:
            value = default
        return value

    def getint(self, option, site=None, default=None):
        site = site or self.config['SITE']['site']
        value = self.config[site].getint(option)
        if value is None:
            value = default
        return value

    def data_path(self):
        '''Top level directory where DEB data should be stored '''
        return Path(self.get('deb_path'))

    def upload_dir(self):
        '''Directory where files to be uploaded should be placed'''
        return self.data_path() / 'Upload'

    def upload_workpath(self):
        '''Returns path to file containing name of files to upload.'''
        return self.upload_dir() / 'new.txt'

    def upload_endpath(self):
        '''Returns path to file used to signal end of uploading.'''
        return self.upload_dir() / 'end.txt'

class TestConfig(unittest.TestCase):
    def test_load_bad_path(self):
        """Config should return a usable config even if provided a bad config."""
        config = DebConfig('NotAPath')
        self.assertEqual(config.get('SITE'), 'SITE')

    def test_getint(self):
        config = DebConfig('NotAPath')
        self.assertEqual(config.getint(DC_DEBCONF_VERSION), DEBCONF_VERSION)


if __name__ == "__main__":
    config = DebConfig()
    print(f'Deb Config in {config.path}')
    print(f'User: {config.get(DC_SIU_FOLDER)}@{config.get(DC_SIU_HOST)}')
    print(f'keyfile: {config.get(DC_SIU_KEY)}')
    print(f'Python: {config.get(DC_PYTHON_VERSION)} PSS search: {config.get(DC_SEARCH_PATH)}')

