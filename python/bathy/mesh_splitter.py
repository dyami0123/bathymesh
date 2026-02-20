"""Mesh splitting functionality for dividing meshes along planes."""

import logging
from dataclasses import dataclass
from typing import Union

import numpy as np
import open3d as o3d
from scipy.spatial import Delaunay
from tqdm import tqdm

from bathy.config import MeshGenerationConfig, MeshSplittingConfig

logger = logging.getLogger(__name__)


@dataclass
class SplitPlane:
    """A plane defined by a point and normal vector."""

    origin: tuple[float, float, float]
    normal: tuple[float, float, float]

    def __post_init__(self) -> None:
        """Normalize the normal vector."""
        n = np.array(self.normal, dtype=np.float64)
        norm = np.linalg.norm(n)
        if norm > 0:
            n = n / norm
        self.normal = tuple(n.tolist())

    def signed_distance(self, point: np.ndarray) -> float:
        """
        Compute signed distance from point to plane.

        Positive = same side as normal, negative = opposite side.
        """
        n = np.array(self.normal)
        o = np.array(self.origin)
        return float(np.dot(point - o, n))

    def classify_point(self, point: np.ndarray, epsilon: float = 1e-8) -> int:
        """
        Classify point relative to plane.

        Returns:
            1 = positive side (same as normal)
            -1 = negative side
            0 = on plane (within epsilon)
        """
        d = self.signed_distance(point)
        if d > epsilon:
            return 1
        elif d < -epsilon:
            return -1
        return 0


