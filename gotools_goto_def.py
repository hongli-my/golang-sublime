import sublime
import sublime_plugin
import os
import json

from .gotools_util import Buffers
from .gotools_util import GoBuffers
from .gotools_util import Logger
from .gotools_util import ToolRunner

class GotoolsGotoDef(sublime_plugin.TextCommand):
  def is_enabled(self):
    return GoBuffers.is_go_source(self.view)

  # Capture mouse events so users can click on a definition.
  def want_event(self):
    return True

  def run(self, edit, event=None):
    filename, row, col, offset, offset_end = Buffers.location_at_cursor(self.view)

    try:
      file, row, col = self.get_guru_location(filename, offset)
    except Exception as e:
      Logger.status(str(e))
      return

    if not os.path.isfile(file):
      Logger.log("WARN: file indicated by guru not found: " + file)
      Logger.status("guru failed: Please enable debugging and check console log")
      return

    Logger.log("opening definition at " + file + ":" + str(row) + ":" + str(col))
    w = self.view.window()
    new_view = w.open_file(file + ':' + str(row) + ':' + str(col), sublime.ENCODED_POSITION)
    group, index = w.get_view_index(new_view)
    if group != -1:
      w.focus_group(group)

  def get_guru_location(self, filename, offset):
    args = ["-json", "definition", filename+":#"+str(offset)]

    location, err, rc = ToolRunner.run(self.view, "guru", args)
    if rc != 0:
      raise Exception("no definition found")

    Logger.log("guru output:\n" + location.rstrip())

    # cut anything prior to the first path separator
    location = json.loads(location.rstrip())['objpos'].rsplit(":", 2)

    if len(location) != 3:
      raise Exception("no definition found")

    file = location[0]
    row = int(location[1])
    col = int(location[2])

    return [file, row, col]
