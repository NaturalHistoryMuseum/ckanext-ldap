# Contributing

Hi! Thanks for considering contributing to ckanext-ldap. :sauropod:

We welcome suggestions, bug reports, and code or documentation changes. This document will give you a quick overview of how to make one of these contributions.

If you're completely new to Git, GitHub, or contributing to open source, you might find it helpful to read some other material first, like [W3's Git Tutorial](https://www.w3schools.com/git), [GitHub Quickstart](https://docs.github.com/en/get-started/quickstart), or [How to Contribute to Open Source](https://opensource.guide/how-to-contribute). This document does assume some familiarity with these concepts for brevity, but we're happy to help anyone who's new or needs further clarification.


## Quick links

- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Support](./.github/SUPPORT.md)
- [Issues](https://github.com/NaturalHistoryMuseum/ckanext-ldap/issues)


## Table of contents

1. [Introduction](#introduction)
2. [Questions](#questions)
3. [Suggestions and bug reports](#suggestions-and-bug-reports)
4. [Commits and pull requests](#commits-and-pull-requests)
   1. [Commits](#commits)
   2. [Code changes and style guide](#code-changes-and-style-guide)
   3. [Documentation changes](#documentation-changes)


## Introduction

### Code of Conduct

We have a [Code of Conduct](./CODE_OF_CONDUCT.md), which all contributors and community participants are expected to adhere to.

### About this repository

This repository contains the code for an extension/plugin for a larger system called [CKAN](https://github.com/ckan/ckan); it is not a standalone project.

### Official maintainers

This extension and [several others](https://github.com/search?q=topic:ckan+org:NaturalHistoryMuseum&type=repositories) are maintained by the Data Portal team at the Natural History Museum, London. This is a very small team, so contributions are very welcome!

The current core team consists of:
- Josh ([@jrdh](https://github.com/jrdh)) - Technical Lead
- Ginger ([@alycejenni](https://github.com/alycejenni)) - Senior Software Engineer


## Questions

Before asking your question, have you checked:
- [The README](./README.md)
- [The documentation](https://ckanext-ldap.readthedocs.io)
- [The existing issues](https://github.com/NaturalHistoryMuseum/ckanext-ldap/issues?q=is:issue)
- [CKAN's documentation](https://docs.ckan.org/en/latest)

If none of those answer your question, try contacting us before raising it as an issue on GitHub. You can find places to contact us in [SUPPORT.md](./.github/SUPPORT.md).


## Suggestions and bug reports

Suggestions, feature requests, and bug reports are all submitted as [GitHub issues](https://docs.github.com/en/issues).

See GitHub's documentation for the basics on [how to create an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/creating-an-issue). Before you create an issue, please check the [existing issues](https://github.com/NaturalHistoryMuseum/ckanext-ldap/issues?q=is:issue) to see if it's already been raised.

### Good bug reports

We've provided a template for bug reports. It's not 100% necessary to follow this template exactly, but it does demonstrate the kind of information that will be useful to anyone trying to fix the problem. The most key information is anything that will allow someone to try and recreate your issue on their own system.

### Good feature suggestions

We've also provided a template for feature suggestions. This is fairly sparse, and again isn't completely necessary to follow exactly. Please just try to provide as much information about your idea as possible.


## Commits and pull requests

If you want to contribute a change to any of the files in the repository, whether it's code, documentation, or repository meta files like `.gitignore`, you'll need to make commits and pull requests.

The process is generally as follows:

1. [Fork the repository](https://docs.github.com/en/get-started/quickstart/fork-a-repo).
2. Create a new branch to work on by branching off `dev`. We name ours in the format `user/feature-name`, e.g. `ginger/deprecate-ckanpackager`. Try to only work on one topic (e.g. implementing one feature, or fixing a couple of related bugs) per branch.
3. Make your changes, and commit often; each commit should only contain one change. See below for specifics on how to word your commits.
4. Push your changes back to your fork.
5. [Open a pull request](https://docs.github.com/en/get-started/quickstart/contributing-to-projects#making-a-pull-request) in this repository, with the base branch set to **dev** and the compare branch set to your new branch. Provide a summary of your changes in the description.
6. There are several automated checks that will run when you open the pull request. Try to make all of them pass. If you do not at least _attempt_ to make them pass, we will not merge your pull request.
   1. Tests. Update them so that they pass, if necessary. New tests are always welcome in any pull request, but if you have added a new feature that has decreased the coverage, new tests are required.
   2. Commit format validation. If you have not followed the conventional commits format for one or more of your commits, this will fail.
   3. Code format validation. If you have not formatted your code correctly (using Ruff, docformatter, and/or Prettier), this will fail.
7. Wait for feedback from one of the core maintainers. If it's been a week or so and we haven't responded, we may not have seen it. You can find other places to contact us in [SUPPORT.md](./.github/SUPPORT.md).

### Commits

Our commits follow the [Conventional Commits](https://www.conventionalcommits.org) style for consistency and to make it easy to generate changelogs. Please follow this style when you make your commits. We have our own slightly tweaked version of the default style called [`cz-nhm`](https://github.com/NaturalHistoryMuseum/cz-nhm). It's very similar with just a few additions.

Commits are formatted as follows - not every line is required:
```
<type>(<scope>): <subject>
<BLANK LINE>
BREAKING CHANGE: <subject>
<BLANK LINE>
<body>
<BLANK LINE>
Closes: <issues>
```

e.g.
```
fix(actions): write a short lowercase description of what you did

Give a bit more context or detail about the changes.

Closes: #1, #3
```

Or, a very basic but still completely valid commit:
```
feat: add an exciting new feature
```

The tools described below are very useful for generating these messages and sticking to the structure, so we _highly_ recommend using them.

#### Tools

We use a few tools to help us with code standardisation and keeping to the conventional commits style. When making a commit, the two key tools to know about are:

1. [commitizen](https://commitizen-tools.github.io/commitizen)
2. [pre-commit](https://pre-commit.com)

Both tools are Python-based and can be installed with `pip`. You'll probably want to use something like [pipx](https://pypa.github.io/pipx) or [venv](https://docs.python.org/3/library/venv.html) instead of installing them globally, but for simplicity, the instructions below are just for pip.

##### commitizen

commitizen is a CLI tool for creating commits in the conventional commits style.

To install with `pip`:
```shell
# NB: cz-nhm must be installed in the same environment as commitizen
pip install commitizen cz-nhm
```

Then to make a commit:
```shell
cz c
# and follow the prompts
```

##### pre-commit

pre-commit is a tool that runs a variety of checks and modifications before a commit is made. You can check the [.pre-commit-config.yaml](./.pre-commit-config.yaml) file to see exactly what it's currently configured to do for this repository, but of particular note:

- reformats Python code with [Ruff](https://docs.astral.sh/ruff)
- reformats JavaScript and stylesheets with [Prettier](https://prettier.io)
- reformats docstrings with [docformatter](https://github.com/PyCQA/docformatter)
- checks your commit message is correcly formatted

To install with `pip`:
```shell
pip install pre-commit
```

When installed, the checks will be run on all staged files when you try to make a commit. If any of them fail or make any modifications, the commit will be abandoned and you will have to write the message again. Because of this, it's probably best to run the checks on the staged files manually before you even attempt a commit:
```shell
pre-commit run
```

Don't forget to stage any modifications that it makes! Once it runs without failing, then you can make your commit.

Something to remember is that empty docstrings will cause conflicts between Ruff and docformatter and the checks will fail repeatedly - so don't leave your docstrings empty!

### Code changes and style guide

We generally use external style guides and tools to help us maintain standardised code. Ruff and Prettier will be run with pre-commit.

#### Python

We use [Ruff](https://docs.astral.sh/ruff) to format our code, using defaults for everything except quote style (we use single quotes).

We also _mostly_ use [CKAN's style](http://docs.ckan.org/en/latest/contributing/python.html), with the following exceptions:
- prefer `f''` strings over `.format()`
- don't use `u''` strings
- use double quotes for docstrings, not single quotes

#### JavaScript and stylesheets (CSS, LESS, etc)

We use [Prettier](https://prettier.io) to format these files. As with Ruff, we use defaults for everything except quote style (we use single quotes).

#### Accessibility

Particularly if you're making frontend changes such as modifying HTML, please make sure your changes meet level AA of the [Web Content Accessibility Guidelines (WCAG)](https://www.w3.org/WAI/standards-guidelines/wcag).

### Documentation changes

Our documentation is generated using [MkDocs](https://www.mkdocs.org), then hosted on [Read the Docs](https://about.readthedocs.com). You can view the current documentation for this repository at [ckanext-ldap.readthedocs.io](https://ckanext-ldap.readthedocs.io).

Most of the documentation for this repository is generated automatically by pulling _docstrings_ from the Python code. This documentation is placed in the "API" subfolder in the rendered output.

There are also a few pages written as standalone `.md` files, e.g. [configuration.md](./docs/configuration.md), or as a subfolder, e.g. [usage](./docs/usage/index.md). You can also edit these or create new pages. In most of our extensions these are still very sparse or automatically generated from content in the README, but the extension `ckanext-versioned-datastore` has a [good example of more complex documentation](https://github.com/NaturalHistoryMuseum/ckanext-versioned-datastore/tree/main/docs/usage/downloads).

Once you've made your changes, follow the commit and pull request guidelines as you would for a code change. You will almost certainly be using the `docs:` commit prefix.
