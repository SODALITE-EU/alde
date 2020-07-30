#
# Copyright 2020 Atos Research and Innovation
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
# This is being developed for the SODALITE Project: http://sodalite.eu
#

#
# Module that has all the logic to talk with TORQUE
#

import re
import shell
import copy
import query
import logging
import linux_probes.cpu_info_parser as parser
import inventory
import xmltodict
import executor_common
from models import db, Testbed, Node, CPU, GPU, Memory, Execution, Testbed, Executable
from typing import Dict, List, Tuple

from testbeds.constants import NAME
from testbeds.constants import MEMORY
from testbeds.constants import STATE
from testbeds.constants import GRES

import testbeds.common


_NAME = "node_name"
_STATE = "state"
_STATUS = "status"
_GPU_STATUS = "gpu_status"
_PARSED_STATUS = "parsed_status"
_PARSED_GPU_STATUS = "parsed_gpu_status"
_GPU_MODEL = "gpu_product_name"
_TOTAL_MEM = "totmem"


def get_nodes_testbed(testbed: Testbed) -> List[dict]:
    """
    This function gets the testbed object information, from that information
    it determines if the testbed it is of the category TORQUE.

    If it is TORQUE, it will determine if it connects via ssh.

        If it connects via ssh it will get the node info executing the command
        via ssh

        If it is not ssh, it will execute directly the sinfo command in console.

    If it is not type TORQUE it will just return an empty list
    """
    command = "pbsnodes"
    params = ["-x"]

    return testbeds.common.get_nodes_testbed(testbed, command, params, _parse_pbsnodes_information)


def _parse_pbsnodes_information(command_output):
    """
    This function will parse all info of the command
    `pbsnodes -x` and convert to a JSON structure 

    This will be used to get information and live stats of the status_code
    of the node
    """

    o = xmltodict.parse(command_output)
    nodes = o["Data"]["Node"]
    for n in nodes:
        status = _parse_status(n.get(_STATUS, ""))
        if status is not None:
            n[_PARSED_STATUS] = status
            n[MEMORY] = status[_TOTAL_MEM]
        n[GRES] = n.get(_GPU_STATUS, "")
        gpustatus = _parse_status(n[GRES])
        n[_PARSED_GPU_STATUS] = gpustatus
    return nodes


def _parse_status(statusline: str, fs=","):
    """Parses different fields of the status line in the output of pbsnodes
    
    It returns a dictionary with all the parsed fields"""
    parts = ( i.split("=", 1) for i in statusline.split(fs) if i != "")
    return { part[0]: part[1] for part in parts }


def get_node_information(testbed: Testbed) -> List[Dict]:
    """Returns a list of dictionaries where each item list correspond to a node in the
    testbed. Dictionary keys must be normalized according to the constants defined in constants.py
    (e.g., the key for the node name is constants.NAME).

    The information is retrieved from the workload manager.
    """

    command = "pbsnodes"
    params = ["-x"]
    return testbeds.common.get_nodes_testbed(testbed, command, params, _parse_pbsnodes_information)


def parse_memory(memory: str) -> Memory:
    """Parses free text from pbsnodes.status output, returning [ size, unit ].
    On error, returns [0, Memory.MEGABYTE] """

    sizes = {
        "kb": Memory.KILOBYTE,
        "mb": Memory.MEGABYTE,
        "gb": Memory.GIGABYTE
    }

    try:
        for key in sizes.keys():
            if memory.endswith(key):
                size = int(memory[0:len(memory) - len(key)])
                unit = sizes[key]
                return Memory(size=size, units=unit)
    except ValueError:
        pass    # follows below

    return Memory(size=0, units=Memory.MEGABYTE)


def parse_gre_field_info(gre):
    """This function will return a dictionary with the GPU information obtained from
    the GRES field of the normalized node structure.

    The gre string has the following format: gpu[0]=k00=v00;k01=v01...,gpu[1]=k10=v10;k11=v11..,k1=v1,k2=v2...
    Example:
    gpu[0]=gpu_id=00000000:03:00.0;gpu_pci_location_id=00000000:03:00.0;gpu_product_name=GeForce GTX 1080 Ti,gpu_display=Disabled,driver_ver=440.33.01,timestamp=Mon May 18 17:38:59 2020
    """

    resources = {}

    parsed = _parse_status(gre)

    gpus = [ inventory.find_gpu(item[_GPU_MODEL], inventory.FIELD_MODEL_NAME) 
            for item in _find_gpus(parsed) ]

    if len(gpus) > 0:
        resources["gpu"] = gpus

    return resources


def _find_gpus(status: Dict):
    """
    """
    i = 0
    while True:
        field = "gpu[{}]".format(i)
        if not field in status:
            break
        yield _parse_status(status[field], ";")
        i = i + 1
    return


def execute_batch(execution, identifier):
    """
    Executes an application with a device supervisor configured
    for slurm sbatch
    """
    execution_configuration, testbed, deployment, executable = executor_common.get_db_info(
        execution, identifier)

    if testbed.category != Testbed.torque_category:
        # If the category is not TORQUE we can not execute the app
        execution.status = Execution.__status_failed__
        execution.output = "Testbed does not support " + Executable.__type_torque_qsub__ + " applications"
        db.session.commit()

    elif not testbed.on_line :
        # If the testbed is off-line we can not execute the app
        execution.status = Execution.__status_failed__
        execution.output = "Testbed is off-line"
        db.session.commit()

    else:
        # Preparing the command to be executed
        command = "qsub"
        endpoint = testbed.endpoint
        params = []
        params.append(executable.executable_file)

        logging.info("Launching execution of application: command: " + command + " | endpoint: " + endpoint + " | params: " + str(params))

        output = shell.execute_command(command, endpoint, params)
        qsub_id = extract_id_from_qsub(output)
        
        #execution = Execution()
        execution.execution_type = execution_configuration.execution_type
        execution.status = Execution.__status_running__
        execution_configuration.executions.append(execution)
        execution.batch_id = qsub_id
        db.session.commit()

        # Add nodes
        # TODO
        #executor_common.add_nodes_to_execution(execution, endpoint)


def extract_id_from_qsub(output):
    output = output.decode('utf-8').split()
    return output[0]

def exec_qstat(endpoint: str):
    output = shell.execute_command('qstat', server=endpoint)
    output = output.decode('utf-8')
    return output


def parse_qstat_output(output: str, job_id=None) -> Dict:
    """Parse the output of qstat. It returns a dict(key=job_id, value=status).
    If the parameter id is passed, the returned dict only has one key 
    (the id parameter) - if no line is found in qstat for id, the status is '?'. 

    C -  Job is completed after having run/
    E -  Job is exiting after having run.
    H -  Job is held.
    Q -  job is queued, eligible to run or routed.
    R -  job is running.
    T -  job is being moved to new location.
    W -  job is waiting for its execution time
        (-a option) to be reached.
    S -  (Unicos only) job is suspend.
    """
    result = {}

    lines = output.split("\n")

    status = {
        'C': Execution.__status_finished__,
        'R': Execution.__status_running__,
        'Q': Execution.__status_running__,
        'E': Execution.__status_cancelled__,
    }
    if len(lines) > 3:
        for line in lines[2:]:
            fields = line.split()
            if fields == []:
                continue
            f_id = fields[0]
            f_status = fields[-2]
            
            result[f_id] = status.get(f_status, Execution.__status_unknown__)

    if job_id is not None: 
        return { job_id: result.get(job_id, '?') }

    return result