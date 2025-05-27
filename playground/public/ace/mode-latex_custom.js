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
          token: "environment.envline",
          regex: /\\begin\{(?:DEF|PROP|THEO|LEM|REM|EXA|KORO)\}\{.*?\}\{.*?\}/,
          next: "envBody"
        },
        {
          token: "text",
          regex: ".+"
        }
      ],
      envBody: [
        {
          token: "environment.envline", // gleicher Token wie begin
          regex: /\\end\{(?:DEF|PROP|THEO|LEM|REM|EXA|KORO)\}/,
          next: "start"
        },
        {
          token: "environment.body",
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
