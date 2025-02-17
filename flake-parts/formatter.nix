{ ... }:
{
  perSystem =
    {
      config,
      self',
      inputs',
      pkgs,
      system,
      ...
    }:
    let
      fmtWidth = 120;
    in
    {

      treefmt = {

        projectRootFile = ".git/config";

        settings = {

          global.on-unmatched = "warn";
          global.excludes = [
            "*.bak"
            "*.iso"
            "*.jpg"
            "*.ico"
            "*.ox"
            "*.png"
            "*.svg"
            "*.xcf"
            "CNAME"
            "justfile"
            "LICENSE"
          ];

          # formatter = {
          #   toml = {
          #     command = "dprint";
          #     options = [
          #       "fmt"
          #       "--allow-no-files"
          #       "--stdin"
          #     ];
          #     includes = [
          #       "*.toml"
          #       "Cargo.lock"
          #     ];
          #   };

          #   html = {
          #     command = "dprint";
          #     options = [
          #       "fmt"
          #       "--allow-no-files"
          #       "--stdin"
          #     ];
          #     includes = [
          #       "*.html"
          #       "*.hbs"
          #     ];
          #   };

          #   md = {
          #     command = "dprint";
          #     options = [
          #       "fmt"
          #       "--allow-no-files"
          #       "--stdin"
          #     ];
          #     includes = [
          #       "*.md"
          #     ];
          #   };
          # };
        };

        programs = {

          nixfmt = {
            enable = pkgs.lib.meta.availableOn pkgs.stdenv.buildPlatform pkgs.nixfmt-rfc-style.compiler;
            priority = 1;
            package = pkgs.nixfmt-rfc-style;
            width = fmtWidth;
          };

          shellcheck = {
            enable = pkgs.lib.meta.availableOn pkgs.stdenv.buildPlatform pkgs.shellcheck;
            priority = 2;
            package = pkgs.shellcheck;
          };

          rustfmt = {
            enable = pkgs.lib.meta.availableOn pkgs.stdenv.buildPlatform pkgs.rustfmt;
            priority = 3;
            package = pkgs.rustfmt;
          };

          prettier = {
            enable = true;
            package = pkgs.prettierd;
            priority = 4;
            includes = [
              "*.prettierignore"
              "*.atom"
              "*.bash"
              "*.cjs"
              "*.conf"
              "*.css"
              "*.dtd"
              "*.geojson"
              "*.gitignore"
              "*.go"
              "*.hbs"
              "*.html"
              "*.ignore"
              "*.j2"
              "*.java"
              "*.jinja"
              "*.jinja2"
              "*.js"
              "*.jsn"
              "*.json"
              "*.json5"
              "*.jsonc"
              "*.jsx"
              "*.kml"
              "*.kt"
              "*.kts"
              "*.lock"
              "*.md"
              "*.mdx"
              "*.mjs"
              "*.nginx"
              "*.properties"
              "*.props"
              "*.rs"
              "*.rss"
              "*.scss"
              "*.sh"
              "*.svg"
              "*.toml"
              "*.ts"
              "*.tsx"
              "*.vue"
              "*.xml"
              "*.xsd"
              "*.xsl"
              "*.xslt"
              "*.yaml"
              "*.yml"
            ];
            settings = {
              arrowParens = "always";
              bracketSameLine = true;
              bracketSpacing = true;
              cursorOffset = -1;
              editorconfig = false;
              embeddedLanguageFormatting = "auto";
              endOfLine = "auto";
              filepath = null;
              htmlWhitespaceSensitivity = "css";
              insertPragma = false;
              jsxSingleQuote = true;
              overrides = null;
              parser = null;
              pluginSearchDirs = null;
              printWidth = 120;
              proseWrap = "always";
              quoteProps = "as-needed";
              rangeEnd = null;
              rangeStart = null;
              requirePragma = false;
              semi = false;
              singleAttributePerLine = true;
              singleQuote = true;
              tabWidth = 2;
              trailingComma = "all";
              useTabs = false;
              vueIndentScriptAndStyle = false;
              plugins = [
                "@prettier/plugin-xml"
                "prettier-plugin-go-template"
                "prettier-plugin-ignore"
                "prettier-plugin-java"
                "prettier-plugin-jinja-template"
                "prettier-plugin-json"
                "prettier-plugin-jsonc"
                "prettier-plugin-kotlin"
                "prettier-plugin-lock"
                "prettier-plugin-nginx"
                "prettier-plugin-prettierignore"
                "prettier-plugin-properties"
                "prettier-plugin-rust"
                "prettier-plugin-sh"
                "prettier-plugin-toml"
              ];

            };
          };

          dprint = {
            enable = false;
            package = pkgs.dprint;
            priority = 5;
            settings = {
              incremental = true;
              indentWidth = 2;
              lineWidth = 120;
              newLineKind = "auto";
              useTabs = false;
            };
          };

        };

      };
    };
}
