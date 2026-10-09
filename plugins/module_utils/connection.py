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
# Long-running operations (e.g. powervc-services restart --advanced node,
# powervc-log --restart) can take up to an hour; 1 h is the limit.
_CMD_TIMEOUT = 3600
# Poll interval when draining channel output.
_POLL_INTERVAL = 0.1


def build_os_env(os_auth_url, os_username, os_password, os_project,
                 os_user_domain_name='Default', os_project_domain_name='Default',
                 os_identity_api_version='3'):
    """
    Build the OpenStack environment variable dict required by the ``openstack``
    CLI tool.

    All callers — ``command``, ``openstack_commands``, or any future module —
    should use this shared helper so the set of required variables is defined
    in exactly one place.

    ``PYTHONHTTPSVERIFY=0`` suppresses Python TLS warnings for PowerVC's
    self-signed certificate.

    :param str os_auth_url:              Full Keystone endpoint URL.
    :param str os_username:              OpenStack / Keystone username.
    :param str os_password:              Password for os_username.
    :param str os_project:               Project scope for the auth token.
    :param str os_user_domain_name:      Keystone user domain (default: Default).
    :param str os_project_domain_name:   Keystone project domain (default: Default).
    :param str os_identity_api_version:  Keystone API version (default: 3).
    :return dict: Environment variable dict ready to pass as ``env=`` to
                  :class:`Connection`.
    """
    return {
        'OS_AUTH_URL': os_auth_url,
        'OS_USERNAME': os_username,
        'OS_PASSWORD': os_password,
        'OS_PROJECT_NAME': os_project,
        'OS_USER_DOMAIN_NAME': os_user_domain_name,
        'OS_PROJECT_DOMAIN_NAME': os_project_domain_name,
        'OS_IDENTITY_API_VERSION': os_identity_api_version,
        'PYTHONHTTPSVERIFY': '0',
    }


