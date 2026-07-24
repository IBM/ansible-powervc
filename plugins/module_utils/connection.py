"""
SSH connection utility for the IBM PowerVC Ansible collection.

Uses Paramiko so that:
  - The password is never passed on the command line (was: sshpass -p).
  - All commands executed within a single module call reuse the same
    authenticated SSH Transport (one handshake, not one per command).
  - Interactive prompts (e.g. Y/N confirmations) are handled via an SSH
    channel with a pseudo-TTY, replacing the previous pexpect-based path.
"""
import re
import time
import logging
import paramiko
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError


LOGS_FILE = '/tmp/ansible_sdk.log'

# How long (seconds) to wait for a prompt or for the channel to close.
_CMD_TIMEOUT = 300
# Poll interval when draining channel output.
_POLL_INTERVAL = 0.1


def clean_output(s):
    """
    Strip terminal control sequences and normalise whitespace.

    :param str s: raw output string
    :return str s: cleaned string
    """
    s = re.sub(r'^.*\x1b\[2K', '', s)
    escape = re.compile(r'\s*\\(?:x|u)?\x1b\[[0-9;]*[A-GJKSTfsu]\s*')
    s = escape.sub('', s)
    s = s.replace('\r', '\n')
    return s.replace('\t', '     ')


def _make_logger():
    logging.basicConfig(
        filename=LOGS_FILE,
        format='%(asctime)s - %(levelname)s -  - %(message)s',
        filemode='a',
        level=logging.INFO
    )
    return logging.getLogger()


