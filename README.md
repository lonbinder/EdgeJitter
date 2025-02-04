# EdgeJitter
API script for Autodesk Fusion 360. Takes a line in sketch and "jitters" it (adding random convex, concave shapes). Today, this only supports work on SketchLine curves that are along the X or Y axis. 

Currently supported shapes:
 - Rectangles
 - Arcs (hemi-ellipses)
 - Triangles

Planned shapes:
 - Arc+line combos

Potential additional features to add:
 - SketchCurve on Z-axis
 - Selecting multiple SketchCurves
   - Operating on the corner if multiple SketchCurves intersect

TODO:
 - Fix bug when 'ok' is clicked before 'preview' and the user jumped from one numeric input direclty to 'ok'. That skips the input changed event and throws a UI error.
 - Fix bug that seems to be only when recurse is used, and 'preview' is hit repeatedly, it throws an error for a deleted curve.
 - Re-format the HTML, looks terrible.
 - Support percentage input


 General guidance
  - We're following PEP8