#!/usr/bin/env python
# --*-- encoding: utf-8 --*--

"""deployer : deploy scripts on raspberry pi via ssh

Usage:
  deployer.py install
  deployer.py redeploy
"""

from docopt import docopt
from os.path import join
from posixpath import join as ljoin #join but for unix pathes when running on a windows system

import os
import paramiko
import string
import time

class RemoteServer():
    def __init__(self, ip, port, username, password):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

class Deployable():
    def __init__(self, remote_drop_path, local_relative_daemon_folder, python_executable, service_name):
        """
            remote_drop_path : where the project folder will be dropped, contains multiple project
            local_relative_daemon_folder : the name of the folder cointaining the project to deploy
        """
        self.repo_path = os.path.split(os.path.realpath(__file__))[0]
        self.remote_drop_path = remote_drop_path
        self.local_relative_daemon_folder = local_relative_daemon_folder
        self.local_absolute_daemon_folder = join(self.repo_path, self.local_relative_daemon_folder)
        self.remote_absolute_daemon_folder = ljoin(self.remote_drop_path, self.local_relative_daemon_folder)
        self.service_name = service_name
        self.python_executable = python_executable
    
    def printYourself(self):
        print "self.repo_path : {}".format(self.repo_path)
        print "self.remote_drop_path : {}".format(self.remote_drop_path)
        print "self.local_relative_daemon_folder : {}".format(self.local_relative_daemon_folder)
        print "self.local_absolute_daemon_folder : {}".format(self.local_absolute_daemon_folder)
        print "self.remote_absolute_daemon_folder : {}".format(self.remote_absolute_daemon_folder)
        print "self.service_name : {}".format(self.service_name)
        print "self.python_executable : {}".format(self.python_executable)

class RemoteHelper():
    "can do stuff over ssh on a remote server, like delete file over there and all"
    def __init__(self, paramiko_ssh_object):
        self.ssh = paramiko_ssh_object

    ############################################################################################
    #THIS METHOD IS NOT TO BE USED, it is used by sftpUploadSafe and sftpUploadFolderSafe      #
    #it needs the sftp object to be opened and closed before and after its call                #
    # the xxxsafe methode manage that                                                          #
    ############################################################################################
    def _recursiveRemoteMkdir(self, sftp, remote_directory):                                   #
        """                                                                                    #
        Make a full path on the remote server via sftp                                         #
            -sftp : (sftp paramiko) sftp object                                                #
            -remote_directory : (string) absolute path to create                               #
        """                                                                                    #
        if remote_directory == '/':                                                            #
            sftp.chdir('/')                                                                    #
            return                                                                             #
        if remote_directory == '':                                                             #
            return                                                                             #
        try:                                                                                   #
            sftp.chdir(remote_directory)                                                       #
        except IOError:                                                                        #
            dirname, basename = os.path.split(remote_directory.rstrip('/'))                    #
            self._recursiveRemoteMkdir(sftp, dirname)                                          #
            sftp.mkdir(basename, mode=0o755)                                                   #
            sftp.chdir(basename)                                                               #
            return True                                                                        #
    ############################################################################################

    def sftpUploadSafe(self, local_path, remote_path, file_name):
        """
        Upload a file on the remote server, block until the end of the upload
            -local_path : (string) local path WITHOUT the file name
            -remote_path : (string) remote path WITHOUT the file name
            -file_name : (string) filename with it's extension (but without its path)
        """
        print "uploading {} to remote server".format(file_name)
        sftp = self.ssh.open_sftp()
        self._recursiveRemoteMkdir(sftp, remote_path)
        sftp.put(join(local_path, file_name), file_name)
        sftp.close() #bloque jusqua la fin du put

    def sftpUploadFolderSafe(self, local_folder, remote_path, excluded_folders=[]):
        """
        Upload a folder on the remote server, block until the end of the upload, allow you to
        exclude some folders (and their sub folders)
            -local_folder : (string) absolute path of the folder to upload
            -remote_path : (string) absolute path of where to put it on the remote server
            -excluded_folders : list(string) folders to exclude (exclude their sub-folders too)
        """

        print "putting {} in {}".format(local_folder, remote_path)
        sftp = self.ssh.open_sftp()

        def put_dir(sftp, local_folder, remote_folder_path):

            print "processing {} -> {}".format(local_folder, remote_folder_path)

            self._recursiveRemoteMkdir(sftp, remote_folder_path)

            for excluded_folder in excluded_folders:
                if os.path.basename(local_folder) == excluded_folder:
                    print 'Excluding {}'.format(local_folder)
                    return

            for item in os.listdir(local_folder):
                if os.path.isfile(os.path.join(local_folder, item)):
                    sftp.put(os.path.join(local_folder, item), ljoin(remote_folder_path, item))
                else:
                    self._recursiveRemoteMkdir(sftp, ljoin(remote_folder_path, item))
                    put_dir(sftp, os.path.join(local_folder, item), ljoin(remote_folder_path, item))

        put_dir(sftp, local_folder, ljoin(remote_path, os.path.basename(local_folder)))
        sftp.close() #bloque jusqua la fin des put

    def waitForExecCommandEnd(self, channel, command):
        """
        Block untill the end of a command executed by Paramiko.ssh.exec_command
            -channel : (channel) channel stdout returned by Paramiko.ssh.exec_command
            -command : (string) command to run
        """
        while not channel.exit_status_ready():
            print "Waiting for end of {}".format(command)
            time.sleep(1)

    def runRemoteCommand(self, command):
        """
        Run a command on the remote server via ssh and block until it ends
            -command : (string) command to run
        """
        print "running {}".format(command)
        a, stdout, stderr = self.ssh.exec_command(command)
        self.waitForExecCommandEnd(stdout.channel, command)
        #print stdout.readlines()
        #print stderr.readlines()


    def sshDeleteFile(self, absolute_file_path):
        """
        Delete a file on the remote server
            -absolute_file_path : (string) remote absolute path of file to delete
        """
        print "deleting {}" .format(absolute_file_path)
        self.runRemoteCommand("rm " + absolute_file_path)

    def sshDeleteFolder(self, absolute_folder_path):
        """
        Delete a folder on the remote server
            -absolute_file_path : (string) remote absolute path of folder to delete
        """
        print "deleting {}" .format(absolute_folder_path)
        self.runRemoteCommand("rm -rf " + absolute_folder_path)

    def extract_remote_tarfile(self, destination, tar_absolutefilename):
        """
        etrait un tar comme "extract here" de winrar
        """ 
        command = "tar -C {} -zxvf {}".format(destination, tar_absolutefilename)
        self.runRemoteCommand(command)

