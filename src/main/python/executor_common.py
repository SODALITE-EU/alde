from models import db, Execution, Testbed, Executable, Deployment, ExecutionConfiguration, Node, Application
import shell

def get_db_info(execution, identifier):
    """
    Internal method that gets all the necessary srun information
    """

    # Lets recover all the information needed...execution_configuration
    execution_configuration = db.session.query(ExecutionConfiguration).filter_by(id=identifier).first() # This is to avoid reusing objects from other thread
    testbed = db.session.query(Testbed).filter_by(id=execution_configuration.testbed_id).first()
    deployment = db.session.query(Deployment).filter_by(executable_id=execution_configuration.executable_id, testbed_id=testbed.id).first()
    executable = db.session.query(Executable).filter_by(id=execution_configuration.executable_id).first()

    return execution_configuration, testbed, deployment, executable

def add_nodes_to_execution(execution, url):
	"""
	This method takes the squeue id and adds nodes
	that are being used by the execution.

	[garciad@ns54 ~]$ squeue -j 7286 -h -o "%N"
	ns51
	"""

	if execution.status == Execution.__status_running__ and execution.batch_id != None :

		command_output = shell.execute_command("squeue", url , [ '-j ' + str(execution.batch_id) , '-h -o "%N"' ])
		
		if command_output != b'\n' :
			nodes = []
			nodes_string = command_output.decode('utf-8').split('\n')[0]

			array_nodes = nodes_string.split(',')

			for node_in_array in array_nodes :

				if '[' not in node_in_array :
					node = db.session.query(Node).filter_by(name=str(node_in_array)).first()
					nodes.append(node)
				else :
					node_start_name = node_in_array.split('[')[0]
					boundaries = node_in_array.split('[')[1].split(']')[0]
					limits = boundaries.split('-')
					start = int(limits[0])
					end = int(limits[1]) + 1

					for number in range(start,end) :
						node_name = node_start_name + str(number)
						node = db.session.query(Node).filter_by(name=node_name).first()
						nodes.append(node)
				
			execution.nodes = nodes
			db.session.commit()
