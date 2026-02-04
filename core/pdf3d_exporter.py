"""
3D PDF Exporter using U3D format.
Exports interactive 3D PDFs where users can rotate/zoom the model in Adobe Acrobat Reader.
"""
import logging
import tempfile
import os
import struct
import zlib
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class PDF3DExporter:
    """
    Handles exporting 3D meshes to interactive PDF format.
    
    Creates PDFs with embedded U3D 3D annotations that work in Adobe Acrobat Reader.
    Users can rotate, pan, and zoom the 3D model within the PDF.
    """
    
    @staticmethod
    def check_u3d_exporter():
        """
        Check if vtkU3DExporter is available.
        
        Returns:
            tuple: (bool, str) - (available, message)
        """
        try:
            from vtkU3DExporter import vtkU3DExporter
            return True, "vtkU3DExporter available"
        except ImportError:
            return False, "vtkU3DExporter not installed. Install with: pip install vtk-u3dexporter"
    
    @staticmethod
    def mesh_to_u3d(mesh, output_path):
        """
        Export PyVista mesh to U3D format using vtkU3DExporter.
        
        Args:
            mesh: PyVista mesh object
            output_path: Path for U3D output (without .u3d extension)
            
        Returns:
            tuple: (bool, str) - (success, u3d_file_path or error_message)
        """
        try:
            import vtk
            from vtkU3DExporter import vtkU3DExporter
            
            # Create off-screen render window
            render_window = vtk.vtkRenderWindow()
            render_window.SetOffScreenRendering(1)
            render_window.SetSize(800, 600)
            
            renderer = vtk.vtkRenderer()
            renderer.SetBackground(1.0, 1.0, 1.0)
            render_window.AddRenderer(renderer)
            
            # Create mapper and actor from mesh
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(mesh)
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            # Set a nice silver/gray color
            actor.GetProperty().SetColor(0.75, 0.75, 0.78)
            actor.GetProperty().SetSpecular(0.3)
            actor.GetProperty().SetSpecularPower(20)
            
            renderer.AddActor(actor)
            renderer.ResetCamera()
            
            # Render once to initialize
            render_window.Render()
            
            # Export to U3D
            exporter = vtkU3DExporter()
            exporter.SetFileName(output_path)
            exporter.SetInput(render_window)
            exporter.Write()
            
            u3d_path = f"{output_path}.u3d"
            if os.path.exists(u3d_path):
                return True, u3d_path
            else:
                return False, "U3D export failed - file not created"
                
        except ImportError as e:
            logger.error(f"vtkU3DExporter not available: {e}")
            return False, "vtkU3DExporter not installed. Install with: pip install vtk-u3dexporter"
        except Exception as e:
            logger.error(f"Failed to export U3D: {e}")
            return False, str(e)
    
    @staticmethod
    def create_3d_pdf(u3d_path, output_pdf_path, title="3D Model", mesh_info=None):
        """
        Create a PDF with embedded interactive 3D U3D content.
        
        This creates a PDF with a 3D annotation that allows rotation/zoom in Adobe Reader.
        
        Args:
            u3d_path: Path to the U3D file
            output_pdf_path: Path for the output PDF
            title: Title for the document
            mesh_info: Optional dict with mesh dimensions/properties
            
        Returns:
            tuple: (bool, str) - (success, output_path or error_message)
        """
        try:
            # Read the U3D file
            with open(u3d_path, 'rb') as f:
                u3d_data = f.read()
            
            # Compress U3D data with FlateDecode
            compressed_u3d = zlib.compress(u3d_data)
            
            # Build PDF structure
            pdf_objects = []
            
            # Object 1: Catalog
            pdf_objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
            
            # Object 2: Pages
            pdf_objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
            
            # Object 3: Page (A4 size: 595 x 842 points)
            page_width = 595
            page_height = 842
            margin = 50
            
            # 3D annotation rectangle (large, centered)
            annot_x1 = margin
            annot_y1 = 200
            annot_x2 = page_width - margin
            annot_y2 = page_height - 100
            
            pdf_objects.append(
                f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
                f"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> "
                f"/Annots [6 0 R] >>\nendobj\n".encode()
            )
            
            # Object 4: Page content stream (title text)
            content = f"""
BT
/F1 18 Tf
{margin} {page_height - 60} Td
({title}) Tj
ET
BT
/F1 10 Tf
{margin} {page_height - 80} Td
(Interactive 3D Model - Use mouse to rotate, scroll to zoom) Tj
ET
"""
            # Add mesh info if available
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
            
            content_bytes = content.encode('latin-1')
            pdf_objects.append(
                f"4 0 obj\n<< /Length {len(content_bytes)} >>\nstream\n".encode() +
                content_bytes +
                b"\nendstream\nendobj\n"
            )
            
            # Object 5: Font
            pdf_objects.append(
                b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
            )
            
            # Object 6: 3D Annotation
            pdf_objects.append(
                f"6 0 obj\n<< /Type /Annot /Subtype /3D "
                f"/Rect [{annot_x1} {annot_y1} {annot_x2} {annot_y2}] "
                f"/3DD 7 0 R "
                f"/3DV 8 0 R "
                f"/3DA << /A /PO /AIS /L /DIS /I >> "
                f"/F 4 "
                f"/Contents (3D Model) "
                f">>\nendobj\n".encode()
            )
            
            # Object 7: 3D Stream (the U3D data)
            pdf_objects.append(
                f"7 0 obj\n<< /Type /3D /Subtype /U3D "
                f"/Length {len(compressed_u3d)} /Filter /FlateDecode >>\nstream\n".encode() +
                compressed_u3d +
                b"\nendstream\nendobj\n"
            )
            
            # Object 8: Default 3D View
            # Camera position for isometric-like view
            # C2W is a 12-element array: rotation matrix (9) + translation (3)
            # This creates a nice isometric view
            pdf_objects.append(
                b"8 0 obj\n<< /Type /3DView /XN (Default) /IN (Default View) "
                b"/MS /M "
                b"/C2W [0.707 0.408 -0.577 0 0.816 0.577 0.707 -0.408 0.577 0 0 100] "
                b"/CO 100 "
                b"/P << /Subtype /O >> "
                b"/BG << /Type /3DBG /CS /DeviceRGB /C [1 1 1] >> "
                b"/LS << /Type /3DLightingScheme /Subtype /CAD >> "
                b">>\nendobj\n"
            )
            
            # Build PDF file
            pdf_header = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n"
            
            # Calculate object positions
            positions = []
            current_pos = len(pdf_header)
            
            pdf_body = b""
            for obj in pdf_objects:
                positions.append(current_pos)
                pdf_body += obj
                current_pos += len(obj)
            
            # Build xref table
            xref_pos = len(pdf_header) + len(pdf_body)
            xref = f"xref\n0 {len(pdf_objects) + 1}\n0000000000 65535 f \n"
            for pos in positions:
                xref += f"{pos:010d} 00000 n \n"
            xref = xref.encode()
            
            # Trailer
            trailer = f"trailer\n<< /Size {len(pdf_objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
            
            # Write PDF
            with open(output_pdf_path, 'wb') as f:
                f.write(pdf_header)
                f.write(pdf_body)
                f.write(xref)
                f.write(trailer)
            
            return True, output_pdf_path
            
        except Exception as e:
            logger.error(f"Failed to create 3D PDF: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    @staticmethod
    def export_interactive_3d_pdf(mesh, output_path, title="3D Model"):
        """
        Export mesh to an interactive 3D PDF that works in Adobe Acrobat Reader.
        
        Args:
            mesh: PyVista mesh object
            output_path: Path for the output PDF
            title: Title for the document
            
        Returns:
            tuple: (bool, str) - (success, output_path or error_message)
        """
        if mesh is None:
            return False, "No mesh provided"
        
        # Check if vtkU3DExporter is available
        available, msg = PDF3DExporter.check_u3d_exporter()
        if not available:
            logger.warning(f"vtkU3DExporter not available: {msg}")
            # Fall back to static PDF
            return PDF3DExporter.export_static_3d_pdf(mesh, output_path, title)
        
        try:
            # Create temp directory for U3D
            temp_dir = tempfile.mkdtemp()
            u3d_base = os.path.join(temp_dir, "model")
            
            # Export to U3D
            success, result = PDF3DExporter.mesh_to_u3d(mesh, u3d_base)
            if not success:
                logger.warning(f"U3D export failed: {result}, falling back to static PDF")
                return PDF3DExporter.export_static_3d_pdf(mesh, output_path, title)
            
            u3d_path = result
            
            # Get mesh info
            from core.mesh_calculator import MeshCalculator
            mesh_info = MeshCalculator.get_mesh_data(mesh)
            
            # Create 3D PDF
            success, result = PDF3DExporter.create_3d_pdf(
                u3d_path, output_path, title, mesh_info
            )
            
            # Cleanup temp files
            try:
                os.remove(u3d_path)
                os.rmdir(temp_dir)
            except:
                pass
            
            return success, result
            
        except Exception as e:
            logger.error(f"Failed to export interactive 3D PDF: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to static PDF
            return PDF3DExporter.export_static_3d_pdf(mesh, output_path, title)
    
    @staticmethod
    def export_static_3d_pdf(mesh, output_path, title="3D Model"):
        """
        Fallback: Export static PDF with multiple view screenshots.
        Used when vtkU3DExporter is not available.
        
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
            
            story.append(Paragraph("3D Model Export (Static Views)", title_style))
            story.append(Paragraph(
                f"File: {title}<br/>"
                "<font color='#EF4444'>Note: Install vtk-u3dexporter for interactive 3D PDFs</font>",
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
        return PDF3DExporter.export_interactive_3d_pdf(mesh, output_path, title)
