# Mkdocs Framework and Material Theme for the Polkadot Developer Documentation Site

This repo contains the Mkdocs config files, theme overrides, and CSS changes.

- [Mkdocs](https://www.mkdocs.org/)
- [Material for Mkdocs](https://squidfunk.github.io/mkdocs-material/)

The actual content is stored in the `polkadot-docs` repo and pulled in during build.

- [Polkadot Docs](https://github.com/polkadot-developers/polkadot-docs)

## Get Started

### Clone the Repository

So first, lets clone this repository:

```bash
git clone https://github.com/papermoonio/polkadot-mkdocs
cd polkadot-mkdocs
```

### Install Dependencies

To get started you need to have [Mkdocs](https://www.mkdocs.org/) installed. All dependencies can be installed with a single command, you can run:

```bash
pip install -r requirements.txt
```

## Set Up Repository Structure

In order for everything to work correctly, the structure needs to be as follows:

```text
polkadot-mkdocs
|--- /material-overrides/ (folder)
|--- /polkadot-docs/ (repository)
|--- mkdocs.yml
```

Inside the `polkadot-mkdocs` directory just created, clone the [`polkadot-docs` repository](https://github.com/polkadot-developers/polkadot-docs):

```bash
git clone https://github.com/polkadot-developers/polkadot-docs.git
```

## Run the Docs

Now in the `polkadot-mkdocs` folder, you can build the site by running:

```bash
mkdocs serve
```

> **_NOTE:_** To improve build times, you can disable the git revision plugin by running the following command before you serve the docs: `export ENABLED_GIT_REVISION_DATE=false`.

After a successful build, the site should be available locally at `http://127.0.0.1:8000`.
