import numpy as np
import pygmsh
import gmsh
from shapely.geometry import Polygon, MultiPolygon
from typing import Tuple, Union, List

from .base_triangulator import BaseTriangulator  # Adjust this import as needed


class GmshTriangulator(BaseTriangulator):
    def triangulate_polygon(
        self,
        geometries: Union[Polygon, MultiPolygon, List[Polygon]]
    ) -> Tuple[np.ndarray, np.ndarray]:

        polygons = self._normalize_geometries(geometries)

        with pygmsh.geo.Geometry() as geom:
            
            geom.env
            plane_surfaces = []

            for polygon in polygons:
                exterior = np.array(polygon.exterior.coords)
                
                # Create exterior curve loop
                exterior_points = [geom.add_point(coord + [0.0]) for coord in exterior[:-1]]  # Skip last duplicate point
                exterior_lines = [geom.add_line(exterior_points[i], exterior_points[(i + 1) % len(exterior_points)]) 
                                for i in range(len(exterior_points))]
                exterior_loop = geom.add_curve_loop(exterior_lines)
                
                # Create hole curve loops
                hole_loops = []
                for hole in polygon.interiors:
                    hole_coords = np.array(hole.coords)
                    hole_points = [geom.add_point(coord + [0.0]) for coord in hole_coords[:-1]]  # Skip last duplicate point
                    hole_lines = [geom.add_line(hole_points[i], hole_points[(i + 1) % len(hole_points)]) 
                                for i in range(len(hole_points))]
                    hole_loop = geom.add_curve_loop(hole_lines)
                    hole_loops.append(hole_loop)
                
                # Create plane surface with holes
                surface = geom.add_plane_surface(exterior_loop, hole_loops)
                plane_surfaces.append(surface)

            geom.add_physical(plane_surfaces, "plane")  # Optional: add physical tag
            
            mesh = geom.generate_mesh(dim = 2, verbose=True, algorithm=5)
    
        # Extract vertices and triangles
        points = mesh.points[:, :2]  # Ignore z-coordinates
        cells = mesh.cells_dict.get("triangle")
        if cells is None:
            raise ValueError("No triangles found in mesh.")

        return points, cells
