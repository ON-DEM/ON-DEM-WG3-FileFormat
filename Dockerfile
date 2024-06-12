# Dockerfile
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get clean && apt-get update && \
    apt-get install -y \
    python3 python3-sphinx python3-sphinx-automodapi python3-sphinxcontrib.bibtex texlive texlive-latex-extra latexmk graphviz

RUN apt-get autoclean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives/*deb
 
