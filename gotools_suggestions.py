import sublime
import sublime_plugin
import json
import os
from .golangconfig import setting_value

from .gotools_util import Buffers
from .gotools_util import GoBuffers
from .gotools_util import Logger
from .gotools_util import ToolRunner

class GotoolsSuggestions(sublime_plugin.EventListener):
  CLASS_SYMBOLS = {
    "func": "ƒ",
    "var": "ν",
    "type": "ʈ",
    "package": "ρ"
  }

  def on_query_completions(self, view, prefix, locations):
    if not GoBuffers.is_go_source(view): return
    if not setting_value("autocomplete")[0]: return

    gocodeFlag = ["-f=json", "-sock=none"] if setting_value("gocode_client_mode")[0] else ["-f=json"]
    suggestionsJsonStr, stderr, rc = ToolRunner.run(view, "gocode", gocodeFlag + ["autocomplete", view.file_name(), str(locations[0])], stdin=Buffers.buffer_text(view))

    suggestionsJson = json.loads(suggestionsJsonStr)

    Logger.log("DEBUG: gocode output: " + suggestionsJsonStr)

    if rc != 0:
      Logger.status("no completions found: " + str(e))
      return []

    if len(suggestionsJson) > 0:
      return ([GotoolsSuggestions.build_suggestion(j) for j in suggestionsJson[1]], sublime.INHIBIT_WORD_COMPLETIONS)
    else:
      return []

  @staticmethod
  def build_suggestion(json):
    label = '{0: <30.30} {1: <40.40} {2}'.format(
      json["name"],
      json["type"],
      GotoolsSuggestions.CLASS_SYMBOLS.get(json["class"], "?"))
    return (label, json["name"])
