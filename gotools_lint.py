import sublime
import sublime_plugin
import re
import os

from .golangconfig import setting_value
from .gotools_util import Buffers
from .gotools_util import GoBuffers
from .gotools_util import Logger
from .gotools_util import ToolRunner

# class GotoolsLintOnSave(sublime_plugin.EventListener):

#   def on_post_save(self, view):
#     if not GoBuffers.is_go_source(view): return
#     if not setting_value("lint_on_save")[0]: return
#     if Logger.err: return
#     view.run_command('gotools_lint')

class GotoolsLint(sublime_plugin.TextCommand):
  def is_enabled(self):
    return GoBuffers.is_go_source(self.view)

  def run(self, edit):
    if setting_value("lint_backend")[0] == "golint":
      self.run_golint()
    elif setting_value("lint_backend")[0] == "govet":
      self.run_govet()
    elif setting_value("lint_backend")[0] == "both":
      rc = self.run_govet()
      if rc != 1:
        self.run_golint()
    else:
      sublime.error_message("Must choose a linter: govet or golint or both")
      return

  def run_govet(self):
    command = "go"
    args = ["vet"]

    stdout, stderr, rc = ToolRunner.run(self.view, command, args, timeout=60, cwd=os.path.dirname(self.view.file_name()))

    # Clear previous syntax error marks
    self.view.erase_regions("mark")

    if rc == 1:
      # Show syntax errors and bail
      self.show_syntax_errors(stderr, "^(.*?):(\d+):*(\d*):(.*)$")
    elif rc != 0:
      # Ermmm...
      Logger.log("unknown govet error (" + str(rc) + ") stderr:\n" + stderr)
    else:
      # Everything's good, hide the syntax error panel
      self.view.window().run_command("hide_panel", {"panel": "output.gotools_syntax_errors"})

    return rc

  def run_golint(self):
    command = "golint"
    args = [self.view.file_name()]

    stdout, stderr, rc = ToolRunner.run(self.view, command, args, timeout=60)

    # Clear previous syntax error marks
    self.view.erase_regions("mark")

    if rc != 0:
      # Ermmm...
      Logger.log("unknown golint error (" + str(rc) + ") stderr:\n" + stderr)
      return

    if stdout != "":
      # Show syntax errors and bail
      self.show_syntax_errors(stdout, "^(.*):(\d+):(\d+):(.*)$")
    else:
      # Everything's good, hide the syntax error panel
      self.view.window().run_command("hide_panel", {"panel": "output.gotools_syntax_errors"})

  # Display an output panel containing the syntax errors, and set gutter marks for each error.
  def show_syntax_errors(self, stderr, file_regex,):
    output_view = self.view.window().create_output_panel('gotools_syntax_errors')
    output_view.set_scratch(True)
    output_view.settings().set("result_file_regex", file_regex)
    output_view.run_command("select_all")
    output_view.run_command("right_delete")

    marks = []
    for error in stderr.splitlines():
      match = re.match(file_regex, error)
      if not match or not match.group(2):
        Logger.log("skipping unrecognizable error: " + error)
        continue

      syntax_output = error.replace(match.group(1), self.view.file_name())
      output_view.run_command('append', {'characters': syntax_output})

      row = int(match.group(2))
      pt = self.view.text_point(row-1, 0)
      Logger.log("adding mark at row " + str(row))
      marks.append(sublime.Region(pt))

    self.view.window().run_command("show_panel", {"panel": "output.gotools_syntax_errors"})

    if len(marks) > 0:
      self.view.add_regions("mark", marks, "mark", "dot", sublime.DRAW_STIPPLED_UNDERLINE | sublime.PERSISTENT)
