"""
3D PDF Exporter using U3D format.
Exports interactive 3D PDFs where users can rotate/zoom the model in Adobe Acrobat Reader.

Implementation notes:
- Interactive 3D in PDF requires embedding U3D (or PRC). We use VTK's vtkU3DExporter when
  it exists in the installed VTK build.
- Some Python environments may ship VTK without vtkU3DExporter. In that case we fall back
  to a static multi-view PDF.
"""
import logging
import tempfile
import os
import zlib
import sys
import platform

logger = logging.getLogger(__name__)


class PDF3DExporter:
    """
    Handles exporting 3D meshes to interactive PDF format.
    
    Creates PDFs with embedded U3D 3D annotations that work in Adobe Acrobat Reader.
    Users can rotate, pan, and zoom the 3D model within the PDF.
    """

    @staticmethod
    def _get_vtk_u3d_exporter_cls():
        """Return vtkU3DExporter class if available in the current VTK build, else None."""
        errors = []

        # Prefer vtkmodules import (modern VTK wheels)
        try:
            from vtkmodules.vtkIOExport import vtkU3DExporter  # type: ignore

            logger.debug("vtkU3DExporter resolved via vtkmodules.vtkIOExport")
            return vtkU3DExporter
        except Exception as e:
            errors.append(("vtkmodules.vtkIOExport", repr(e)))
            logger.debug("vtkU3DExporter not available via vtkmodules.vtkIOExport: %s", e, exc_info=True)

        # Fallbacks (older / alternate layouts)
        try:
            import vtk  # type: ignore

            if hasattr(vtk, "vtkU3DExporter"):
                logger.debug("vtkU3DExporter resolved via vtk.vtkU3DExporter")
                return vtk.vtkU3DExporter
        except Exception as e:
            errors.append(("vtk (hasattr)", repr(e)))
            logger.debug("vtk import/hasattr(vtkU3DExporter) failed: %s", e, exc_info=True)

        try:
            from vtk import vtkU3DExporter  # type: ignore

            logger.debug("vtkU3DExporter resolved via 'from vtk import vtkU3DExporter'")
            return vtkU3DExporter
        except Exception as e:
            errors.append(("vtk direct", repr(e)))
            logger.debug("vtkU3DExporter not available via 'from vtk import vtkU3DExporter': %s", e, exc_info=True)

        if errors:
            logger.debug("vtkU3DExporter resolution attempts failed: %s", errors)
        return None

    @staticmethod
    def _log_runtime_context():
        """Log runtime and VTK context to help diagnose U3D export availability."""
        logger.info(
            "3D PDF runtime context | python=%s | platform=%s | executable=%s",
            sys.version.replace("\n", " "),
            platform.platform(),
            sys.executable,
        )
        try:
            import vtk  # type: ignore

            vtk_ver = vtk.vtkVersion.GetVTKVersion()
            logger.info("VTK detected | version=%s | vtk_file=%s", vtk_ver, getattr(vtk, "__file__", "<unknown>"))
        except Exception as e:
            logger.warning("VTK import failed while checking U3D availability: %s", e, exc_info=True)

    @staticmethod
    def check_u3d_exporter():
        """Check if vtkU3DExporter is available (via installed VTK)."""
        PDF3DExporter._log_runtime_context()
        cls = PDF3DExporter._get_vtk_u3d_exporter_cls()
        if cls is None:
            return (
                False,
                "vtkU3DExporter is not available in your VTK build. "
                "Install/upgrade VTK (pip install -U vtk).",
            )
        logger.info("vtkU3DExporter available: %s", getattr(cls, "__name__", str(cls)))
        return True, "vtkU3DExporter available via VTK"

    @staticmethod
    def mesh_to_u3d(mesh, output_path_base: str):
        """Export a PyVista/VTK mesh to U3D using VTK's vtkU3DExporter.

        Args:
            mesh: PyVista mesh (vtkPolyData)
            output_path_base: base path WITHOUT extension (VTK typically appends .u3d)

        Returns:
            (success, u3d_path_or_error)
        """
        try:
            import vtk  # type: ignore

            exporter_cls = PDF3DExporter._get_vtk_u3d_exporter_cls()
            if exporter_cls is None:
                logger.error("mesh_to_u3d: vtkU3DExporter not available (output_base=%s)", output_path_base)
                return False, "vtkU3DExporter not available"

            # Mesh diagnostics
            try:
                mesh_type = type(mesh).__name__
                n_points = getattr(mesh, "GetNumberOfPoints", lambda: None)()
                n_cells = getattr(mesh, "GetNumberOfCells", lambda: None)()
                logger.info(
                    "mesh_to_u3d: mesh=%s points=%s cells=%s",
                    mesh_type,
                    n_points,
                    n_cells,
                )
            except Exception:
                logger.debug("mesh_to_u3d: unable to read mesh diagnostics", exc_info=True)

            # Off-screen render window
            render_window = vtk.vtkRenderWindow()
            render_window.SetOffScreenRendering(1)
            render_window.SetSize(800, 600)

            renderer = vtk.vtkRenderer()
            renderer.SetBackground(1.0, 1.0, 1.0)
            render_window.AddRenderer(renderer)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(mesh)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.75, 0.75, 0.78)
            actor.GetProperty().SetSpecular(0.3)
            actor.GetProperty().SetSpecularPower(20)

            renderer.AddActor(actor)
            renderer.ResetCamera()
            render_window.Render()

            exporter = exporter_cls()
            exporter.SetFileName(output_path_base)
            logger.info(
                "mesh_to_u3d: using exporter=%s output_base=%s",
                getattr(exporter_cls, "__name__", str(exporter_cls)),
                output_path_base,
            )

            # API differs across builds
            if hasattr(exporter, "SetInput"):
                exporter.SetInput(render_window)
            elif hasattr(exporter, "SetRenderWindow"):
                exporter.SetRenderWindow(render_window)
            else:
                return False, "Unsupported vtkU3DExporter API (no SetInput/SetRenderWindow)"

            exporter.Write()

            logger.info("mesh_to_u3d: exporter.Write() returned; checking output files...")

            candidates = [f"{output_path_base}.u3d", output_path_base]
            for cand in candidates:
                if os.path.exists(cand):
                    try:
                        size = os.path.getsize(cand)
                        logger.info("mesh_to_u3d: U3D created: %s (bytes=%d)", cand, size)
                        if size < 1024:
                            logger.warning("mesh_to_u3d: U3D file is unexpectedly small (%d bytes): %s", size, cand)
                    except Exception:
                        logger.debug("mesh_to_u3d: could not stat output candidate: %s", cand, exc_info=True)
                    return True, cand

            logger.error("mesh_to_u3d: U3D export failed - no candidate files created (base=%s)", output_path_base)
            return False, "U3D export failed - file not created"

        except Exception as e:
            logger.error("Failed to export U3D: %s", e, exc_info=True)
            return False, str(e)

    @staticmethod
    def create_3d_pdf(u3d_path, output_pdf_path, title="3D Model", mesh_info=None):
        """Create a PDF with an embedded interactive 3D (U3D) annotation."""
        try:
            logger.info("create_3d_pdf: u3d_path=%s output_pdf_path=%s title=%s", u3d_path, output_pdf_path, title)
            with open(u3d_path, "rb") as f:
                u3d_data = f.read()

            logger.info("create_3d_pdf: U3D input bytes=%d", len(u3d_data))

            compressed_u3d = zlib.compress(u3d_data)

            logger.info("create_3d_pdf: U3D compressed bytes=%d", len(compressed_u3d))

            pdf_objects = []

            # 1: Catalog
            pdf_objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
            # 2: Pages
            pdf_objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

            # Page (A4: 595 x 842)
            page_width = 595
            page_height = 842
            margin = 50
            annot_x1 = margin
            annot_y1 = 200
            annot_x2 = page_width - margin
            annot_y2 = page_height - 100

            # 3: Page
            pdf_objects.append(
                (
                    f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
                    f"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> "
                    f"/Annots [6 0 R] >>\nendobj\n"
                ).encode("ascii")
            )

            # 4: Content stream
            content = f"""
BT
/F1 18 Tf
{margin} {page_height - 60} Td
({title}) Tj
ET
BT
/F1 10 Tf
{margin} {page_height - 80} Td
(Interactive 3D Model - Drag to rotate, scroll to zoom) Tj
ET
"""
            if mesh_info:
                y_pos = 180
                content += f"""
BT
/F1 9 Tf
{margin} {y_pos} Td
(Dimensions: {mesh_info.get('width', 0):.2f} x {mesh_info.get('height', 0):.2f} x {mesh_info.get('depth', 0):.2f} mm) Tj
ET
BT
/F1 9 Tf
{margin} {y_pos - 15} Td
(Volume: {mesh_info.get('volume_cm3', 0):.4f} cm3   |   Surface: {mesh_info.get('surface_area_cm2', 0):.2f} cm2) Tj
ET
"""

            content_bytes = content.encode("latin-1")
            pdf_objects.append(
                f"4 0 obj\n<< /Length {len(content_bytes)} >>\nstream\n".encode("ascii")
                + content_bytes
                + b"\nendstream\nendobj\n"
            )

            # 5: Font
            pdf_objects.append(
                b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
            )

            # 6: 3D Annotation
            pdf_objects.append(
                (
                    f"6 0 obj\n<< /Type /Annot /Subtype /3D "
                    f"/Rect [{annot_x1} {annot_y1} {annot_x2} {annot_y2}] "
                    f"/3DD 7 0 R /3DV 8 0 R "
                    f"/3DA << /A /PO /AIS /L /DIS /I >> "
                    f"/F 4 /Contents (3D Model) >>\nendobj\n"
                ).encode("ascii")
            )

            # 7: 3D Stream
            pdf_objects.append(
                (
                    f"7 0 obj\n<< /Type /3D /Subtype /U3D /Length {len(compressed_u3d)} "
                    f"/Filter /FlateDecode >>\nstream\n"
                ).encode("ascii")
                + compressed_u3d
                + b"\nendstream\nendobj\n"
            )

            # 8: Default 3D View
            pdf_objects.append(
                b"8 0 obj\n<< /Type /3DView /XN (Default) /IN (Default View) "
                b"/MS /M "
                b"/C2W [0.707 0.408 -0.577 0 0.816 0.577 0.707 -0.408 0.577 0 0 100] "
                b"/CO 100 /P << /Subtype /O >> "
                b"/BG << /Type /3DBG /CS /DeviceRGB /C [1 1 1] >> "
                b"/LS << /Type /3DLightingScheme /Subtype /CAD >> >>\nendobj\n"
            )

            # Build PDF
            pdf_header = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n"
            positions = []
            current_pos = len(pdf_header)
            pdf_body = b""
            for obj in pdf_objects:
                positions.append(current_pos)
                pdf_body += obj
                current_pos += len(obj)

            xref_pos = len(pdf_header) + len(pdf_body)
            xref = f"xref\n0 {len(pdf_objects) + 1}\n0000000000 65535 f \n"
            for pos in positions:
                xref += f"{pos:010d} 00000 n \n"
            xref_bytes = xref.encode("ascii")

            trailer = (
                f"trailer\n<< /Size {len(pdf_objects) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref_pos}\n%%EOF\n"
            ).encode("ascii")

            with open(output_pdf_path, "wb") as f:
                f.write(pdf_header)
                f.write(pdf_body)
                f.write(xref_bytes)
                f.write(trailer)

            try:
                logger.info("create_3d_pdf: PDF written (bytes=%d)", os.path.getsize(output_pdf_path))
            except Exception:
                logger.debug("create_3d_pdf: could not stat output PDF", exc_info=True)

            return True, output_pdf_path

        except Exception as e:
            logger.error("Failed to create 3D PDF: %s", e, exc_info=True)
            return False, str(e)

    @staticmethod
    def export_interactive_3d_pdf(mesh, output_path, title="3D Model", allow_static_fallback: bool = True):
        """Export mesh to an interactive 3D PDF; optionally fall back to static when unavailable."""
        if mesh is None:
            return False, "No mesh provided"

        available, msg = PDF3DExporter.check_u3d_exporter()
        if not available:
            logger.error("Interactive 3D PDF export not available: %s", msg)
            if allow_static_fallback:
                logger.warning("Falling back to static PDF due to missing U3D exporter")
                return PDF3DExporter.export_static_3d_pdf(mesh, output_path, title)
            return False, msg

        temp_dir = tempfile.mkdtemp()
        try:
            u3d_base = os.path.join(temp_dir, "model")
            success, u3d_path_or_err = PDF3DExporter.mesh_to_u3d(mesh, u3d_base)
            if not success:
                logger.error("U3D export failed: %s", u3d_path_or_err)
                if allow_static_fallback:
                    logger.warning("Falling back to static PDF due to U3D export failure")
                    return PDF3DExporter.export_static_3d_pdf(mesh, output_path, title)
                return False, f"U3D export failed: {u3d_path_or_err}"

            from core.mesh_calculator import MeshCalculator

            mesh_info = MeshCalculator.get_mesh_data(mesh)
            return PDF3DExporter.create_3d_pdf(u3d_path_or_err, output_path, title, mesh_info)
        finally:
            try:
                for name in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, name))
                    except Exception:
                        pass
                os.rmdir(temp_dir)
            except Exception:
                pass
    
    @staticmethod
    def export_static_3d_pdf(mesh, output_path, title="3D Model"):
        """
        Export static PDF with multiple high-quality view screenshots.
        
        Args:
            mesh: PyVista mesh object
            output_path: Path for the output PDF
            title: Title for the document
            
        Returns:
            tuple: (bool, str) - (success, output_path or error_message)
        """
        try:
            import pyvista as pv
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Image, 
                Table, TableStyle
            )
            from reportlab.lib.enums import TA_CENTER
            
            if mesh is None:
                return False, "No mesh provided"
            
            # Create temporary directory for screenshots
            temp_dir = tempfile.mkdtemp()
            screenshots = []
            view_names = []
            
            # Define view angles
            views = [
                ('Isometric', 'isometric'),
                ('Front', 'yz'),
                ('Right Side', 'xz'),
                ('Top', 'xy'),
            ]
            
            for view_name, view_type in views:
                try:
                    plotter = pv.Plotter(off_screen=True, window_size=[800, 600])
                    plotter.background_color = 'white'
                    
                    plotter.add_mesh(
                        mesh, 
                        color='#D4D4D4',
                        specular=0.5,
                        specular_power=15,
                        smooth_shading=True
                    )
                    
                    plotter.add_light(pv.Light(position=(1, 1, 1), intensity=1.0))
                    plotter.add_light(pv.Light(position=(-1, -0.5, 0.5), intensity=0.4))
                    
                    if view_type == 'isometric':
                        plotter.view_isometric()
                    elif view_type == 'yz':
                        plotter.view_yz()
                    elif view_type == 'xz':
                        plotter.view_xz()
                    elif view_type == 'xy':
                        plotter.view_xy()
                    
                    plotter.reset_camera()
                    
                    img_path = os.path.join(temp_dir, f'view_{view_type}.png')
                    plotter.screenshot(img_path)
                    plotter.close()
                    
                    screenshots.append(img_path)
                    view_names.append(view_name)
                    
                except Exception as e:
                    logger.warning(f"Failed to capture {view_name} view: {e}")
            
            if not screenshots:
                return False, "Failed to capture any views"
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=15*mm,
                leftMargin=15*mm,
                topMargin=15*mm,
                bottomMargin=15*mm
            )
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=12,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1E293B')
            )
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#64748B')
            )
            view_title_style = ParagraphStyle(
                'ViewTitle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=10,
                spaceAfter=8,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1E293B')
            )
            
            story = []
            
            story.append(Paragraph("3D Model Export", title_style))
            story.append(Paragraph(
                f"File: {title}<br/>"
                "Multiple views with detailed measurements",
                subtitle_style
            ))
            story.append(Spacer(1, 10))
            
            # Add mesh info
            from core.mesh_calculator import MeshCalculator
            mesh_data = MeshCalculator.get_mesh_data(mesh)
            
            info_data = [
                ['Property', 'Value'],
                ['Width (X)', f"{mesh_data['width']:.2f} mm"],
                ['Height (Y)', f"{mesh_data['height']:.2f} mm"],
                ['Depth (Z)', f"{mesh_data['depth']:.2f} mm"],
                ['Volume', f"{mesh_data['volume_cm3']:.4f} cm³"],
                ['Surface Area', f"{mesh_data['surface_area_cm2']:.2f} cm²"],
            ]
            
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0F7FF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ])
            
            info_table = Table(info_data, colWidths=[100*mm, 70*mm])
            info_table.setStyle(table_style)
            story.append(info_table)
            story.append(Spacer(1, 20))
            
            # Add views in 2x2 grid
            page_width = A4[0] - 30*mm
            img_width = (page_width - 10*mm) / 2
            img_height = img_width * 0.75
            
            for i in range(0, len(screenshots), 2):
                row_data = []
                label_data = []
                for j in range(2):
                    if i + j < len(screenshots):
                        try:
                            img = Image(screenshots[i + j], width=img_width, height=img_height)
                            row_data.append(img)
                            label_data.append(Paragraph(view_names[i + j], view_title_style))
                        except:
                            pass
                
                if label_data:
                    label_table = Table([label_data], colWidths=[img_width + 5*mm] * len(label_data))
                    story.append(label_table)
                    
                if row_data:
                    view_table = Table([row_data], colWidths=[img_width + 5*mm] * len(row_data))
                    view_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    story.append(view_table)
                    story.append(Spacer(1, 15))
            
            doc.build(story)
            
            # Cleanup
            for img_path in screenshots:
                try:
                    os.remove(img_path)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass
            
            return True, output_path
            
        except Exception as e:
            logger.error(f"Failed to export static 3D PDF: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    # Alias for backward compatibility
    @staticmethod
    def export_3d_pdf(mesh, output_path, title="3D Model", include_views=True):
        """
        Export mesh to 3D PDF. Tries interactive first, falls back to static.
        
        Args:
            mesh: PyVista mesh object
            output_path: Path for PDF output file
            title: Title for the PDF document
            include_views: Unused, kept for backward compatibility
            
        Returns:
            tuple: (bool, str) - (success, error_message or output_path)
        """
        # include_views kept for backward compatibility; interactive-first behavior preserved.
        return PDF3DExporter.export_interactive_3d_pdf(mesh, output_path, title)
