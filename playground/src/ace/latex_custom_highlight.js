import ace from "ace-builds/src-noconflict/ace"

// Registriere neuen Modus unter 'ace/mode/latex-custom'
ace.define("ace/mode/latex_custom", ["require", "exports", "module", "ace/lib/oop", "ace/mode/text", "ace/mode/text_highlight_rules"], function (require, exports, module) {
  const oop = require("ace/lib/oop")
  const TextMode = require("ace/mode/text").Mode
  const TextHighlightRules = require("ace/mode/text_highlight_rules").TextHighlightRules

  class LatexHighlightRules extends TextHighlightRules {
    constructor() {
      super()
      this.$rules = {
        start: [
          {
            token: "heading", // Für \section und \subsection
            regex: /\\(?:sub)*section\*?\{.*?\}/
          },
          {
            token: "environment.special", // Für \begin{DEF} etc.
            regex: /\\begin\{(?:DEF|PROP|REM|THEO|EXA|KORO)\}/
          },
          {
            token: "environment.special", // Für \end{DEF} etc.
            regex: /\\end\{(?:DEF|PROP|REM|THEO|EXA|KORO)\}/
          },
          {
            token: "text", // Fallback für alles andere
            regex: ".+"
          }
        ]
      }
      this.normalizeRules()
    }
  }

  const Mode = function () {
    this.HighlightRules = LatexHighlightRules
  }
  oop.inherits(Mode, TextMode)

  exports.Mode = Mode
})
