# Building Boundary Regularization Tool

This repository contains a Python-based application for regularizing building boundaries from shapefiles. The tool provides a graphical user interface (GUI) for loading shapefiles, processing building polygons, and visualizing the results.

## Features

- **Shapefile Support**: Load and process shapefiles containing building polygons.
- **Polygon Regularization**: Regularize building boundaries using configurable parameters.
- **Visualization**: View original, simplified, and regularized polygons in the GUI.
- **Batch Processing**: Process multiple polygons in groups or separately.
- **Export Results**: Save the regularized polygons as a new shapefile.

## Application UI

![APP](https://github.com/user-attachments/assets/9a0ca092-65c6-433a-a901-8c43fa6f5d6b)

## Regularized Building Boundaries

![Picture2](https://github.com/user-attachments/assets/1ba9395a-84b6-4ded-97b6-4025361a06ee)

## Requirements

- Python 3.8 or higher
- Required Python libraries:
  - `numpy`
  - `pandas`
  - `matplotlib`
  - `shapely`
  - `geopandas`
  - `tkinter`
 
  ## Citations
```bash
@ARTICLE{Li2019-iz,
  title   = "{GEOMETRIC} {OBJECT} {BASED} {BUILDING} {RECONSTRUCTION} {FROM}
             {SATELLITE} {IMAGERY} {DERIVED} {POINT} {CLOUDS}",
  author  = "Li, Zhixin and Xu, Bo and Shan, Jie",
  journal = "International Archives of the Photogrammetry, Remote Sensing \&
             Spatial Information Sciences",
  year    =  2019
}

@ARTICLE{Schuegraf2024-bp,
  title     = "Rectilinear building footprint regularization using deep learning",
  author    = "Schuegraf, P and Li, Zhixin and Tian, Jiaojiao and Shan, Jie and
               Bittner, K",
  journal   = "ISPRS Ann. Photogramm. Remote Sens. Spat. Inf. Sci.",
  publisher = "Copernicus Publications",
  volume    =  48,
  number    =  2,
  pages     = "1--6",
  month     =  jun,
  year      =  2024
}
```
