"""
This module handles all errors in ssh CLI execution
"""
import re

ANSIBLE_ESCAPE = re.compile(r'\s*\\(?:x|u)?\x1b\[[0-9;]*[A-GJKSTfsu]\s*')


class CLIError(Exception):
    """
    Exception raised when an SSH CLI command fails or the connection errors.
    Inherits from Exception so it can be caught with a plain ``except Exception``.
    """

    def __init__(self, message=None):
        cleaned = self._clean_message(message or "")
        self.message = cleaned
        super().__init__(cleaned)

    def __str__(self):
        return self._clean_message(self.message)

    def __repr__(self):
        return f"CLIError({self._clean_message(self.message)!r})"

    @staticmethod
    def _clean_message(msg):
        msg = ANSIBLE_ESCAPE.sub('', msg)
        msg = msg.replace('\r', '\n')
        msg = msg.replace('\t', '     ')
        return "Command returned non zero exit code:\n" + msg
