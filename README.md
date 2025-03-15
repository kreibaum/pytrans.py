# Archived

Rewritten in Rust and included directly with https://github.com/kreibaum/pacosako/

# pytrans.py

Turns json translation files into elm code for build time website translation

Intended usage is, that you put pytrans.py on your path and then you can run

```bash
# Rebuild translation file (e.g. when translation changed or in CI)
pytrans.py
# Switch language to Esperanto and rebuild
pytrans.py Esperanto
```

You need to set up a `pytrans.json` configuration file as well as several `LanguageName.json` input files.

Helper functions to find all translation gaps should come later.
