# Model Data

This project defines generic data structures to exchange DEM simulations data. It is supported by the [ON-DEM network](https://on-dem.atlassian.net/wiki/spaces/Index/overview?homepageId=13304023)

The source code is mirrored in ON-DEM's project at Github.com:
[https://github.com/ON-DEM/ON-DEM-WG3-FileFormat](https://github.com/ON-DEM/ON-DEM-WG3-FileFormat)
and in Gricad's gitlab:
[(https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data)](https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data) where it is built.

The generated pages are located [here](https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data).

## Local build:


```
git clone https://gricad-gitlab.univ-grenoble-alpes.fr/on-dem/model-data.git
cd sphinx
make html
make latexpdf

```
The output is in ```sphinx/build```

The prerequisites are listed [here](https://gricad-gitlab.univ-grenoble-alpes.fr/on-dem/model-data/-/blob/main/Dockerfile).

Alternatively, run the docker image from registry directly:
```
docker run -it gricad-registry.univ-grenoble-alpes.fr/on-dem/model-data:main
```

## Remote build:

 - Click the "edit" button when viewing a source file
 - Edit
 - Type a commit message to explain the change and give a name to the branch (unless you commit to master branch)
 - Click "commit"
 
 The new html/pdf should appear in the [job artifacts](https://gricad-gitlab.univ-grenoble-alpes.fr/on-dem/model-data/-/pipelines) after ~30sec. After a commit to master branch it may need a few minutes for the update to be reflected in [the public pages](https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data).
