ace.define("ace/mode/latex_custom", [
  "require", "exports", "module",
  "ace/mode/latex", "ace/lib/oop", "ace/mode/text_highlight_rules"
], function (require, exports, module) {
  const LatexMode = require("ace/mode/latex").Mode;
  const oop = require("ace/lib/oop");
  const TextHighlightRules = require("ace/mode/text_highlight_rules").TextHighlightRules;

  const CustomHighlightRules = function () {
    this.$rules = {
      start: [
        {
          token: "heading.section",
          regex: /\\section\*?\{.*?\}/
        },
        {
          token: "heading.subsection",
          regex: /\\subsection\*?\{.*?\}/
        },
        {
          token: "environment.def",
          regex: /\\begin\{(?:DEF|PROP|THEO|LEM|REM|EXA|KORO)\}\{.*?\}\{.*?\}/
        },
        {
          token: "environment.def",
          regex: /\\end\{(?:DEF|PROP|THEO|LEM|REM|EXA|KORO)\}/
        },
        {
          token: "text",
          regex: ".+"
        }
      ]
    };
    this.normalizeRules();
  };
  oop.inherits(CustomHighlightRules, TextHighlightRules);

  const CustomLatexMode = function () {
    LatexMode.call(this);
    this.HighlightRules = CustomHighlightRules;
  };
  oop.inherits(CustomLatexMode, LatexMode);

  exports.Mode = CustomLatexMode;
});
