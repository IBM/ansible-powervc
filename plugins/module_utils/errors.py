"""
This module handles all errors in ssh CLI execution
"""
import re

ANSIBLE_ESCAPE = re.compile(r'\s*\\(?:x|u)?\x1b\[[0-9;]*[A-GJKSTfsu]\s*')


class CLIError():
    """
    Class to handle errors in ssh CLI Execution
    """

    def __init__(self, message=None):
        cleaned = self._clean_message(message or "")
        self.message = cleaned

    def __str__(self):
        return self._clean_message(self.message)

    def __repr__(self):
        return f"CLIError({self._clean_message(self.message)!r})"

    @staticmethod
    def _clean_message(msg):
        # Remove ANSIBLEescapes
        msg = ANSIBLE_ESCAPE.sub('', msg)
        # Normalize newlines
        msg = msg.replace('\r', '\n')
        # Replace tabs with spaces
        msg = msg.replace('\t', '     ')
        return "Command returned non zero exit code:\n" + msg
