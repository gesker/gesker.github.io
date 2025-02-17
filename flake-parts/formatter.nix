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

          formatter = {
            toml = {
              command = "dprint";
              options = [
                "fmt"
                "--stdin"
              ];
              includes = [
                "*.toml"
                "Cargo.lock"
              ];
            };

            html = {
              command = "dprint";
              options = [
                "fmt"
                "--stdin"
              ];
              includes = [
                "*.html"
                "*.hbs"
              ];
            };
          };
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

          dprint = {
            enable = pkgs.lib.meta.availableOn pkgs.stdenv.buildPlatform pkgs.dprint;
            priority = 3;
            package = pkgs.dprint;
          };

          prettier = {
            enable = pkgs.lib.meta.availableOn pkgs.stdenv.buildPlatform pkgs.prettierd;
            priority = 4;
            package = pkgs.prettierd;
            settings = {
              printWidth = fmtWidth;
            };
          };

          rustfmt = {
            enable = pkgs.lib.meta.availableOn pkgs.stdenv.buildPlatform pkgs.rustfmt;
            priority = 5;
            package = pkgs.rustfmt;
          };

          # dprint = {
          #   enable = true;
          #   package = pkgs.dprint;
          #   priority = 1;
          #   settings = {
          #     incremental = true;
          #     indentWidth = 2;
          #     lineWidth = 120;
          #     newLineKind = "auto";
          #     useTabs = false;
          #     plugins = [
          #       "https://plugins.dprint.dev/dockerfile-0.3.2.wasm"
          #       "https://plugins.dprint.dev/exec-0.5.0.json@8d9972eee71fa1590e04873540421f3eda7674d0f1aae3d7c788615e7b7413d0"
          #       "https://plugins.dprint.dev/g-plane/malva-v0.10.1.wasm"
          #       "https://plugins.dprint.dev/g-plane/markup_fmt-v0.13.0.wasm"
          #       "https://plugins.dprint.dev/g-plane/pretty_graphql-v0.2.0.wasm"
          #       "https://plugins.dprint.dev/g-plane/pretty_yaml-v0.5.0.wasm"
          #       "https://plugins.dprint.dev/json-0.19.3.wasm"
          #       "https://plugins.dprint.dev/jupyter-0.1.4.wasm"
          #       "https://plugins.dprint.dev/markdown-0.17.8.wasm"
          #       "https://plugins.dprint.dev/prettier-0.46.1.json@e5bd083088a8dfc6e5ce2d3c9bee81489b065bd5345ef55b59f5d96627928b7a"
          #       "https://plugins.dprint.dev/roslyn-0.18.0.json@9586754a7e586ccda5dba4e694c0f225aabde63720c905dd85e02453b6f5e5de"
          #       "https://plugins.dprint.dev/ruff-0.3.9.wasm"
          #       "https://plugins.dprint.dev/toml-0.6.2.wasm"
          #       "https://plugins.dprint.dev/typescript-0.93.0.wasm"

          #     ];
          #   };
          # };

          #   prettier = {
          #     enable = true;
          #     package = pkgs.prettierd;
          #     priority = 2;
          #     includes = [
          #       "*.prettierignore"
          #       "*.atom"
          #       "*.bash"
          #       "*.cjs"
          #       "*.conf"
          #       "*.css"
          #       "*.dtd"
          #       "*.geojson"
          #       "*.gitignore"
          #       "*.go"
          #       "*.html"
          #       "*.ignore"
          #       "*.j2"
          #       "*.java"
          #       "*.jinja"
          #       "*.jinja2"
          #       "*.js"
          #       "*.jsn"
          #       "*.json"
          #       "*.json5"
          #       "*.jsonc"
          #       "*.jsx"
          #       "*.kml"
          #       "*.kt"
          #       "*.kts"
          #       "*.lock"
          #       "*.md"
          #       "*.mdx"
          #       "*.mjs"
          #       "*.nginx"
          #       "*.properties"
          #       "*.props"
          #       "*.rs"
          #       "*.rss"
          #       "*.scss"
          #       "*.sh"
          #       "*.svg"
          #       "*.toml"
          #       "*.ts"
          #       "*.tsx"
          #       "*.vue"
          #       "*.xml"
          #       "*.xsd"
          #       "*.xsl"
          #       "*.xslt"
          #       "*.yaml"
          #       "*.yml"
          #     ];
          #     settings = {
          #       arrowParens = "always";
          #       bracketSameLine = true;
          #       bracketSpacing = true;
          #       cursorOffset = -1;
          #       editorconfig = false;
          #       embeddedLanguageFormatting = "auto";
          #       endOfLine = "auto";
          #       filepath = null;
          #       htmlWhitespaceSensitivity = "css";
          #       insertPragma = false;
          #       jsxSingleQuote = true;
          #       overrides = null;
          #       parser = null;
          #       pluginSearchDirs = null;
          #       printWidth = 120;
          #       proseWrap = "always";
          #       quoteProps = "as-needed";
          #       rangeEnd = null;
          #       rangeStart = null;
          #       requirePragma = false;
          #       semi = false;
          #       singleAttributePerLine = true;
          #       singleQuote = true;
          #       tabWidth = 2;
          #       trailingComma = "all";
          #       useTabs = false;
          #       vueIndentScriptAndStyle = false;
          #       plugins = [
          #         "@prettier/plugin-xml"
          #         "prettier-plugin-go-template"
          #         "prettier-plugin-ignore"
          #         "prettier-plugin-java"
          #         "prettier-plugin-jinja-template"
          #         "prettier-plugin-json"
          #         "prettier-plugin-jsonc"
          #         "prettier-plugin-kotlin"
          #         "prettier-plugin-lock"
          #         "prettier-plugin-nginx"
          #         "prettier-plugin-prettierignore"
          #         "prettier-plugin-properties"
          #         "prettier-plugin-rust"
          #         "prettier-plugin-sh"
          #         "prettier-plugin-toml"
          #       ];

          #     };
          #   };
          # };

        };

      };
    };
}
