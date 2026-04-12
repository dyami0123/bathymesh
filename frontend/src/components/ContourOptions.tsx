import { useState, useEffect } from "react";
import { defaultsApiConfigDefaultsGet } from "../client";
import type { ProjectConfigOutput } from "../client";
import { useProject, useProjectDispatch } from "@/state/projectContext";

export function ContourOptions() {
  const project = useProject();
  const dispatch = useProjectDispatch();

  const [min_polygon_area, setMinPolygonArea] = useState(
    project.mesh_generation.contour_extraction.min_polygon_area
  );
  const [simplifify_tolerance, setSimplifyTolerance] = useState(
    project.mesh_generation.contour_extraction.simplify_tolerance
  );
  const [max_segments, setMaxSegments] = useState(
    project.mesh_generation.contour_extraction.max_segments
  );
  const [min_area_fraction, setMinAreaFraction] = useState(
    project.mesh_generation.contour_extraction.min_area_fraction
  );

  const createConfig = () => ({
    min_polygon_area: min_polygon_area,
    simplify_tolerance: simplifify_tolerance,
    max_segments: max_segments,
    min_area_fraction: min_area_fraction,
  });

  useEffect(() => {
    dispatch({
      type: "set_contour_extraction",
      payload: createConfig(),
    });
  }, [min_polygon_area, simplifify_tolerance, max_segments, min_area_fraction]);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-bold">Contour Extraction Options</h2>
      <div className="flex flex-col gap-2">
        <label>
          Min Polygon Area:
          <input
            type="number"
            value={min_polygon_area}
            onChange={(e) => setMinPolygonArea(Number(e.target.value))}
            className="ml-2 p-1 border rounded"
            title="Minimum polygon area for contour extraction"
          ></input>
        </label>
        <label>
          Simplify Tolerance:
          <input
            type="number"
            value={simplifify_tolerance}
            onChange={(e) => setSimplifyTolerance(Number(e.target.value))}
            className="ml-2 p-1 border rounded"
            title="Tolerance for contour simplification"
          />
        </label>

        <label>
          Max Segments:
          <input
            type="number"
            value={max_segments}
            onChange={(e) => setMaxSegments(Number(e.target.value))}
            className="ml-2 p-1 border rounded"
            title="Maximum number of contour segments"
            min={1}
            step={1}
          />
        </label>

        <label>
          Min Area Fraction:
          <input
            type="number"
            value={min_area_fraction}
            onChange={(e) => setMinAreaFraction(Number(e.target.value))}
            className="ml-2 p-1 border rounded"
            title="Minimum retained area fraction after filtering"
            min={0}
            max={1}
            step="0.01"
          />
        </label>
      </div>
    </div>
  );
}
