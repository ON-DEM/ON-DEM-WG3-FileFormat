# Model Data

This project defines generic data structures to exchange DEM simulations data. It is supported by the [ON-DEM network](https://on-dem.atlassian.net/wiki/spaces/Index/overview?homepageId=13304023)

The source code is mirrored in ON-DEM's project at Github.com:
[https://github.com/ON-DEM/ON-DEM-WG3-FileFormat](https://github.com/ON-DEM/ON-DEM-WG3-FileFormat)
and in Gricad's gitlab:
[(https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data)](https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data) where it is built.

The generated pages are located [here](https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data).


## Local build:

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

Then:

```
git clone https://github.com/ON-DEM/ON-DEM-WG3-FileFormat.git
cd sphinx
make html
make latexpdf

```
The output is in ```sphinx/build```

### in case of issues with the sphinx version

1. run the docker image from registry directly:
```
docker run -it gricad-registry.univ-grenoble-alpes.fr/on-dem/model-data:main
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
