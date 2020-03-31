# -*- coding: utf-8 -*-
import fiona as fn
import rasterio
import rasterio.mask


def extract_raster_part(pop_raster, border, output):
    """Extract raster part for Jakarta admin border."""

    border_shape = [feature["geometry"] for feature in border]

    out_image, out_transform = rasterio.mask.mask(pop_raster, border_shape, crop=True)
    out_meta = pop_raster.meta

    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    with rasterio.open(output, "w", **out_meta) as o_rst:
        o_rst.write(out_image)
