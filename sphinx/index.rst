.. wp3 documentation master file, created by
   sphinx-quickstart on Sun Jun  2 19:09:56 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Simulation Data
===============

This document defines data classes and attributes of the objects in a DEM simulation.
It is available in `PDF <https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data/wp3.pdf>`_ and in `HTML <https://on-dem.gricad-pages.univ-grenoble-alpes.fr/model-data/index.html>`_ formats.

System of units
_______________

Physical quantities are assigned to many variables, not units. The actual system of units can be specified as one of the scene's attribute (`scene.units` defines the units for time, length, mass). By convention, the notation for the quantities is:
- time: *T*
- length: *L*
- mass: *M*
- force: *F*

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   basic_types
   scene
   body
   interaction
   model
   bibliography
   
.. .. toctree::
..    :hidden:
..    
..    interaction_full


* :ref:`genindex`

