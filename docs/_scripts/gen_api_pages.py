# !/usr/bin/env python
# encoding: utf-8

"""
Generate the code reference pages and navigation.

Adapted from https://mkdocstrings.github.io/recipes.
"""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

root = 'ckanext'

py_files = sorted(Path(root).rglob('*.py'))

for path in py_files:
    module_path = path.relative_to(root).with_suffix('')
    doc_path = path.relative_to(root).with_suffix('.md')
    full_doc_path = Path('API', doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == '__init__':
        if len(parts) == 1:
            continue
        parts = parts[:-1]
        doc_path = doc_path.with_name('index.md')
        full_doc_path = full_doc_path.with_name('index.md')
    elif parts[-1] == '__main__':
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = '.'.join(parts)
        fd.write(f'::: ckanext.{ident}')

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open('API/index.md', 'w') as nav_file:
    nav_file.writelines(nav.build_literate_nav())