class Connection:
    """
    Manages a single Paramiko SSH session for the lifetime of one module call.

    The Transport is opened lazily on the first :meth:`run` call and reused
    for every subsequent command executed during the same module invocation.
    ``__del__`` closes the Transport when the object is garbage-collected at
    the end of the module's ``main()`` function.
    """

    def __init__(self, module, host_ip, user, password, command=None, messages=None):
        """
        :param module:      Ansible module instance (used for host-key-checking env)
        :param str host_ip: Controller IP / hostname
        :param str user:    SSH login user (typically ``pvcroot``)
        :param str password:SSH login password  (never placed on the command line)
        :param str command: CLI command to execute on :meth:`run`
        :param dict messages: ``{pattern: reply}`` map for interactive prompts
        """
        self.module = module
        self.host_ip = host_ip
        self.user = user
        self.password = password
        self.cmd = command
        self.messages = messages or {}
        self.logger = _make_logger()

        # Shared Transport — created once, reused across run() calls.
        self._transport = None

    # ------------------------------------------------------------------
    # Transport lifecycle
    # ------------------------------------------------------------------

    def _get_transport(self):
        """Return the open Transport, creating it on first call."""
        if self._transport is not None and self._transport.is_active():
            return self._transport

        self.logger.info("Opening SSH transport to %s", self.host_ip)
        sock_transport = paramiko.Transport((self.host_ip, 22))
        sock_transport.connect(username=self.user, password=self.password)
        self._transport = sock_transport
        self.logger.info("SSH transport established to %s", self.host_ip)
        return self._transport

    def close(self):
        """Explicitly close the underlying Transport."""
        if self._transport is not None:
            try:
                self._transport.close()
            except Exception:
                pass
            self._transport = None

    def __del__(self):
        self.close()

    # ------------------------------------------------------------------
    # Public interface — called by every module
    # ------------------------------------------------------------------

    def run(self):
        """
        Execute ``self.cmd`` over the shared SSH Transport.

        If ``self.messages`` is non-empty, a PTY channel is used so that
        interactive prompts can be matched and answered.  Otherwise a plain
        ``exec_command`` session is used (simpler, more reliable exit codes).

        :return: ``(exit_code: int, output_lines: list[str])``
        """
        try:
            transport = self._get_transport()
            self.logger.info("Command: %s", self.cmd)

            if self.messages:
                exit_code, stdout = self._run_interactive(transport)
            else:
                exit_code, stdout = self._run_simple(transport)

            self.logger.info("Exit code: %s", exit_code)

            if exit_code == 255:
                return 1, str(CLIError("SSH Connection failed")).split('\n')

            if not stdout:
                stdout = "The command did not return any output"

            lines = clean_output(stdout.strip('\n').strip('\t').strip()).split('\n')
            return exit_code, lines

        except paramiko.AuthenticationException as e:
            self.logger.error("SSH authentication failed: %s", e)
            raise CLIError(f"SSH authentication failed: {e}")
        except paramiko.SSHException as e:
            self.logger.error("SSH error: %s", e)
            raise CLIError(f"SSH error: {e}")
        except Exception as e:
            self.logger.critical("Unexpected error: %s", e)
            raise

    # ------------------------------------------------------------------
    # Internal execution helpers
    # ------------------------------------------------------------------

    def _run_simple(self, transport):
        """
        Run a non-interactive command via ``exec_command``.
        Returns ``(exit_code, stdout_str)``.
        """
        chan = transport.open_session()
        chan.settimeout(_CMD_TIMEOUT)
        chan.exec_command(self.cmd)

        stdout_chunks = []
        stderr_chunks = []

        deadline = time.monotonic() + _CMD_TIMEOUT
        while not chan.exit_status_ready():
            if time.monotonic() > deadline:
                chan.close()
                raise CLIError("Command timed out")
            if chan.recv_ready():
                stdout_chunks.append(chan.recv(4096).decode('utf-8', errors='replace'))
            if chan.recv_stderr_ready():
                stderr_chunks.append(chan.recv_stderr(4096).decode('utf-8', errors='replace'))
            time.sleep(_POLL_INTERVAL)

        # Drain remaining data after exit
        while chan.recv_ready():
            stdout_chunks.append(chan.recv(4096).decode('utf-8', errors='replace'))
        while chan.recv_stderr_ready():
            stderr_chunks.append(chan.recv_stderr(4096).decode('utf-8', errors='replace'))

        exit_code = chan.recv_exit_status()
        chan.close()

        stdout = ''.join(stdout_chunks)
        stderr = ''.join(stderr_chunks)

        # Surface stderr when the command fails and stdout is empty
        if exit_code != 0 and not stdout.strip() and stderr.strip():
            stdout = stderr

        return exit_code, stdout

    def _run_interactive(self, transport):
        """
        Run a command that requires interactive prompt/response via a PTY channel.
        Returns ``(exit_code, stdout_str)``.
        """
        chan = transport.open_session()
        chan.get_pty()
        chan.settimeout(_CMD_TIMEOUT)
        chan.exec_command(self.cmd)

        buf = ''
        deadline = time.monotonic() + _CMD_TIMEOUT

        for pattern, reply in self.messages.items():
            regex = re.compile(pattern, re.IGNORECASE | re.DOTALL)
            matched = False

            while time.monotonic() < deadline:
                if chan.recv_ready():
                    chunk = chan.recv(4096).decode('utf-8', errors='replace')
                    buf += chunk
                    if regex.search(buf):
                        chan.sendall(reply + '\n')
                        self.logger.info("Sent reply for pattern %r", pattern)
                        matched = True
                        break
                if chan.exit_status_ready():
                    break
                time.sleep(_POLL_INTERVAL)

            if not matched:
                self.logger.warning("Pattern %r not matched within timeout", pattern)

        # Drain remaining output
        while not chan.exit_status_ready():
            if time.monotonic() > deadline:
                chan.close()
                raise CLIError("Interactive command timed out")
            if chan.recv_ready():
                buf += chan.recv(4096).decode('utf-8', errors='replace')
            time.sleep(_POLL_INTERVAL)

        while chan.recv_ready():
            buf += chan.recv(4096).decode('utf-8', errors='replace')

        exit_code = chan.recv_exit_status()
        chan.close()

        return exit_code, buf