class MeshSplitter:
    """
    Splits meshes along planes with triangle clipping and optional capping.

    Supports both explicit plane definitions and grid-based convenience splitting.
    """

    config: MeshSplittingConfig

    def __init__(self, config: MeshSplittingConfig) -> None:
        self.config = config

    @classmethod
    def from_config(cls, config: MeshGenerationConfig) -> "MeshSplitter":
        """Create MeshSplitter from MeshGenerationConfig."""
        return cls(config.mesh_splitting)

    def split_mesh(
        self, mesh: o3d.geometry.TriangleMesh
    ) -> list[o3d.geometry.TriangleMesh]:
        """
        Split mesh into sub-meshes based on configured planes.

        Uses iterative (breadth-first) approach: applies each plane to all
        existing pieces before moving to the next plane.

        Args:
            mesh: Input Open3D TriangleMesh to split

        Returns:
            List of split mesh pieces (single-element list if no planes configured)
        """
        planes = self.get_split_planes(mesh)
        if not planes:
            logger.info("No split planes configured, returning original mesh")
            return [mesh]

        logger.info(f"Splitting mesh with {len(planes)} plane(s)")
        pieces = [mesh]

        for plane_idx, plane in enumerate(
            tqdm(planes, desc="Applying split planes", unit="plane")
        ):
            new_pieces = []
            for piece in pieces:
                if len(np.asarray(piece.vertices)) == 0:
                    continue

                pos_half, neg_half = self._split_by_plane(piece, plane)

                if len(np.asarray(pos_half.vertices)) > 0:
                    new_pieces.append(pos_half)
                if len(np.asarray(neg_half.vertices)) > 0:
                    new_pieces.append(neg_half)

            pieces = new_pieces
            logger.debug(
                f"After plane {plane_idx + 1}/{len(planes)}: {len(pieces)} pieces"
            )

        logger.info(f"Split complete: {len(pieces)} total pieces")
        return pieces

    def get_split_planes(self, mesh: o3d.geometry.TriangleMesh) -> list[SplitPlane]:
        """
        Get split planes from config (explicit or grid-generated).

        Args:
            mesh: Mesh used to compute bounding box for grid-based splitting

        Returns:
            List of SplitPlane objects
        """
        if self.config.planes:
            logger.debug(f"Using {len(self.config.planes)} explicit split plane(s)")
            return [SplitPlane(p.origin, p.normal) for p in self.config.planes]
        return self._generate_grid_planes(mesh)

    def _generate_grid_planes(
        self, mesh: o3d.geometry.TriangleMesh
    ) -> list[SplitPlane]:
        """
        Generate split planes for grid-based splitting.

        Creates evenly-spaced planes along each axis based on grid_splits_x/y/z config.

        Args:
            mesh: Mesh to get bounding box from

        Returns:
            List of SplitPlane objects for grid splitting
        """
        bbox = mesh.get_axis_aligned_bounding_box()
        min_bound = np.array(bbox.min_bound)
        max_bound = np.array(bbox.max_bound)

        planes = []
        axis_names = ["X", "Y", "Z"]
        axis_splits = [
            self.config.grid_splits_x,
            self.config.grid_splits_y,
            self.config.grid_splits_z,
        ]

        for axis, splits in enumerate(axis_splits):
            if len(splits) > 0:
                normal: list[float] = [0.0, 0.0, 0.0]
                normal[axis] = 1.0

                for split_loc in splits:
                    origin = [0.0, 0.0, 0.0]
                    origin[axis] = float(split_loc)

                    planes.append(
                        SplitPlane(
                            (float(origin[0]), float(origin[1]), float(origin[2])),
                            (float(normal[0]), float(normal[1]), float(normal[2])),
                        )
                    )

                    logger.debug(
                        f"Grid plane {axis_names[axis]}: origin={origin}, normal={normal}"
                    )

        logger.debug(f"Generated {len(planes)} grid-based split plane(s)")
        return planes

    def _split_by_plane(
        self, mesh: o3d.geometry.TriangleMesh, plane: SplitPlane
    ) -> tuple[o3d.geometry.TriangleMesh, o3d.geometry.TriangleMesh]:
        """
        Split mesh into two halves at a single plane.

        Triangles crossing the plane are clipped, creating new vertices and triangles.
        If cap_cut_faces is enabled, the cut boundary is triangulated and added.

        Args:
            mesh: Input mesh to split
            plane: Plane to split along

        Returns:
            Tuple of (positive_half, negative_half) meshes
        """
        vertices = np.asarray(mesh.vertices)
        triangles = np.asarray(mesh.triangles)

        if len(vertices) == 0 or len(triangles) == 0:
            empty = o3d.geometry.TriangleMesh()
            return empty, empty

        # Classify all vertices
        classifications = np.array([plane.classify_point(v) for v in vertices])

        # Storage for new geometry
        pos_vertices: list[np.ndarray] = []
        pos_triangles: list[tuple[int, int, int]] = []
        neg_vertices: list[np.ndarray] = []
        neg_triangles: list[tuple[int, int, int]] = []

        # Vertex index maps (old index -> new index for each side)
        pos_vertex_map: dict[int, int] = {}
        neg_vertex_map: dict[int, int] = {}

        # Track boundary edges for capping
        pos_boundary_edges: list[tuple[np.ndarray, np.ndarray]] = []
        neg_boundary_edges: list[tuple[np.ndarray, np.ndarray]] = []

        # Process each triangle
        for tri in tqdm(
            triangles,
            desc="Clipping triangles",
            unit="tri",
            leave=False,
            mininterval=0.5,
        ):
            i0, i1, i2 = tri
            v0, v1, v2 = vertices[i0], vertices[i1], vertices[i2]
            c0, c1, c2 = (
                int(classifications[i0]),
                int(classifications[i1]),
                int(classifications[i2]),
            )

            # Classify triangle
            pos_count = sum(1 for c in [c0, c1, c2] if c > 0)
            neg_count = sum(1 for c in [c0, c1, c2] if c < 0)

            if neg_count == 0:
                # Triangle fully on positive side (or on plane)
                self._add_triangle_to_side(
                    [(i0, v0), (i1, v1), (i2, v2)],
                    pos_vertices,
                    pos_triangles,
                    pos_vertex_map,
                )
            elif pos_count == 0:
                # Triangle fully on negative side (or on plane)
                self._add_triangle_to_side(
                    [(i0, v0), (i1, v1), (i2, v2)],
                    neg_vertices,
                    neg_triangles,
                    neg_vertex_map,
                )
            else:
                # Triangle crosses the plane - need to clip
                self._clip_triangle(
                    v0,
                    v1,
                    v2,
                    c0,
                    c1,
                    c2,
                    plane,
                    pos_vertices,
                    pos_triangles,
                    neg_vertices,
                    neg_triangles,
                    pos_boundary_edges,
                    neg_boundary_edges,
                )

        # Build output meshes
        pos_mesh = self._build_mesh(pos_vertices, pos_triangles)
        neg_mesh = self._build_mesh(neg_vertices, neg_triangles)

        # Cap cut faces if enabled
        if self.config.cap_cut_faces and (pos_boundary_edges or neg_boundary_edges):
            logger.debug("Creating caps for cut faces")
            if pos_boundary_edges:
                pos_cap = self._create_cap(pos_boundary_edges, plane, flip_normal=True)
                if pos_cap is not None:
                    pos_mesh = self._combine_meshes(pos_mesh, pos_cap)
            if neg_boundary_edges:
                neg_cap = self._create_cap(neg_boundary_edges, plane, flip_normal=False)
                if neg_cap is not None:
                    neg_mesh = self._combine_meshes(neg_mesh, neg_cap)

        # Clean up meshes
        pos_mesh.remove_duplicated_vertices()
        pos_mesh.remove_degenerate_triangles()
        neg_mesh.remove_duplicated_vertices()
        neg_mesh.remove_degenerate_triangles()

        return pos_mesh, neg_mesh

    def _add_triangle_to_side(
        self,
        vertex_data: list[tuple[int, np.ndarray]],
        vertices: list[np.ndarray],
        triangles: list[tuple[int, int, int]],
        vertex_map: dict[int, int],
    ) -> None:
        """Add a triangle to a side, reusing vertices where possible."""
        tri_indices = []
        for old_idx, vertex in vertex_data:
            if old_idx in vertex_map:
                new_idx = vertex_map[old_idx]
            else:
                new_idx = len(vertices)
                vertices.append(vertex.copy())
                vertex_map[old_idx] = new_idx
            tri_indices.append(new_idx)
        triangles.append((tri_indices[0], tri_indices[1], tri_indices[2]))

    def _clip_triangle(
        self,
        v0: np.ndarray,
        v1: np.ndarray,
        v2: np.ndarray,
        c0: int,
        c1: int,
        c2: int,
        plane: SplitPlane,
        pos_vertices: list[np.ndarray],
        pos_triangles: list[tuple[int, int, int]],
        neg_vertices: list[np.ndarray],
        neg_triangles: list[tuple[int, int, int]],
        pos_boundary_edges: list[tuple[np.ndarray, np.ndarray]],
        neg_boundary_edges: list[tuple[np.ndarray, np.ndarray]],
    ) -> None:
        """
        Clip a triangle by a plane, adding resulting triangles to each side.

        Handles all cases of triangle-plane intersection and tracks boundary
        edges for capping.
        """
        verts = [v0, v1, v2]
        classes = [c0, c1, c2]

        # Count vertices on each side
        pos_verts = [(i, verts[i]) for i in range(3) if classes[i] > 0]
        neg_verts = [(i, verts[i]) for i in range(3) if classes[i] < 0]
        on_plane_verts = [(i, verts[i]) for i in range(3) if classes[i] == 0]

        # Find intersection points
        intersections = []
        edge_pairs = [(0, 1), (1, 2), (2, 0)]

        for e0, e1 in edge_pairs:
            c_e0, c_e1 = classes[e0], classes[e1]
            # If edge crosses the plane (one positive, one negative)
            if (c_e0 > 0 and c_e1 < 0) or (c_e0 < 0 and c_e1 > 0):
                intersection = self._find_intersection(verts[e0], verts[e1], plane)
                intersections.append((e0, e1, intersection))

        # Handle different cases based on vertex distribution
        if len(pos_verts) == 1 and len(neg_verts) == 2:
            # One vertex on positive side, two on negative
            self._clip_one_vs_two(
                pos_verts[0],
                neg_verts,
                intersections,
                plane,
                pos_vertices,
                pos_triangles,
                neg_vertices,
                neg_triangles,
                pos_boundary_edges,
                neg_boundary_edges,
                positive_is_one=True,
            )
        elif len(neg_verts) == 1 and len(pos_verts) == 2:
            # One vertex on negative side, two on positive
            self._clip_one_vs_two(
                neg_verts[0],
                pos_verts,
                intersections,
                plane,
                neg_vertices,
                neg_triangles,
                pos_vertices,
                pos_triangles,
                neg_boundary_edges,
                pos_boundary_edges,
                positive_is_one=False,
            )
        elif len(on_plane_verts) == 1:
            # One vertex exactly on plane
            on_idx, on_vert = on_plane_verts[0]
            if len(pos_verts) == 1 and len(neg_verts) == 1:
                # The other two vertices are on opposite sides
                pos_idx, pos_vert = pos_verts[0]
                neg_idx, neg_vert = neg_verts[0]
                intersection = self._find_intersection(pos_vert, neg_vert, plane)

                # Add triangle to positive side
                self._add_new_triangle(
                    [on_vert, pos_vert, intersection],
                    pos_vertices,
                    pos_triangles,
                )
                # Add triangle to negative side
                self._add_new_triangle(
                    [on_vert, intersection, neg_vert],
                    neg_vertices,
                    neg_triangles,
                )
                # Track boundary edge
                pos_boundary_edges.append((on_vert.copy(), intersection.copy()))
                neg_boundary_edges.append((intersection.copy(), on_vert.copy()))

    def _clip_one_vs_two(
        self,
        one_vert: tuple[int, np.ndarray],
        two_verts: list[tuple[int, np.ndarray]],
        intersections: list[tuple[int, int, np.ndarray]],
        plane: SplitPlane,
        one_vertices: list[np.ndarray],
        one_triangles: list[tuple[int, int, int]],
        two_vertices: list[np.ndarray],
        two_triangles: list[tuple[int, int, int]],
        one_boundary_edges: list[tuple[np.ndarray, np.ndarray]],
        two_boundary_edges: list[tuple[np.ndarray, np.ndarray]],
        positive_is_one: bool,
    ) -> None:
        """Handle case where one vertex is on one side and two on the other."""
        one_idx, one_v = one_vert
        two_idx_0, two_v_0 = two_verts[0]
        two_idx_1, two_v_1 = two_verts[1]

        # Find the two intersection points (edges from the "one" vertex)
        int_points = []
        for e0, e1, intersection in intersections:
            if one_idx in (e0, e1):
                other_idx = e1 if e0 == one_idx else e0
                int_points.append((other_idx, intersection))

        if len(int_points) < 2:
            # Fallback: shouldn't happen with valid input
            return

        # Sort intersection points to match edge ordering
        int_points.sort(key=lambda x: x[0])
        int_0 = int_points[0][1]
        int_1 = int_points[1][1]

        # Triangle on the "one" side (single triangle)
        self._add_new_triangle([one_v, int_0, int_1], one_vertices, one_triangles)

        # Quad on the "two" side (split into two triangles)
        # The quad vertices are: int_0, two_v_0, two_v_1, int_1
        # Need to maintain consistent winding
        self._add_new_triangle([int_0, two_v_0, two_v_1], two_vertices, two_triangles)
        self._add_new_triangle([int_0, two_v_1, int_1], two_vertices, two_triangles)

        # Track boundary edge (from int_0 to int_1)
        if positive_is_one:
            one_boundary_edges.append((int_0.copy(), int_1.copy()))
            two_boundary_edges.append((int_1.copy(), int_0.copy()))
        else:
            one_boundary_edges.append((int_1.copy(), int_0.copy()))
            two_boundary_edges.append((int_0.copy(), int_1.copy()))

    def _add_new_triangle(
        self,
        verts: list[np.ndarray],
        vertices: list[np.ndarray],
        triangles: list[tuple[int, int, int]],
    ) -> None:
        """Add a new triangle from new vertices (no vertex reuse)."""
        base_idx = len(vertices)
        for v in verts:
            vertices.append(v.copy())
        triangles.append((base_idx, base_idx + 1, base_idx + 2))

    def _find_intersection(
        self, v1: np.ndarray, v2: np.ndarray, plane: SplitPlane
    ) -> np.ndarray:
        """
        Find intersection point between line segment and plane.

        Args:
            v1: First endpoint of segment
            v2: Second endpoint of segment
            plane: Plane to intersect with

        Returns:
            Intersection point as numpy array
        """
        d1 = plane.signed_distance(v1)
        d2 = plane.signed_distance(v2)

        # Avoid division by zero
        if abs(d1 - d2) < 1e-10:
            return (v1 + v2) / 2

        t = d1 / (d1 - d2)
        return v1 + t * (v2 - v1)

    def _build_mesh(
        self,
        vertices: list[np.ndarray],
        triangles: list[tuple[int, int, int]],
    ) -> o3d.geometry.TriangleMesh:
        """Build an Open3D mesh from vertices and triangles."""
        mesh = o3d.geometry.TriangleMesh()
        if vertices and triangles:
            mesh.vertices = o3d.utility.Vector3dVector(np.array(vertices))
            mesh.triangles = o3d.utility.Vector3iVector(np.array(triangles))
            mesh.compute_vertex_normals()
        return mesh

    def _create_cap(
        self,
        boundary_edges: list[tuple[np.ndarray, np.ndarray]],
        plane: SplitPlane,
        flip_normal: bool,
    ) -> Union[o3d.geometry.TriangleMesh, None]:
        """
        Create a cap mesh from boundary edges.

        Collects cut edges, orders them into loops, projects to 2D,
        triangulates, and projects back to 3D.

        Args:
            boundary_edges: List of (start, end) edge tuples from cut triangles
            plane: The cut plane
            flip_normal: Whether to flip the cap normal

        Returns:
            Cap mesh or None if capping fails
        """
        if not boundary_edges:
            return None

        # Collect unique boundary points
        boundary_points = []
        point_set: set[tuple[float, float, float]] = set()

        for edge in boundary_edges:
            for pt in edge:
                key = tuple(np.round(pt, decimals=6).tolist())
                if key not in point_set:
                    point_set.add(key)
                    boundary_points.append(pt)

        if len(boundary_points) < 3:
            return None

        # Project points to 2D (plane coordinates)
        points_2d = self._project_to_plane(np.array(boundary_points), plane)

        # Triangulate in 2D
        try:
            tri = Delaunay(points_2d)
            triangles_2d = tri.simplices
        except Exception as e:
            logger.warning(f"Cap triangulation failed: {e}")
            return None

        # Build cap mesh
        cap_vertices = boundary_points
        cap_triangles = []

        for tri_indices in triangles_2d:
            if flip_normal:
                cap_triangles.append((tri_indices[0], tri_indices[2], tri_indices[1]))
            else:
                cap_triangles.append((tri_indices[0], tri_indices[1], tri_indices[2]))

        return self._build_mesh(cap_vertices, cap_triangles)

    def _project_to_plane(self, points: np.ndarray, plane: SplitPlane) -> np.ndarray:
        """
        Project 3D points onto a plane's local 2D coordinate system.

        Args:
            points: Nx3 array of 3D points
            plane: Plane to project onto

        Returns:
            Nx2 array of 2D coordinates
        """
        normal = np.array(plane.normal)
        origin = np.array(plane.origin)

        # Create orthonormal basis for the plane
        # Find a vector not parallel to normal
        if abs(normal[0]) < 0.9:
            ref = np.array([1.0, 0.0, 0.0])
        else:
            ref = np.array([0.0, 1.0, 0.0])

        u = np.cross(normal, ref)
        u = u / np.linalg.norm(u)
        v = np.cross(normal, u)

        # Project points
        relative = points - origin
        coords_2d = np.column_stack([np.dot(relative, u), np.dot(relative, v)])

        return coords_2d

    def _combine_meshes(
        self,
        mesh1: o3d.geometry.TriangleMesh,
        mesh2: o3d.geometry.TriangleMesh,
    ) -> o3d.geometry.TriangleMesh:
        """Combine two meshes into one."""
        if len(np.asarray(mesh1.vertices)) == 0:
            return mesh2
        if len(np.asarray(mesh2.vertices)) == 0:
            return mesh1

        combined = mesh1 + mesh2
        combined.compute_vertex_normals()
        return combined