class GenericDeployer(object):
    """
	Deploy something on a remote server
	"""

    def __init__(self, remoteServer, deployable):
        self.remoteServer = remoteServer
        self.deployable = deployable
        self.ssh = paramiko.SSHClient()
        self.serverInterface = RemoteHelper(self.ssh)

    def makeLocalPathIfNecessary(self, path):
        """
		Créer un chemin si il n'existe pas
			-path : (sting) le chemin a créer
		"""
        if not os.path.exists(path):
            os.makedirs(path)

    def formatFile(self, infile_path, outfile_path, params, target, method="format"):
        """
		Remplit les champs d'un fichier de template avec le contenu du dictionnaire 'params'
			-infile_path : (string) chemin du fichier d'entrée
			-outfile_path : (string) chemin du fichier de sortie
			-params : (dictionnaire de string) la clé est le terme à remplacer
			-target : (string) indique si passe un fichier windows ou linux, les valeur
					  possible sont 'linux' ou 'windows'
			-method : (string) indique si on utilise la méthode Template.substitute ou string.format
					  les valeur possible sont "format" et "substitute"
					  La methode formats remplace ce qui est entre '{}' et la methode substitute
					  remplace ce qui est de type $xxxxxx
		"""
        print "formating file {} using {} method".format(infile_path, method)
        print "writing formated file in {}".format(outfile_path)
        base, _ = os.path.split(outfile_path)
        self.makeLocalPathIfNecessary(base)

        openingMode = 'w'
        if target == 'linux':
            openingMode += 'b'

        with open(infile_path, 'r') as infile, open(outfile_path, openingMode) as outfile:
            for line in infile:
                if "format" == method:
                    line = line.decode('UTF-8').format(**params)
                    outfile.write(line.encode('UTF-8'))
                else:
                    template = string.Template(line.decode('UTF-8'))
                    outfile.write(template.substitute(**params).encode('UTF-8'))

    def authentificate(self):
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print "Connection a %s:%s user=%s mdp=XXXXXXXXX" % (self.remoteServer.ip,
                                                            self.remoteServer.port,
                                                            self.remoteServer.username)
        self.ssh.connect(self.remoteServer.ip, port=self.remoteServer.port, username=self.remoteServer.username,
                         password=self.remoteServer.password)

    def end_connection(self):
        print "Closing ssh connection"
        self.ssh.close()
        print "Done"

    def prepare(self):
        """
        install dependancies on the server
        """
        raise Exception("Not yet implemented")

    def install(self):
        """
        will delete anything in the remote folder, use the first time, or for a fresh start
        """
        print "Using this deployable :"
        self.deployable.printYourself()

        self.authentificate()

        # in case it was already deployed before
        self.serverInterface.runRemoteCommand('systemctl stop {}'.format(self.deployable.service_name))
        time.sleep(2)

        # deploy the web app for the service to work
        self.serverInterface.sshDeleteFolder(self.deployable.remote_absolute_daemon_folder)
        self.serverInterface.sftpUploadFolderSafe(self.deployable.local_absolute_daemon_folder,
                                                  self.deployable.remote_drop_path)

        # make the service file
        abs_service_local_path = join(self.deployable.repo_path, 'services_files_for_debian', 'lib', 'systemd',
                                      'system')
        abs_service_remote_path = '/lib/systemd/system'
        self.serverInterface.runRemoteCommand('sudo chmod a+w /lib/systemd/system')
        service_template_filename = 'service.template'
        service_template_filled_filename = '{}.service'.format(self.deployable.service_name)
        self.formatFile(join(abs_service_local_path, service_template_filename),
                        join(abs_service_local_path, service_template_filled_filename),
                        {"absolute_path_to_service": ljoin(self.deployable.remote_absolute_daemon_folder,
                                                           self.deployable.python_executable),
                         "service_description" : "{} daemons".format(self.deployable.service_name)
                         },
                        'linux',
                        'substitute'
                        )

        # deploy the service file and activate it
        self.serverInterface.sftpUploadSafe(abs_service_local_path, abs_service_remote_path,
                                            service_template_filled_filename)
        self.serverInterface.runRemoteCommand('sudo systemctl daemon-reload')
        abs_service_remote_filename = ljoin(abs_service_remote_path, service_template_filled_filename)
        self.serverInterface.runRemoteCommand('sudo systemctl enable {}'.format(abs_service_remote_filename))
        self.serverInterface.runRemoteCommand('sudo systemctl start {}'.format(self.deployable.service_name))
        self.end_connection()

        # delete the service file created from the template
        os.remove(join(abs_service_local_path, service_template_filled_filename))

    def redeploy(self):
        """
        redeploy only the python file, not destroying other files created in the same folder
        """
        print "Using this deployable :"
        self.deployable.printYourself()

        self.authentificate()

        # stop the service
        self.serverInterface.runRemoteCommand('sudo systemctl stop {}'.format(self.deployable.service_name))
        time.sleep(2)

        # uploade the new code
        self.serverInterface.sshDeleteFile(
            ljoin(self.deployable.remote_absolute_daemon_folder, self.deployable.python_executable))
        self.serverInterface.sftpUploadSafe(
            self.deployable.local_absolute_daemon_folder,
            self.deployable.remote_absolute_daemon_folder,
            self.deployable.python_executable
        )

        # restart the service
        self.serverInterface.runRemoteCommand('sudo systemctl start {}'.format(self.deployable.service_name))

rpi = RemoteServer("192.168.1.75", 22, "pi", "raspberry")
camera_rpi_deployable = Deployable(
                            "/home/pi", #absolute path that will be created on the raspberry and where the script will be dropped
                            "ledflasher", #folder next to this script containing the sccript to deploy
                            "ledflasher.py", #name of the python script to deploy in the folder given above
                            "ledflasher" #name of the systemd service that will be created
                            )

rpiDeployer = GenericDeployer(rpi, camera_rpi_deployable)
args = docopt(__doc__)
if args['install']:
    print "Installing script in {} (purging the directory content), and creating/initiating a service for startup".format(camera_rpi_deployable.remote_absolute_daemon_folder)
    rpiDeployer.install()
elif args['redeploy']:
    print "redeploying script in {}, and restarting service".format(camera_rpi_deployable.remote_absolute_daemon_folder)
    rpiDeployer.redeploy()