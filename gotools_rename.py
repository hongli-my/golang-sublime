import sublime
import sublime_plugin
import os

from .gotools_util import Buffers
from .gotools_util import GoBuffers
from .gotools_util import Logger
from .gotools_util import ToolRunner

class GotoolsRenameCommand(sublime_plugin.TextCommand):
  def is_enabled(self):
    return GoBuffers.is_go_source(self.view)

  def run(self, edit):
    initial_text = self.view.substr(self.view.word(self.view.sel()[0].begin()))
    self.view.window().show_input_panel("Go rename:", initial_text, self.do_rename, None, None)

  def do_rename(self, name):
    filename, _row, _col, offset, _offset_end = Buffers.location_at_cursor(self.view)
    args = [
      "-offset", "{file}:#{offset}".format(file=filename, offset=offset),
      "-to", name,
      "-v"
    ]
    output, err, exit = ToolRunner.run(self.view, "gorename", args, timeout=15)

    if exit != 0:
      print("GoTools: Gorename error:\n%s" % err)
      Logger.status("rename failed ({0}): {1}".format(exit, err))
      return
    Logger.status("renamed symbol to {name}".format(name=name))

    panel = self.view.window().create_output_panel('gotools_rename')
    panel.set_scratch(True)
    # TODO: gorename isn't emitting line numbers, so to get clickable
    # referenced we'd need to process each line to append ':N' to make the
    # sublime regex work properly (line number is a required capture group).
    panel.settings().set("result_file_regex", "^\t(.*\.go)$")
    panel.run_command("select_all")
    panel.run_command("right_delete")
    panel.run_command('append', {'characters': err})
    self.view.window().run_command("show_panel", {"panel": "output.gotools_rename"})
