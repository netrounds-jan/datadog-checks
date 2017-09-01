import subprocess
import sys
import time

from checks import AgentCheck
from utils.timeout import timeout, TimeoutException

# Runs arbitrary commands, but exects that the STDOUT from the process will
# begin with a sigil that denotes the success or failure of the check.
# Config file looks like:
# init_config:
# # Not required for this check
#
# instances:
#     - name: "some.check.name1"
#       command: "/path/to/command with args"
#     - name: "some.check.name2"
#       command: "/path/to/command with args2"
class NagiosRunner(AgentCheck):
  def __init__(self, name, init_config, agentConfig):
    AgentCheck.__init__(self, name, init_config, agentConfig)
    self.last_ts = {}

  def check(self, instance):

    cmd = instance.get('command')
    name = instance.get('name')
    default_timeout = self.init_config.get('default_timeout', 5)
    timeout_seconds = int(instance.get('command_timeout', default_timeout))

    status = AgentCheck.UNKNOWN
    try:
      output = timeout(timeout_seconds)(subprocess.check_output)(cmd, stderr=subprocess.STDOUT, shell=True)
      status = AgentCheck.OK
      self.log.debug("Got OK {0}".format(name))
    except subprocess.CalledProcessError as e:
      # This is thrown if return code is != 0
      ret = e.returncode
      self.log.debug("Got NOK {0}: {1}".format(name, ret))
      if ret == 1:
        status = AgentCheck.WARNING
        output = e.output
      elif ret == 2:
        status = AgentCheck.CRITICAL
        output = e.output
      else:
        status = AgentCheck.UNKNOWN
        output = e.output
    except TimeoutException:
      self.log.warn(
        "Timeout while running `%s` command. Skipping...",
        cmd
      )
      status = AgentCheck.UNKNOWN
      output = "Command timeout."

    self.service_check(
      name,
      status,
      message = output,
      tags = []
    )
