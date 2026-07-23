"""
This module creates an ssh connection with a PowerVC controller and executes CLI commands via the ssh connection
"""
import io
import re
import os
import logging
import pexpect
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError


LOGS_FILE = '/tmp/ansible_sdk.log'


def resolve_return_code(ret_code):
    """
    Resolve the exit code to return strings for success or failure

    :param int ret_code: Exit code of a process
    :return str msg: message
    """
    if ret_code == 255:
        return "SSH Connection failed"
    if ret_code == 0:
        return "Successful"
    return "Error"


def clean_output(s):
    """
    Remove invalid characters with regular expressions and return cleaned string

    :param str s: imput string
    :return str s: cleaned string
    """
    s = re.sub(r'^.*\x1b\[2K', '', s)
    escape = re.compile(r'\s*\\(?:x|u)?\x1b\[[0-9;]*[A-GJKSTfsu]\s*')
    s = escape.sub('', s)
    s = s.replace('\r', '\n')
    # s = s.sub(r'.*\x1b\[2K', '')
    # s = s.split('\\x1b\\[2K')[-1]
    return s.replace('\t', '     ')


class Connection:
    """
    Class to create an ssh connection with the PowerVC Controller to execute CLI commands
    """

    def __init__(self, module, host_ip, user, password, command=None, messages={}):
        """
        Initialize connection and logger

        :param module: Ansible module
        :param str host_ip: Controller IP address
        :param str user: ssh login user (pvcroot)
        :param str password: ssh login password
        :param str command: ssh command to be executed
        :param dict messages: messaegs expected during command execution
        """
        self.module = module
        self.host_ip = host_ip
        self.password = password
        self.user = user
        self.cmd = command
        self.messages = messages
        self.logger = self.create_logger()

    def create_logger(self):
        """
        Create a logger with the LOGS_FILE

        :return : logger
        """
        logging.basicConfig(
            filename=LOGS_FILE,
            format='%(asctime)s - %(levelname)s - '
            ' - ' + '%(message)s',
            filemode='a',
            level=logging.INFO
        )
        logger = logging.getLogger()
        return logger

    def _construct_ssh_command(self):
        """
        Constructs the ssh command with ip, host_key_checking variables, user, password and command

        :return str ssh_command: ssh command
        """
        host_key_ignore = ''
        # 'ANSIBLE_HOST_KEY_CHECKING' only will work if it is set as environment variable
        # All other options like from ansible config file or inventory file wont work
        if os.environ.get('ANSIBLE_HOST_KEY_CHECKING') in [
            'False',
            'false',
            'FALSE',
            '0',
            'no',
            'No',
            'NO'
        ]:
            host_key_ignore = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

        # spawn with pexpect
        self.logger.info('Command %s', self.cmd)
        cmd = self.cmd if self.cmd is not None else ""
        if self.password:
            ssh_command = "sshpass -p '{0}' ssh {1}@{2} {3} '{4}'".format(
                self.password, self.user, self.host_ip, host_key_ignore, cmd)
        else:
            ssh_command = "ssh '{0}'@{1} {2} '{3}'".format(
                self.user, self.host_ip, host_key_ignore, cmd)
        return ssh_command

    def run(self):
        """
        Run ssh command

        :return int, str exit_code, stdout: Return exit_code of the ssh_command with the stdout
        """
        ssh_command = self._construct_ssh_command()
        try:
            self.logger.info('Running ssh command: %s', ssh_command)
            if not self.messages:
                exit_code, stdout, stderr = self.module.run_command(
                    ssh_command, use_unsafe_shell=True)

                # Some CLI commands print errors only to stderr. If the command
                # failed, return stderr so the caller gets the actual error message.
                if exit_code != 0 and stderr:
                    stdout = stderr

            else:
                child = pexpect.spawn(
                    ssh_command, encoding="utf-8", timeout=300)
                self.logger.info("Child process spawned %s", child)
                child.logfile = io.StringIO()
                for msg, value in self.messages.items():
                    i = child.expect([msg, pexpect.TIMEOUT, pexpect.EOF])
                    if i == 0:
                        child.sendline(value)
                        self.logger.info("PASSED %s", value)
                    elif i == 1:
                        self.logger.error("Timeout waiting for next prompt")
                        break
                    elif i == 2:
                        self.logger.critical("Premature exit")
                        break
                child.expect(pexpect.EOF)
                exit_code = child.exitstatus or child.signalstatus or 0
                output_buffer = child.logfile
                stdout = output_buffer.getvalue()
            self.logger.info(
                "Command execution completed with exit code: %s", exit_code)
            if stdout is None or stdout == "":
                stdout = "The command did not return any output"
            if exit_code == 255:
                return 1, str(CLIError(resolve_return_code(exit_code))).split('\n')

            return exit_code, clean_output(stdout.strip('\n').strip('\t').strip()).split('\n')
        except pexpect.exceptions.TIMEOUT:
            self.logger.critical("Operation timed out")
            return 1, "Operation timed out"
        except pexpect.exceptions.EOF:
            self.logger.critical("Unexpected end of process")
            return 1, "Unexpected end of process"
        except Exception as e:
            self.logger.critical("Module failed: %s", str(e))
            return 1, f"Module failed: {str(e)}"