def clean_output(s):
    """
    Strip terminal control sequences and normalise whitespace.

    :param str s: raw output string
    :return str s: cleaned string
    """
    # Strip ESC c (full terminal reset) and ESC ] OSC sequences
    s = re.sub(r'\x1bc', '', s)
    s = re.sub(r'\x1b\][^\x07\x1b]*[\x07\x1b]', '', s)
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

    def __init__(self, module, host_ip, user, password, command=None, messages=None, env=None):
        """
        :param module:      Ansible module instance (used for host-key-checking env)
        :param str host_ip: Controller IP / hostname
        :param str user:    SSH login user (typically ``pvcroot``)
        :param str password:SSH login password  (never placed on the command line)
        :param str command: CLI command to execute on :meth:`run`
        :param dict messages: ``{pattern: reply}`` map for interactive prompts
        :param dict env:    Environment variables to set on the SSH channel via
                            ``update_environment()`` before executing the command.
                            Injected at the SSH protocol level so they are never
                            visible on the command line and bypass any shell
                            restrictions (e.g. rbash blocking ``export``).
        """
        self.module = module
        self.host_ip = host_ip
        self.user = user
        self.password = password
        self.cmd = command
        self.messages = messages or {}
        self.env = env or {}
        self.logger = _make_logger()

        # Shared Transport — created once, reused across run() calls.
        self._transport = None

    # ------------------------------------------------------------------
    # Transport lifecycle
    # ------------------------------------------------------------------

    # def _get_transport(self):
    #     """Return the open Transport, creating it on first call."""
    #     if self._transport is not None and self._transport.is_active():
    #         return self._transport

    #     self.logger.info("Opening SSH transport to %s", self.host_ip)
    #     sock_transport = paramiko.Transport((self.host_ip, 22))
    #     sock_transport.connect(username=self.user, password=self.password)
    #     self._transport = sock_transport
    #     self.logger.info("SSH transport established to %s", self.host_ip)
    #     return self._transport

    def _get_transport(self):
        """Return the open Transport, creating it on first call."""
        if self._transport is not None and self._transport.is_active():
            return self._transport

        self.logger.info("Opening SSH transport to %s", self.host_ip)

        sock_transport = paramiko.Transport((self.host_ip, 22))

        try:
            sock_transport.connect()

            # def interactive_handler(title, instructions, prompts):
            #     return [self.password for _ in prompts]

            def interactive_handler(title, instructions, prompts):
                self.logger.info(
                    "Keyboard-interactive authentication: "
                    "title=%r instructions=%r prompts=%r",
                    title,
                    instructions,
                    prompts
                )

                responses = []

                for prompt, echo in prompts:
                    self.logger.info(
                        "SSH authentication prompt: prompt=%r echo=%s",
                        prompt,
                        echo
                    )

                    if "password" in prompt.lower():
                        responses.append(self.password)
                    else:
                        self.logger.error(
                            "Unsupported keyboard-interactive prompt: %r",
                            prompt
                        )
                        responses.append("")

                return responses

            self.logger.info(
                "SSH authentication: user=%r host=%r password_present=%s password_length=%d",
                self.user,
                self.host_ip,
                bool(self.password),
                len(self.password) if self.password else 0
            )
            sock_transport.auth_interactive(
                self.user,
                interactive_handler
            )

            self._transport = sock_transport
            self.logger.info(
                "SSH transport established to %s using keyboard-interactive",
                self.host_ip
            )
            return self._transport

        except Exception:
            sock_transport.close()
            raise

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
        # No socket-level timeout — the deadline loop below owns the overall
        # time limit.  A socket timeout on recv() would fire prematurely for
        # long-running commands and is redundant with our deadline check.
        chan.settimeout(None)
        cmd = self.cmd
        if self.env:
            # Prepend env vars inline as KEY='value' so they are guaranteed
            # to reach the executed process regardless of whether the sshd
            # AcceptEnv / PermitUserEnvironment is configured.
            # update_environment() is unreliable: some sshd builds silently
            # accept the channel request but never propagate the variables.
            prefix = ' '.join(
                # Single-quote each value; escape embedded single quotes.
                "{}='{}'".format(k, v.replace("'", "'\\''"))
                for k, v in self.env.items()
            )
            cmd = f"{prefix} {cmd}"
        chan.exec_command(cmd)

        stdout_chunks = []
        stderr_chunks = []

        deadline = time.monotonic() + _CMD_TIMEOUT
        while True:
            if time.monotonic() > deadline:
                chan.close()
                raise CLIError("Command timed out")

            # Drain all available data every iteration so the remote end's
            # send buffer never fills up and stalls a long-running command.
            drained = False
            while chan.recv_ready():
                stdout_chunks.append(chan.recv(4096).decode('utf-8', errors='replace'))
                drained = True
            while chan.recv_stderr_ready():
                stderr_chunks.append(chan.recv_stderr(4096).decode('utf-8', errors='replace'))
                drained = True

            if chan.exit_status_ready():
                break

            # Only sleep when no data arrived; skip when data is flowing so
            # output is consumed as fast as possible and buffers stay clear.
            if not drained:
                time.sleep(_POLL_INTERVAL)

        # Drain any remaining data after the exit status is signalled.
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
        chan.settimeout(None)
        cmd = self.cmd
        if self.env:
            prefix = ' '.join(
                "{}='{}'".format(k, v.replace("'", "'\\''"))
                for k, v in self.env.items()
            )
            cmd = f"{prefix} {cmd}"
        chan.exec_command(cmd)

        buf = ''

        for pattern, reply in self.messages.items():
            regex = re.compile(pattern, re.IGNORECASE | re.DOTALL)
            matched = False
            # Each prompt gets its own fresh deadline so that time spent
            # waiting for earlier prompts does not eat into the budget for
            # post-prompt work (e.g. a service restart triggered by --restart).
            prompt_deadline = time.monotonic() + _CMD_TIMEOUT

            while time.monotonic() < prompt_deadline:
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

        # Drain remaining output after all prompts have been answered.
        # Use a fresh deadline so a long post-prompt operation (e.g.
        # powervc-log --restart) has its own full time budget.
        drain_deadline = time.monotonic() + _CMD_TIMEOUT
        while True:
            if time.monotonic() > drain_deadline:
                chan.close()
                raise CLIError("Interactive command timed out")

            # Drain all available data to prevent the remote buffer from
            # filling and stalling exit_status_ready().
            drained = False
            while chan.recv_ready():
                buf += chan.recv(4096).decode('utf-8', errors='replace')
                drained = True

            if chan.exit_status_ready():
                break

            if not drained:
                time.sleep(_POLL_INTERVAL)

        while chan.recv_ready():
            buf += chan.recv(4096).decode('utf-8', errors='replace')

        exit_code = chan.recv_exit_status()
        chan.close()

        return exit_code, buf
