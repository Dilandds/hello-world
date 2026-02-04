"""
3D PDF Exporter using Aspose.3D library.
Exports interactive 3D PDFs where users can rotate/zoom the model in Adobe Acrobat Reader.

Requirements:
- Python 3.11 (Aspose-3D requires Python < 3.12)
- pip install aspose-3d
"""
import logging
import tempfile
import os
import sys
import platform

logger = logging.getLogger(__name__)


class PDF3DExporter:
    """
    Handles exporting 3D meshes to interactive PDF format.
    
    Creates PDFs with embedded 3D annotations that work in Adobe Acrobat Reader.
    Users can rotate, pan, and zoom the 3D model within the PDF.
    """

    @staticmethod
    def _log_runtime_context():
        """Log runtime context to help diagnose export availability."""
        logger.info(
            "3D PDF runtime context | python=%s | platform=%s | executable=%s",
            sys.version.replace("\n", " "),
            platform.platform(),
            sys.executable,
        )

    @staticmethod
    def check_aspose_available():
        """Check if Aspose.3D is available for 3D PDF export."""
        PDF3DExporter._log_runtime_context()
        
        # Check Python version first
        py_version = sys.version_info
        if py_version >= (3, 12):
            msg = f"Python {py_version.major}.{py_version.minor} detected. Aspose-3D requires Python < 3.12. Please use Python 3.11."
            logger.error(msg)
            return False, msg
        
        try:
            from aspose.threed import Scene
            from aspose.threed.formats import PdfSaveOptions
            logger.info("Aspose.3D is available for 3D PDF export")
            return True, "Aspose.3D available"
        except ImportError as e:
            logger.warning("Aspose.3D not available: %s", e)
            return False, f"Aspose.3D not installed. Install with: pip install aspose-3d"
        except Exception as e:
            logger.error("Error checking Aspose.3D: %s", e, exc_info=True)
            return False, str(e)

    @staticmethod
    def export_interactive_3d_pdf(mesh, output_path, title="3D Model", allow_static_fallback: bool = False):
        """
        Export mesh to an interactive 3D PDF using Aspose.3D.
        
        Args:
            mesh: PyVista mesh object
            output_path: Path for the output PDF
            title: Title for the document
            allow_static_fallback: If True, fall back to static PDF when Aspose unavailable
            
        Returns:
            tuple: (bool, str) - (success, output_path or error_message)
        """
        if mesh is None:
            return False, "No mesh provided"

        logger.info("=" * 60)
        logger.info("Starting interactive 3D PDF export")
        logger.info("Output path: %s", output_path)
        logger.info("Title: %s", title)
        logger.info("=" * 60)

        # Check if Aspose is available
        available, msg = PDF3DExporter.check_aspose_available()
        if not available:
            logger.error("Interactive 3D PDF export not available: %s", msg)
            if allow_static_fallback:
                logger.warning("Falling back to static PDF")
                return PDF3DExporter.export_static_3d_pdf(mesh, output_path, title)
            return False, msg

        temp_dir = tempfile.mkdtemp()
        logger.info("Created temp directory: %s", temp_dir)
        
        try:
            # Export mesh to temporary STL file first
            temp_stl = os.path.join(temp_dir, "temp_model.stl")
            
            # Get mesh statistics for logging
            try:
                n_points = mesh.n_points if hasattr(mesh, 'n_points') else mesh.GetNumberOfPoints()
                n_cells = mesh.n_cells if hasattr(mesh, 'n_cells') else mesh.GetNumberOfCells()
                logger.info("Mesh statistics: points=%d, cells=%d", n_points, n_cells)
            except Exception as e:
                logger.debug("Could not read mesh statistics: %s", e)
            
            # Save PyVista mesh to STL
            try:
                logger.info("Saving mesh to temporary STL: %s", temp_stl)
                mesh.save(temp_stl)
                stl_size = os.path.getsize(temp_stl)
                logger.info("STL saved successfully: %d bytes", stl_size)
            except Exception as e:
                logger.error("Failed to save temporary STL: %s", e, exc_info=True)
                return False, f"Failed to save temporary STL: {e}"
            
            # Use Aspose.3D to convert STL to interactive 3D PDF
            try:
                logger.info("Importing Aspose.3D modules...")
                from aspose.threed import Scene
                from aspose.threed.formats import PdfSaveOptions, PdfLightingScheme, PdfRenderMode
                logger.info("Aspose.3D modules imported successfully")
                
                # Load the STL file
                logger.info("Loading STL into Aspose.3D Scene...")
                scene = Scene.from_file(temp_stl)
                logger.info("STL loaded into Aspose.3D Scene successfully")
                
                # Configure PDF export options for maximum interactivity
                logger.info("Configuring PDF export options...")
                pdf_options = PdfSaveOptions()
                pdf_options.lighting_scheme = PdfLightingScheme.CAD
                pdf_options.render_mode = PdfRenderMode.SHADED_ILLUSTRATION
                
                # Try to set additional options if available
                try:
                    if hasattr(pdf_options, 'embed_textures'):
                        pdf_options.embed_textures = True
                        logger.info("Enabled texture embedding")
                except Exception as e:
                    logger.debug("Could not set embed_textures: %s", e)
                
                logger.info("PDF options configured: lighting=%s, render_mode=%s", 
                           pdf_options.lighting_scheme, pdf_options.render_mode)
                
                # Save as 3D PDF
                logger.info("Exporting to 3D PDF: %s", output_path)
                scene.save(output_path, pdf_options)
                logger.info("Aspose.3D scene.save() completed")
                
                # Verify output
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info("=" * 60)
                    logger.info("3D PDF CREATED SUCCESSFULLY")
                    logger.info("Path: %s", output_path)
                    logger.info("Size: %d bytes (%.2f KB)", file_size, file_size / 1024)
                    logger.info("=" * 60)
                    
                    if file_size < 1024:
                        logger.warning("WARNING: PDF file is unexpectedly small (%d bytes) - may indicate an issue", file_size)
                    
                    return True, output_path
                else:
                    logger.error("PDF file was not created at: %s", output_path)
                    return False, "PDF file was not created"
                    
            except Exception as e:
                logger.error("Aspose.3D export failed: %s", e, exc_info=True)
                if allow_static_fallback:
                    logger.warning("Falling back to static PDF after Aspose error")
                    return PDF3DExporter.export_static_3d_pdf(mesh, output_path, title)
                return False, f"Aspose.3D export failed: {e}"
                
        finally:
            # Cleanup temporary files
            try:
                for name in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, name))
                    except Exception:
                        pass
                os.rmdir(temp_dir)
                logger.debug("Cleaned up temp directory: %s", temp_dir)
            except Exception as e:
                logger.debug("Could not clean up temp directory: %s", e)
    
    @staticmethod
    def export_static_3d_pdf(mesh, output_path, title="3D Model"):
        """
        Export static PDF with multiple high-quality view screenshots.
        This is used as a fallback when interactive export is not available.
        
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
            
            logger.info("Creating static PDF with multiple views...")
            
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
                    logger.info("Captured %s view", view_name)
                    
                except Exception as e:
                    logger.warning("Failed to capture %s view: %s", view_name, e)
            
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
            logger.info("Static PDF created: %s", output_path)
            
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
            logger.error("Failed to export static 3D PDF: %s", e, exc_info=True)
            return False, str(e)
    
    # Backward compatibility aliases
    @staticmethod
    def check_u3d_exporter():
        """Check if 3D PDF export is available (backward compatibility)."""
        return PDF3DExporter.check_aspose_available()
    
    @staticmethod
    def export_3d_pdf(mesh, output_path, title="3D Model", include_views=True):
        """
        Export mesh to 3D PDF (backward compatibility).
        
        Args:
            mesh: PyVista mesh object
            output_path: Path for PDF output file
            title: Title for the PDF document
            include_views: Unused, kept for backward compatibility
            
        Returns:
            tuple: (bool, str) - (success, error_message or output_path)
        """
        return PDF3DExporter.export_interactive_3d_pdf(mesh, output_path, title, allow_static_fallback=False)
