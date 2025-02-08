# EdgeJitter
API script for Autodesk Fusion 360. Takes a line in sketch and "jitters" it (adding random convex, concave shapes). Today, this only supports work on SketchLine curves that are along the X or Y axis. 

Currently supported shapes:
 - Rectangles
 - Arcs (hemi-ellipses)
 - Triangles

Planned shapes:
 - Arc+line combos

Potential additional features to add:
 - Re-introduce percentage distances for cut size
 - SketchCurve on Z-axis
 - Selecting multiple SketchCurves
   - Operating on the corner if multiple SketchCurves intersect

TODO:
 - Fix bug where user has to re-select the curve after preview (this is due to 'deleted' entity)


 General guidance
  - We're following PEP8