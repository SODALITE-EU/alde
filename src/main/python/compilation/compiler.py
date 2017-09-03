# This module will compile the differe4nt applications
#
# This is being developed for the TANGO Project: http://tango-project.eu
#
# Copyright: David García Pérez, Atos Research and Innovation, 2016.
#
# This code is licensed under an Apache 2.0 license. Please, refer to the LICENSE.TXT file for more information

from models import db, Executable
import shell
import os
import uuid
import compilation.config as config
import compilation.template as template

_singularity_pm_image_ = 'singularity_pm.img'

def return_not_compiled_executables():
	"""
	It looks in the db for all the not compiled executables
	"""

	return db.session.query(Executable).filter_by(status=Executable.__status_not_compiled__).all()

def compile_executables(app_folder='/tmp'):
	"""
	From all the executables that in not compiled status it compiles one by one

	TODO in the future make this into threads since it could be more efficient,
	let the user configure the number of threads, since many apps compiling 
	at the same time could be problematic

	In bigger installation, it could be thinkable to create workers to
	perform this tasks.
	"""

	# TODO fix the error of not being able to read from config the context... 

	executables = return_not_compiled_executables()

	for executable in executables:
		if  executable.compilation_type == "SINGULARITY:PM":
			executable.status = Executable.__status_compiling__
			db.session.commit()
			compile_singularity_pm(executable, app_folder)
		else:
			executable.status = Executable.__status_error_type__

def compile_singularity_pm(executable, app_folder):
	"""
	It compiles a singularity container of the type
	TANGO Programming Model
	"""

	# TODO add log information to all this process

	# First we load the configuration config
	configuration = config.find_compilation_config('SINGULARITY:PM')
	connection_url = configuration['connection_url']

	# We upload an unzip the src to the compilation node
	compilation_folder = create_random_folder(connection_url)
	upload_zip_file_application(executable, connection_url, compilation_folder, app_folder)
	unzip_src(executable, connection_url, compilation_folder)

	# We create the new template and upload it to the compilation VM
	output_template = create_singularity_template(configuration, executable, connection_url, compilation_folder)

	# We create the image and we build the container
	create_singularity_image(configuration, connection_url, _singularity_pm_image_)
	image_file = build_singularity_container(connection_url, output_template, _singularity_pm_image_, app_folder)

	executable.singularity_image_file = image_file
	executable.status = Executable.__status_compiled__ 
	db.session.commit()

def build_singularity_container(connection_url, template, image_file, upload_folder):
	"""
	It builds a singularity container following an specific 
	definition

	sudo singularity bootstrap test.img docker.def
	"""

	img_file_name = str(uuid.uuid4()) + '.img'
	local_filename = os.path.join(upload_folder, img_file_name)

	shell.execute_command('sudo', connection_url, ['singularity', 'bootstrap', image_file, template ])
	shell.scp_file(local_filename, connection_url, image_file, False)

	return local_filename

def create_singularity_image(configuration, connection_url, image_file):
	"""
	Creating the image in the compilation node
	"""

	image_size = configuration['singularity_image_size']

	shell.execute_command('singularity', connection_url, [ 'create', '--size', image_size, image_file ])

def create_singularity_template(configuration, executable, connection_url, compilation_folder):
	"""
	It creates the template, returns its name and it uploads 
	it to the singularity compilation node
	"""

	singularity_pm_template = configuration['singularity_template']

	output_template = template.update_template(singularity_pm_template, executable.compilation_script, compilation_folder)

	shell.scp_file(output_template, connection_url, '.')

	return output_template

def unzip_src(executable, connection_url, destination_folder):
	"""
	It unzips the selected zip file in the selected location for compiling
	"""

	zip_file = os.path.join(destination_folder, executable.source_code_file)
	shell.execute_command('unzip', connection_url, [ zip_file, '-d', destination_folder ])

def upload_zip_file_application(executable, connection_url, destination_folder, upload_folder):
	"""
	It uploads the zip file of the application to the selected 
	destination folder
	"""

	filename = os.path.join(upload_folder, executable.source_code_file)
	destination = os.path.join('.', destination_folder)

	shell.scp_file(filename, connection_url, destination)

def create_random_folder(connection_url):
	"""
	It creates a random folder via ssh into a server and
	returns its localiton
	"""

	# We generate a UUID for the folder
	folder_name = str(uuid.uuid4())

	# We create the folder
	shell.execute_command('mkdir', connection_url, [ folder_name ])

	return folder_name