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
# Unit tests that checks ALDE torque module
#

import os
import unittest
import unittest.mock as mock
import re
import inventory
from models import Testbed, Application, Deployment, ExecutionConfiguration, Executable, Execution
from sqlalchemy_mapping_tests.mapping_tests import MappingTest
from models import db, Testbed, Node, CPU, Memory
import torque
import testbeds.facade
from testfixtures import LogCapture
from unittest.mock import call


def read(relpath: str):
    path = os.path.join(os.path.dirname(__file__), relpath)
    f = open(path, 'rb')
    result = f.read()
    f.close()
    return result
    

class TorqueTests(MappingTest):
    """
    Unittests of the functions used to interact with and torque
    testbed
    """
    command_pbsnodes_output = read('testdata/pbsnodes.out')

    @mock.patch('torque.shell.execute_command')
    def test_get_nodes_testbed(self, mock_shell):
        """
        It verifies the correct work of the function get_nodes_testbed
        """
        command="pbsnodes"
        params=["-x"]

        # It checks first if it is type TORQUE
        testbed = Testbed('x', 'false', 'xxx', 'protocol', 'xxx')

        nodes = torque.get_nodes_testbed(testbed)
        self.assertEqual(0, len(nodes))

        # We create a testbed with local access
        testbed = Testbed('x', 'false', Testbed.torque_category, Testbed.protocol_local, 'xxx')
        mock_shell.return_value = self.command_pbsnodes_output
        nodes = torque.get_nodes_testbed(testbed)

        self.assertEqual(3,len(nodes))
        mock_shell.assert_called_with(command=command, params=params)

        # We create a testbe with ssh access
        testbed = Testbed('x', 'false', Testbed.torque_category, Testbed.protocol_ssh , "user@ssh.com")
        mock_shell.return_value = self.command_pbsnodes_output
        nodes = torque.get_nodes_testbed(testbed)

        self.assertEqual(3,len(nodes))
        mock_shell.assert_called_with(command=command, server="user@ssh.com", params=params)

        # Testbed with unknown protocol should return empty String
        # We create a testbed with ssh access
        testbed = Testbed('x', True, Testbed.torque_category, "xxx" , "user@ssh.com")
        mock_shell.return_value = self.command_pbsnodes_output
        nodes = torque.get_nodes_testbed(testbed)

        self.assertEqual(0,len(nodes))


    def test_parse_status(self):
        """Tests parsing status line from pbsnodes output"""
        s = "opsys=linux,uname=Linux node-6.novalocal 3.10.0-1062.12.1.el7.x86_64,totmem=131583196kb,availmem=128473264kb,physmem=131583196kb,ncpus=40,loadave=0.00,gres="
        d = torque._parse_status(s)
        self.assertEqual("linux", d.get("opsys"))
        self.assertEqual("131583196kb", d.get(torque._TOTAL_MEM))
        self.assertEqual("128473264kb", d.get("availmem"))


    def test_parse_gpu_status(self):
        s = "gpu_id=00000000:03:00.0;gpu_product_name=GeForce GTX 1080 Ti"
        d = torque._parse_status(s, ";")

        self.assertEqual("GeForce GTX 1080 Ti", d["gpu_product_name"])
        self.assertEqual("00000000:03:00.0", d["gpu_id"])
        return


    def test_find_gpus(self):
        s = "gpu[0]=gpu_product_name=GeForce GTX 1080 Ti,gpu[1]=gpu_product_name=Nvidia TESLA C2075,field1=value1"
        gpustatus = torque._parse_status(s)
        gpus = list(torque._find_gpus(gpustatus))
        self.assertEqual(2, len(gpus))


    def test_parse_pbsnodes_information(self):
        """
        Unit test to verify the correct work of the function:
        parse_scontrol_information
        """

        nodes_info = torque._parse_pbsnodes_information(self.command_pbsnodes_output)

        self.assertEqual(3, len(nodes_info))
        self.assertEqual("node-1.novalocal", nodes_info[0]['name'])
        self.assertEqual("20", nodes_info[0]['total_cores'])
        self.assertEqual("40", nodes_info[0]['total_threads'])
        self.assertEqual("2", nodes_info[0]['total_sockets'])
        self.assertEqual("131583196kb", nodes_info[0][torque._PARSED_STATUS][torque._TOTAL_MEM])
        self.assertTrue("gpu[0]=gpu_id=00000000" in nodes_info[0][torque.GRES])
        self.assertEqual("node-2.novalocal", nodes_info[1]['name'])
        self.assertEqual("1", nodes_info[1]['gpus'])
        self.assertEqual("node-6.novalocal", nodes_info[2]['name'])

    @mock.patch('torque.shell.execute_command')
    def test_get_node_information(self, mock_shell):
        """
        It verifies the correct work of the function get_nodes_testbed
        """
        command = "pbsnodes"
        params = ["-x"]

        # It checks first if it is type TORQUE
        testbed = Testbed('x', 'false', 'xxx', 'protocol', 'xxx')

        nodes = torque.get_node_information(testbed)
        self.assertEqual(0, len(nodes))

        # We create a testbed with local access
        testbed = Testbed('x', 'false', Testbed.torque_category, Testbed.protocol_local, 'xxx')
        mock_shell.return_value = self.command_pbsnodes_output
        nodes_info = torque.get_node_information(testbed)

        self.assertEqual(3, len(nodes_info))
        self.assertEqual("node-1.novalocal", nodes_info[0]['name'])
        self.assertEqual("20", nodes_info[0]['total_cores'])
        self.assertEqual("40", nodes_info[0]['total_threads'])
        self.assertEqual("2", nodes_info[0]['total_sockets'])
        self.assertEqual("node-2.novalocal", nodes_info[1]['name'])
        self.assertEqual("1", nodes_info[1]['gpus'])
        self.assertEqual("131583196kb", nodes_info[0][torque._PARSED_STATUS][torque._TOTAL_MEM])

        self.assertEqual("node-6.novalocal", nodes_info[2]['name'])
        mock_shell.assert_called_with(command=command, params=params)

        # We create a testbed with ssh access
        testbed = Testbed('x', 'false', Testbed.torque_category, Testbed.protocol_ssh , "user@ssh.com")
        mock_shell.return_value = self.command_pbsnodes_output
        nodes_info = torque.get_node_information(testbed)

        self.assertEqual(3, len(nodes_info))
        self.assertEqual("node-1.novalocal", nodes_info[0]['name'])
        self.assertEqual("20", nodes_info[0]['total_cores'])
        self.assertEqual("40", nodes_info[0]['total_threads'])
        self.assertEqual("2", nodes_info[0]['total_sockets'])
        self.assertEqual("node-2.novalocal", nodes_info[1]['name'])
        self.assertEqual("1", nodes_info[1]['gpus'])
        self.assertEqual("node-6.novalocal", nodes_info[2]['name'])
        mock_shell.assert_called_with(command=command, server="user@ssh.com", params=params)

        # Testbed with unknown protocol should return empty String
        testbed = Testbed('x', True, Testbed.torque_category, "xxx" , "user@ssh.com")
        nodes = torque.get_node_information(testbed)

        self.assertEqual(0,len(nodes))

    @mock.patch('shell.execute_command')
    def test_update_node_information(self, mock_shell):
        """
        Test that the correct work of this function
        """
        l = LogCapture() # we capture the logger
        command = "pbsnodes"
        params = ["-x"]

        # We store some data in the db for the test.
        # We add a testbed to the db
        testbed = Testbed("name1",
                            True,
                            Testbed.torque_category,
                            Testbed.protocol_ssh,
                            "user@server",
                            ['torque'])

        # We add some nodes to Testbed_1
        node_1 = Node()
        node_1.name = "node-1.novalocal"
        node_1.information_retrieved = True
        node_2 = Node()
        node_2.name = "node-2.novalocal"
        node_2.information_retrieved = True
        testbed.nodes = [ node_1, node_2 ]
        node_1.disabled = True

        db.session.add(testbed)
        db.session.commit()

        # We mock the command call
        mock_shell.return_value = self.command_pbsnodes_output

        testbeds.facade.update_testbed_node_information(testbed)

        # We verify the results
        node_1 = db.session.query(Node).filter_by(name='node-1.novalocal').first()
        node_2 = db.session.query(Node).filter_by(name='node-2.novalocal').first()
        self.assertEqual('free', node_1.state)
        self.assertEqual(1, len(node_1.memories))
        self.assertEqual(Memory.KILOBYTE, node_1.memories[0].units)
        self.assertEqual(131583196, node_1.memories[0].size)
        self.assertEqual(1,len(node_1.gpus))

        self.assertEqual('free', node_2.state)
        self.assertEqual(1, len(node_2.memories))
        self.assertEqual(Memory.KILOBYTE, node_2.memories[0].units)
        self.assertEqual(131583197, node_2.memories[0].size)
        self.assertEqual(0,len(node_2.gpus))

        mock_shell.assert_called_with(command=command, server="user@server", params=params)
        self.assertEqual(1, mock_shell.call_count)

        # Checking that we are logging the correct messages
        l.check(
            ('root', 'INFO', 'Updating information for node: node-1.novalocal if necessary'),
            ('root', 'INFO', 'Updating memory information for node: node-1.novalocal'),
            ('root', 'INFO', 'Updating gpu information for node: node-1.novalocal'),
            ('root', 'INFO', 'Updating information for node: node-2.novalocal if necessary'),
            ('root', 'INFO', 'Updating memory information for node: node-2.novalocal'),
            )
        l.uninstall() # We uninstall the capture of the logger

    def test_parse_memory(self):
        m = torque.parse_memory("131583196kb")
        self.assertEqual(str(Memory(131583196, Memory.KILOBYTE)), str(m))

        m = torque.parse_memory("131583mb")
        self.assertEqual(str(Memory(131583, Memory.MEGABYTE)), str(m))

        m = torque.parse_memory("131gb")
        self.assertEqual(str(Memory(131, Memory.GIGABYTE)), str(m))

        m = torque.parse_memory("11err")
        self.assertEqual(str(Memory(0, Memory.MEGABYTE)), str(m))

        m = torque.parse_memory("1s1gb")
        self.assertEqual(str(Memory(0, Memory.MEGABYTE)), str(m))

    @mock.patch('shell.execute_command')
    def test_exec_qstat(self, mock_shell):
        mock_shell.return_value = read('testdata/qstat.out')
        endpoint = "user@host"
        self.assertNotEqual('', torque.exec_qstat(endpoint))

    def test_parse_qstat_output(self):
        output = read('testdata/qstat.out').decode('utf-8')

        self._check_qstat(output, 'C', Execution.__status_finished__)
        self._check_qstat(output, 'R', Execution.__status_running__)
        self._check_qstat(output, 'Q', Execution.__status_running__)
        self._check_qstat(output, 'E', Execution.__status_cancelled__)
        self._check_qstat(output, '?', Execution.__status_unknown__)
        self._check_qstat('', '', '?')

        self.assertEqual(torque.parse_qstat_output(output), { 
            "1186.cloudserver": Execution.__status_unknown__, 
            "1187.cloudserver": Execution.__status_finished__})

    def _check_qstat(self, output, f_status, expected):
        id = "1186.cloudserver"
        output = output.replace('?', f_status)
        actual = torque.parse_qstat_output(output, id)
        self.assertEqual(expected, actual[id])

    @mock.patch("executor_common.add_nodes_to_execution")
    @mock.patch("shell.execute_command")
    def test_execute_application_type_torque_qsub(self, mock_shell, mock_add_nodes):
        """
        It verifies that the application type slurm sbatch is executed
        """

        # First we verify that the testbed is of type TORQUE to be able
        # to execute it, in this case it should give an error since it is
        # not of type torque

        # We define the different entities necessary for the test.
        testbed = Testbed(name="nova2",
                          on_line=True,
                          category="xxxx",
                          protocol="SSH",
                          endpoint="user@testbed.com",
                          package_formats= ['sbatch', 'SINGULARITY'],
                          extra_config= {
                              "enqueue_compss_sc_cfg": "nova.cfg" ,
                              "enqueue_env_file": "/home_nfs/home_ejarquej/installations/rc1707/COMPSs/compssenv"
                          })
        db.session.add(testbed)

        application = Application(name="super_app")
        db.session.add(application)
        db.session.commit() # So application and testbed get an id

        executable = Executable()
        executable.compilation_type = Executable.__type_torque_qsub__
        executable.executable_file = "pepito.sh"
        db.session.add(executable)
        db.session.commit() # We do this so executable gets and id

        deployment = Deployment()
        deployment.testbed_id = testbed.id
        deployment.executable_id = executable.id
        db.session.add(deployment) # We add the executable to the db so it has an id

        execution_config = ExecutionConfiguration()
        execution_config.execution_type = Executable.__type_torque_qsub__
        execution_config.application = application
        execution_config.testbed = testbed
        execution_config.executable = executable 
        db.session.add(execution_config)
        db.session.commit()

        execution = Execution()
        execution.execution_type = Executable.__type_torque_qsub__
        execution.status =  Execution.__status_submitted__

        torque.execute_batch(execution, execution_config.id)

        self.assertEquals(Execution.__status_failed__, execution.status)
        self.assertEquals("Testbed does not support TORQUE:QSUB applications", execution.output)

        # If the testbed is off-line, execution isn't allowed also
        testbed.category = Testbed.torque_category
        testbed.on_line = False
        db.session.commit()

        execution = Execution()
        execution.execution_type = Executable.__type_torque_qsub__
        execution.status = Execution.__status_submitted__

        torque.execute_batch(execution, execution_config.id)

        self.assertEquals(Executable.__type_torque_qsub__, execution.execution_type)
        self.assertEquals(Execution.__status_failed__, execution.status)
        self.assertEquals("Testbed is off-line", execution.output)

        ## Test executing
        output = b'1208.cloudserver'
        mock_shell.return_value = output

        testbed.category = Testbed.torque_category
        testbed.on_line = True
        db.session.commit()

        execution = Execution()
        execution.execution_type = Executable.__type_torque_qsub__
        execution.status = Execution.__status_submitted__

        torque.execute_batch(execution, execution_config.id)

        mock_shell.assert_called_with("qsub", "user@testbed.com", ["pepito.sh"])
        execution = db.session.query(Execution).filter_by(execution_configuration_id=execution_config.id).first()
        self.assertEqual(execution.execution_type, execution_config.execution_type)
        self.assertEqual(execution.status, Execution.__status_running__)
        self.assertEqual("1208.cloudserver", execution.batch_id)

        # TODO
        # mock_add_nodes.assert_called_with(execution, "user@testbed.com")
