# Model Data

This project defines generic data structures to exchange DEM simulations data. It is supported by the [ON-DEM network](https://on-dem.atlassian.net/wiki/spaces/Index/overview?homepageId=13304023)

The source code is mirrored in ON-DEM's project at Github.com:
[https://github.com/ON-DEM/ON-DEM-WG3-FileFormat](https://github.com/ON-DEM/ON-DEM-WG3-FileFormat)
and in Gricad's gitlab:
[https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data](https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data)

The generated pages are located on [github](https://on-dem.github.io/ON-DEM-WG3-FileFormat/) and on [gitlab](https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data).

## Local build

It should be noted that for a local build sphinx needs to be installed. This can be done by
```
pip install sphinx
pip install sphinx-automodapi
pip install sphinxcontrib-bibtex
```
For debian distributions, the prerequisites (also visible [here](https://gricad-gitlab.univ-grenoble-alpes.fr/on-dem/model-data/-/blob/main/Dockerfile)) are
```
apt-get install python3 python3-sphinx python3-sphinx-automodapi python3-sphinxcontrib.bibtex texlive texlive-latex-extra latexmk graphviz
```

Clone this repository and move to the folder `sphinx`:
```
git clone https://github.com/ON-DEM/ON-DEM-WG3-FileFormat.git
cd sphinx
```

Then, build the documentation:

In unix (Linux, MacOS):
```bash
make html
make latexpdf
```

or in windows:
```
python -m sphinx -b html . build
```

The output is in ```sphinx/build```

### in case of issues with the sphinx version

1. run the docker image from registry directly:
```
docker run -it gricad-registry.univ-grenoble-alpes.fr/on-dem/model-data:main
```
or 
```
docker pull ghcr.io/on-dem/on-dem-wg3-fileformat:sha-d2bc1b2
docker run -it ghcr.io/on-dem/on-dem-wg3-fileformat:sha-d2bc1b2 bash
```
Then reproduce the steps above.

2. Or, use a virtual environment with the same sphinx version

```
python3 -m venv .venv-docs
source .venv-docs/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-docs.txt
```

Then build with:

```
cd sphinx
source ../.venv-docs/bin/activate
make html
make latexpdf
```

Note: `.venv-docs/` is ignored by git and should not be committed.

## Remote build:

 - Click the "edit" button when viewing a source file
 - Edit
 - Type a commit message to explain the change and give a name to the branch (unless you commit to master branch)
 - Click "commit"
 
 The new html/pdf should appear in the [job artifacts](https://gricad-gitlab.univ-grenoble-alpes.fr/on-dem/model-data/-/pipelines) after ~30sec. After a commit to master branch it may need a few minutes for the update to be reflected in [the public pages](https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data).

## Contributing

### Adding a model
1. Select a model you wish to add to the OPEN File Format.
2. Figure out which variables are needed for the interactions: Most likely, some of the variables are already defined somewhere.
3. Explore the file existing format specifications, check: [Materials data](./materials.py), [Interaction data](./interaction.py) and [Interaction models](./model.py).
4. Check the "VARIABLES" tab on [this spreadsheet](https://docs.google.com/spreadsheets/d/1UALlIVtaxdMpy1aX-9HdBKr23dg9fmQPuUDZsQNo8TI/edit?gid=0#gid=0). If the variables of your model are already included, then use the variable name(s), and symbols decided. If not there, make a proposal following the agreed rules (snake_case, LaTeX format for symbols and quantities).
5. Look at [interaction.py](./interaction.py): Check if your model can inherit from existing models, some variables might need to be included both in [interaction.py](./interaction.py) to insure code interoperability.
6. Add the necessary data to [materials.py](./materials.py), check if your material can inherit from existing materials. Some variables might need to be included both in [materials.py](./materials.py) to insure code interoperability. If you need to add variables using the names and symbols decided/proposed.
7. Add model description to [model.py](./model.py).
8. Generate the pages locally [(instructions to Local build)](#local-build) to check that the changes that you made look as expected.
9. Create a new branch (with a meaningful name 🙏) with your addition (following the steps below) and create a merge request after you finish adding things.