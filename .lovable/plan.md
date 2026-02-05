

# Ruler/Measurement Tool Implementation Plan

## Overview

Add a precise ruler tool for measuring 3D objects with orthographic pre-defined views (Front, Side, Top, Bottom, Rear) for accuracy. When the ruler mode is activated, the viewer automatically switches to orthographic projection and displays view selection buttons.

---

## UI Design Recommendation

### Toolbar Integration

Add a new "Ruler" toggle button to the existing `ViewControlsToolbar`:

```text
+---------------------------------------------------------------+
| [Grid] [Light] [Solid] | [Reset] [Front] [Side] [Top] | [📏 Ruler] [⛶] [📂] [↻] |
+---------------------------------------------------------------+
```

When **Ruler mode is active**, a secondary measurement toolbar appears below with view options:

```text
+---------------------------------------------------------------+
| 📐 Measure Mode  |  [Front] [Side] [Top] [Bottom] [Rear]  |  [Exit Ruler]  |
+---------------------------------------------------------------+
```

### Measurement Workflow

1. Click "Ruler" button - activates measure mode
2. View automatically switches to **Front** (orthographic projection)
3. User can select other views: Side, Top, Bottom, Rear
4. Click two points on the model to measure distance
5. Distance displayed as an overlay annotation with a line connecting the points

### Visual Feedback

- Active measurement points shown as small spheres (color: `#5294E2`)
- Connecting line between points (dashed or solid)
- Distance label positioned at midpoint of the measurement line
- All measurements cleared when exiting ruler mode or changing views

---

## Technical Implementation

### 1. New File: `ui/ruler_toolbar.py`

A secondary toolbar widget that appears when ruler mode is active:

| Component | Purpose |
|-----------|---------|
| `RulerToolbar(QWidget)` | Collapsible toolbar for measurement views |
| View buttons | Front, Side, Top, Bottom, Rear - each switches to orthographic |
| Clear button | Clears all current measurements |
| Exit button | Exits ruler mode |

### 2. Modify: `ui/toolbar.py`

- Add new `ruler_btn` (📏 Ruler) to the utility actions section
- Add signal: `toggle_ruler = pyqtSignal()`
- Track state: `self.ruler_mode_enabled = False`

### 3. Modify: `viewer_widget.py`

Add measurement functionality using PyVista's built-in picking:

```python
# New methods to add:
def enable_ruler_mode(self):
    """Enable point-to-point measurement mode."""
    self.ruler_mode = True
    self.measurement_points = []
    self.plotter.enable_point_picking(
        callback=self._on_point_picked,
        show_message=False,
        use_mesh=True
    )
    # Switch to orthographic projection
    self.plotter.enable_parallel_projection()

def _on_point_picked(self, point):
    """Handle point picked for measurement."""
    self.measurement_points.append(point)
    # Add sphere marker at picked point
    sphere = pv.Sphere(radius=0.5, center=point)
    self.plotter.add_mesh(sphere, color='#5294E2', name=f'measure_pt_{len(self.measurement_points)}')
    
    if len(self.measurement_points) == 2:
        # Calculate and display distance
        distance = self._calculate_distance(self.measurement_points[0], self.measurement_points[1])
        self._draw_measurement_line(distance)
        self.measurement_points = []  # Reset for next measurement
```

### 4. Modify: `stl_viewer.py`

Connect new signals:

```python
def _connect_toolbar_signals(self):
    # ... existing connections ...
    self.toolbar.toggle_ruler.connect(self._toggle_ruler_mode)
    
def _toggle_ruler_mode(self):
    """Toggle ruler/measurement mode."""
    if self.toolbar.ruler_mode_enabled:
        self.viewer_widget.enable_ruler_mode()
        self.ruler_toolbar.show()
        self._view_front()  # Auto-switch to front view
    else:
        self.viewer_widget.disable_ruler_mode()
        self.ruler_toolbar.hide()
```

### 5. View Methods for Measurement (Orthographic)

| View | PyVista Method | Camera Position |
|------|----------------|-----------------|
| Front | `view_yz()` | +X axis looking at YZ plane |
| Side (Right) | `view_xz()` | +Y axis looking at XZ plane |
| Top | `view_xy()` | +Z axis looking at XY plane |
| Bottom | `view_xy()` + flip | -Z axis looking at XY plane |
| Rear | `view_yz()` + flip | -X axis looking at YZ plane |

---

## File Changes Summary

| File | Action | Changes |
|------|--------|---------|
| `ui/ruler_toolbar.py` | **Create** | New measurement toolbar with view buttons |
| `ui/toolbar.py` | Modify | Add ruler button and signal |
| `ui/styles.py` | Modify | Add ruler toolbar styles |
| `viewer_widget.py` | Modify | Add measurement/picking methods |
| `stl_viewer.py` | Modify | Connect signals, manage ruler toolbar visibility |

---

## Technical Notes

### PyVista Measurement Capabilities

PyVista supports:
- `enable_point_picking()` - Pick points on mesh surface
- `enable_parallel_projection()` - Orthographic view for accurate measurement
- `add_lines()` - Draw measurement lines
- `add_point_labels()` - Display distance annotations

### Accuracy Considerations

- Orthographic projection eliminates perspective distortion
- Pre-defined views ensure consistent measurement planes
- Point snapping to mesh vertices ensures precise picks

