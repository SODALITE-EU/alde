#
# Copyright 2018 Atos Research and Innovation
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# https://www.gnu.org/licenses/agpl-3.0.txt
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
# 
# This is being developed for the TANGO Project: http://tango-project.eu
#
# Flask application initialization and config loading
#


# Main ALDE Falsk start app...

import argparse
import configparser
import os
import sys
import alde # pragma: no cover
import logging # pragma: no cover
import file_upload.upload as upload
from logging.config import fileConfig # pragma: no cover
from models import db # pragma: no cover

# Loading logger configuration
fileConfig('logging_config.ini') # pragma: no cover
logger = logging.getLogger() # pragma: no cover

def load_config(configpath):
    """
    Functions that loads ALDE configuration from file
    It is specting a file alde_configuration.ini in the same location
    than the main executable
    """

    logger.info("Loading configuration %s", configpath)
    config = configparser.ConfigParser()
    config.read(configpath)
    default = config['DEFAULT']
    
    options = [
        'SQL_LITE_URL',
        'HOST',
        'PORT',
        'APP_UPLOAD_FOLDER',
        'APP_PROFILE_FOLDER',
        'APP_TYPES',
        'COMPARATOR_PATH',
        'COMPARATOR_FILE',
        'APP_TYPES'
    ]

    conf = { opt: os.getenv(opt, default[opt]) for opt in options }
    conf['APP_TYPES'] = [e.strip() for e in conf['APP_TYPES'].split(',')]

    return conf

def log_config(conf):
    msg = "\n".join([ "\t{} = {}".format(key, conf[key]) for key in conf.keys() ])
    logger.info("ALDE configuration:\n%s\n", msg)

def main(): # pragma: no cover
    """
    Main function that starts the ALDE Flask Service
    """
    parser = argparse.ArgumentParser(description='Application Lifecycle Deployment Engine')
    parser.add_argument('--config', type=str, default='alde_configuration.ini', help='configuration file path')
    args = parser.parse_args()

    conf = load_config(args.config) # pragma: no cover
    log_config(conf)

    logger.info("Starting ALDE") # pragma: no cover
    app = alde.create_app_v1(conf['SQL_LITE_URL'], 
                             conf['PORT'], 
                             conf['APP_UPLOAD_FOLDER'], 
                             conf['APP_PROFILE_FOLDER'], 
                             conf['APP_TYPES'],
                             conf['COMPARATOR_PATH'],
                             conf['COMPARATOR_FILE'] ) # pragma: no cover

    # We start the Flask loop
    db.create_all() # pragma: no cover

    # We register the upload url
    upload_prefix = alde.url_prefix_v1 + "/upload"
    app.register_blueprint(upload.upload_blueprint, url_prefix=upload_prefix)

    app.run(host=conf['HOST'], port=conf['PORT'], use_reloader=False)

if __name__ == '__main__':
    main()
