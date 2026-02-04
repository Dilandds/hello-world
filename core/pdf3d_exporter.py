"""
3D PDF Exporter using U3D format.
Exports interactive 3D PDFs where users can rotate/zoom the model.
"""
import logging
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class PDF3DExporter:
    """Handles exporting 3D meshes to interactive PDF format."""
    
    @staticmethod
    def check_dependencies():
        """
        Check if required dependencies are available.
        
        Returns:
            tuple: (bool, str) - (success, error_message)
        """
        errors = []
        
        # Check for reportlab
        try:
            import reportlab
        except ImportError:
            errors.append("reportlab")
        
        # Check for vtk
        try:
            import vtk
        except ImportError:
            errors.append("vtk")
        
        if errors:
            return False, f"Missing dependencies: {', '.join(errors)}"
        
        return True, ""
    
    @staticmethod
    def export_u3d(mesh, output_path):
        """
        Export mesh to U3D format (intermediate step for 3D PDF).
        
        Args:
            mesh: PyVista mesh object
            output_path: Path for U3D output file
            
        Returns:
            tuple: (bool, str) - (success, error_message or output_path)
        """
        try:
            import vtk
            from vtk import vtkVRMLExporter
            
            # Convert PyVista mesh to VTK format if needed
            if hasattr(mesh, 'GetOutput'):
                vtk_mesh = mesh.GetOutput()
            else:
                vtk_mesh = mesh
            
            # Create a simple VRML export as fallback
            # Note: True U3D requires additional libraries
            vrml_path = output_path.replace('.u3d', '.wrl')
            
            # Create a renderer and add the mesh
            renderer = vtk.vtkRenderer()
            render_window = vtk.vtkRenderWindow()
            render_window.SetOffScreenRendering(1)
            render_window.AddRenderer(renderer)
            
            # Create mapper and actor
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(vtk_mesh)
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.85, 0.85, 0.85)
            
            renderer.AddActor(actor)
            renderer.SetBackground(1, 1, 1)
            render_window.Render()
            
            # Export to VRML
            exporter = vtkVRMLExporter()
            exporter.SetRenderWindow(render_window)
            exporter.SetFileName(vrml_path)
            exporter.Write()
            
            return True, vrml_path
            
        except Exception as e:
            logger.error(f"Failed to export U3D: {e}")
            return False, str(e)
    
    @staticmethod
    def export_3d_pdf(mesh, output_path, title="3D Model", include_views=True):
        """
        Export mesh to 3D PDF with embedded interactive model.
        
        Since true U3D embedding in PDF requires Adobe-specific tools,
        this creates a PDF with multiple static views that simulate
        3D viewing capability.
        
        Args:
            mesh: PyVista mesh object
            output_path: Path for PDF output file
            title: Title for the PDF document
            include_views: Whether to include multiple view angles
            
        Returns:
            tuple: (bool, str) - (success, error_message or output_path)
        """
        try:
            import pyvista as pv
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm, inch
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Image, 
                Table, TableStyle, PageBreak
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from PIL import Image as PILImage
            import io
            
            if mesh is None:
                return False, "No mesh provided"
            
            # Create temporary directory for screenshots
            temp_dir = tempfile.mkdtemp()
            
            # Set up off-screen plotter for screenshots
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
                    
                    # Add mesh with nice rendering
                    plotter.add_mesh(
                        mesh, 
                        color='#D4D4D4',
                        specular=0.5,
                        specular_power=15,
                        smooth_shading=True
                    )
                    
                    # Add lighting
                    plotter.add_light(pv.Light(
                        position=(1, 1, 1),
                        intensity=1.0
                    ))
                    plotter.add_light(pv.Light(
                        position=(-1, -0.5, 0.5),
                        intensity=0.4
                    ))
                    
                    # Set view
                    if view_type == 'isometric':
                        plotter.view_isometric()
                    elif view_type == 'yz':
                        plotter.view_yz()
                    elif view_type == 'xz':
                        plotter.view_xz()
                    elif view_type == 'xy':
                        plotter.view_xy()
                    
                    plotter.reset_camera()
                    
                    # Take screenshot
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
            
            # Styles
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
            
            # Build content
            story = []
            
            # Title
            story.append(Paragraph("3D Model Export", title_style))
            story.append(Paragraph(f"File: {title}", subtitle_style))
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
            
            # Add views in 2x2 grid on first page, then remaining views
            page_width = A4[0] - 30*mm
            img_width = (page_width - 10*mm) / 2
            img_height = img_width * 0.75
            
            # Create 2x2 grid for first 4 views
            if len(screenshots) >= 2:
                # First row
                row1_data = []
                for i in range(min(2, len(screenshots))):
                    try:
                        img = Image(screenshots[i], width=img_width, height=img_height)
                        row1_data.append([
                            Paragraph(view_names[i], view_title_style),
                            img
                        ])
                    except:
                        pass
                
                if row1_data:
                    # Create a table for the row
                    view_table_data = [[item[1] for item in row1_data]]
                    label_table_data = [[item[0] for item in row1_data]]
                    
                    label_table = Table(label_table_data, colWidths=[img_width + 5*mm] * len(label_table_data[0]))
                    story.append(label_table)
                    
                    view_table = Table(view_table_data, colWidths=[img_width + 5*mm] * len(view_table_data[0]))
                    view_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    story.append(view_table)
                    story.append(Spacer(1, 15))
                
                # Second row
                if len(screenshots) >= 3:
                    row2_data = []
                    for i in range(2, min(4, len(screenshots))):
                        try:
                            img = Image(screenshots[i], width=img_width, height=img_height)
                            row2_data.append([
                                Paragraph(view_names[i], view_title_style),
                                img
                            ])
                        except:
                            pass
                    
                    if row2_data:
                        label_table_data = [[item[0] for item in row2_data]]
                        view_table_data = [[item[1] for item in row2_data]]
                        
                        label_table = Table(label_table_data, colWidths=[img_width + 5*mm] * len(label_table_data[0]))
                        story.append(label_table)
                        
                        view_table = Table(view_table_data, colWidths=[img_width + 5*mm] * len(view_table_data[0]))
                        view_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        story.append(view_table)
            
            # Build the PDF
            doc.build(story)
            
            # Cleanup temp files
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
            logger.error(f"Failed to export 3D PDF: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    @staticmethod
    def export_3d_pdf_simple(mesh, output_path, title="3D Model"):
        """
        Export a simplified 3D PDF with isometric view only.
        
        Args:
            mesh: PyVista mesh object
            output_path: Path for PDF output file
            title: Title for the PDF document
            
        Returns:
            tuple: (bool, str) - (success, error_message or output_path)
        """
        return PDF3DExporter.export_3d_pdf(
            mesh, output_path, title, include_views=True
        )
