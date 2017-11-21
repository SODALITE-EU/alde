# Builder script for the Application Lifecycle Deployment Engine
#
# This is being developed for the TANGO Project: http://tango-project.eu
#
# Copyright: David García Pérez, Atos Research and Innovation, 2016.
#
# This code is licensed under an Apache 2.0 license. Please, refer to the LICENSE.TXT file for more information

from sqlalchemy_mapping_tests.mapping_tests import MappingTest
from models import db, Application, ExecutionConfiguration, Executable

class ApplicationMappingTest(MappingTest):
    """
    Series of test to validate the correct mapping to the class
    Application to be stored into an SQL relational db
    """

    def test_crud_application(self):
        """It test basic CRUD operations of an Application Class"""

        # We verify that the object is not in the db after creating
        application = Application("AppName")
        self.assertIsNone(application.id)

        # We store the object in the db
        db.session.add(application)

        # We recover the application from the db
        application = db.session.query(Application).filter_by(name='AppName').first()
        self.assertIsNotNone(application.id)
        self.assertEquals("AppName", application.name)

        # We check that we can update the application
        application.name = 'pepito'
        db.session.commit()
        application_2 = db.session.query(Application).filter_by(name='pepito').first()
        self.assertEquals(application.id, application_2.id)
        self.assertEquals("pepito", application.name)

        # We check the deletion
        db.session.delete(application_2)
        count = db.session.query(Application).filter_by(name='pepito').count()
        self.assertEquals(0, count)

    def test_application_execution_script_relation(self):
        """
        Unit tests that verifies the correct relation between the Application
        class and the ExecutionConfiguration class is built
        """

        # We create an application
        application = Application("AppName")


        # We create several ExecutionConfigurations
        application.execution_configurations = [
            ExecutionConfiguration(),
            ExecutionConfiguration(),
            ExecutionConfiguration()]

        # We save everything to the db
        db.session.add(application)
        db.session.commit()

        # We retrieve the application and verify taht the execution_configurations are there
        application = db.session.query(Application).filter_by(name='AppName').first()

        self.assertEquals(3, len(application.execution_configurations))

        # lets delete a execution_script directly
        db.session.delete(application.execution_configurations[0])
        db.session.commit()

        application = db.session.query(Application).filter_by(name='AppName').first()
        self.assertEquals(2, len(application.execution_configurations))

        # It should be only two execution scripts in the db:
        execution_configurations = db.session.query(ExecutionConfiguration).all()
        self.assertEquals(2, len(execution_configurations))

    def test_application_executable_relation(self):
        """
        Unit tests that verifies the correct relation between the Application
        class and the ExecutionConfiguration class is built
        """

        # We create an application
        application = Application("AppName")
        executable_1 = Executable()
        executable_1.source_code_file = "source1"
        executable_1.compilation_script = "script1"
        executable_1.compilation_type = "type1"
        executable_2 = Executable()
        executable_2.source_code_file = "source2"
        executable_2.compilation_script = "script2"
        executable_2.compilation_type = "type2"
        executable_3 = Executable()
        executable_3.source_code_file = "source3"
        executable_3.compilation_script = "script3"
        executable_3.compilation_type = "type3"

        # We create several Executables
        application.executables = [
            executable_1,
            executable_2,
            executable_3]

        # We save everything to the db
        db.session.add(application)
        db.session.commit()

        # We retrieve the application and verify taht the execution_configurations are there
        application = db.session.query(Application).filter_by(name='AppName').first()

        self.assertEquals(3, len(application.executables))
        self.assertEquals("source1", application.executables[0].source_code_file)
        self.assertEquals("source2", application.executables[1].source_code_file)
        self.assertEquals("source3", application.executables[2].source_code_file)

        # lets delete a execution_script directly
        db.session.delete(application.executables[0])
        db.session.commit()

        application = db.session.query(Application).filter_by(name='AppName').first()
        self.assertEquals(2, len(application.executables))
        self.assertEquals("source2", application.executables[0].source_code_file)
        self.assertEquals("source3", application.executables[1].source_code_file)

        # It should be only two execution scripts in the db:
        executables = db.session.query(Executable).all()
        self.assertEquals(2, len(executables))
        self.assertEquals("source2", executables[0].source_code_file)
        self.assertEquals("source3", executables[1].source_code_file)