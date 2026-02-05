"""
Annotation Exporter - Save and load annotations with 3D models.

Supports:
- JSON sidecar files for any format
- Embedded annotations in STL comments (limited)
- OBJ comments for annotation storage
"""
import json
import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)


class AnnotationExporter:
    """Handles exporting and importing annotations with 3D model files."""
    
    @staticmethod
    def get_annotation_file_path(model_path: str) -> str:
        """Get the path for the annotation sidecar JSON file.
        
        Args:
            model_path: Path to the 3D model file
            
        Returns:
            Path for the annotation JSON file (same name with .annotations.json)
        """
        base, _ = os.path.splitext(model_path)
        return f"{base}.annotations.json"
    
    @staticmethod
    def save_annotations(annotations: List[dict], model_path: str) -> tuple:
        """Save annotations to a sidecar JSON file.
        
        Args:
            annotations: List of annotation dictionaries from AnnotationPanel.export_annotations()
            model_path: Path to the 3D model file
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not annotations:
            return True, "No annotations to save"
        
        annotation_path = AnnotationExporter.get_annotation_file_path(model_path)
        
        try:
            data = {
                'version': '1.0',
                'model_file': os.path.basename(model_path),
                'annotations': annotations,
            }
            
            with open(annotation_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(annotations)} annotations to {annotation_path}")
            return True, annotation_path
            
        except Exception as e:
            logger.error(f"Failed to save annotations: {e}", exc_info=True)
            return False, str(e)
    
    @staticmethod
    def load_annotations(model_path: str) -> tuple:
        """Load annotations from a sidecar JSON file.
        
        Args:
            model_path: Path to the 3D model file
            
        Returns:
            tuple: (annotations: List[dict] or None, message: str)
        """
        annotation_path = AnnotationExporter.get_annotation_file_path(model_path)
        
        if not os.path.exists(annotation_path):
            return None, "No annotation file found"
        
        try:
            with open(annotation_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            annotations = data.get('annotations', [])
            logger.info(f"Loaded {len(annotations)} annotations from {annotation_path}")
            return annotations, f"Loaded {len(annotations)} annotations"
            
        except Exception as e:
            logger.error(f"Failed to load annotations: {e}", exc_info=True)
            return None, str(e)
    
    @staticmethod
    def export_with_model(mesh, annotations: List[dict], output_path: str) -> tuple:
        """Export a model with its annotations.
        
        Saves the mesh to the specified path and creates a sidecar .annotations.json file.
        
        Args:
            mesh: PyVista mesh object
            annotations: List of annotation dictionaries
            output_path: Path for the output model file
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if mesh is None:
            return False, "No mesh provided"
        
        try:
            # Save the mesh
            mesh.save(output_path)
            logger.info(f"Saved mesh to {output_path}")
            
            # Save annotations if any
            if annotations:
                success, msg = AnnotationExporter.save_annotations(annotations, output_path)
                if success:
                    logger.info(f"Saved annotations alongside mesh")
                    return True, f"Model and {len(annotations)} annotations saved"
                else:
                    logger.warning(f"Model saved but annotations failed: {msg}")
                    return True, f"Model saved, but annotations failed: {msg}"
            
            return True, "Model saved"
            
        except Exception as e:
            logger.error(f"Failed to export model: {e}", exc_info=True)
            return False, str(e)
    
    @staticmethod
    def annotations_exist(model_path: str) -> bool:
        """Check if annotations exist for a model file.
        
        Args:
            model_path: Path to the 3D model file
            
        Returns:
            True if annotation file exists
        """
        annotation_path = AnnotationExporter.get_annotation_file_path(model_path)
        return os.path.exists(annotation_path)
    
    @staticmethod
    def delete_annotations(model_path: str) -> tuple:
        """Delete the annotation file for a model.
        
        Args:
            model_path: Path to the 3D model file
            
        Returns:
            tuple: (success: bool, message: str)
        """
        annotation_path = AnnotationExporter.get_annotation_file_path(model_path)
        
        if not os.path.exists(annotation_path):
            return True, "No annotation file to delete"
        
        try:
            os.remove(annotation_path)
            logger.info(f"Deleted annotation file: {annotation_path}")
            return True, "Annotation file deleted"
            
        except Exception as e:
            logger.error(f"Failed to delete annotation file: {e}", exc_info=True)
            return False, str(e)
