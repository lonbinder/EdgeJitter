# EdgeJitter1
API script for Autodesk Fusion 360. Takes a line in sketch and "jitters" it (adding random convex, concave shapes). Today, this only supports work on SketchLine curves that are along the X or Y axis. 

Currently supported shapes:
 - Fixed rectangle (square)
 - Hemi-circle (half a circle as an arc)

Planned shapes:
 - Random rectangle ratios
 - Random depth arcs (not hemi-circles)
 - Arc+line combos

Potential additional features to add:
 - Change the cut size to have a range (min/max) and allow random cuts between those sizes
 - SketchCurve on Z-axis
 - Selecting multiple SketchCurves
   - Operating on the corner if multiple SketchCurves intersect