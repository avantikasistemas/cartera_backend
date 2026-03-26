import os
import base64
from datetime import datetime
from pathlib import Path

class FileHandler:
    """
    Manejador de archivos para guardar evidencias
    """
    
    def __init__(self):
        # Carpeta base para uploads
        self.base_path = Path(__file__).parent.parent / "Uploads"
        self.base_path.mkdir(exist_ok=True)
    
    def guardar_imagen_base64(self, base64_data: str, nombre_original: str) -> dict:
        """
        Guarda una imagen desde base64 a archivo físico
        
        Args:
            base64_data: String base64 (puede incluir el prefijo data:image/...)
            nombre_original: Nombre original del archivo
            
        Returns:
            dict con: nombre_archivo, ruta_relativa, tamano_bytes, tipo_mime
        """
        try:
            # Limpiar base64 (remover prefijo data:image/png;base64, si existe)
            if ',' in base64_data:
                header, base64_data = base64_data.split(',', 1)
                # Extraer tipo mime del header
                if 'data:' in header:
                    tipo_mime = header.split(':')[1].split(';')[0]
                else:
                    tipo_mime = 'image/png'
            else:
                tipo_mime = 'image/png'
            
            # Decodificar base64
            imagen_bytes = base64.b64decode(base64_data)
            tamano_bytes = len(imagen_bytes)
            
            # Generar nombre único con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            extension = Path(nombre_original).suffix or '.png'
            nombre_sin_ext = Path(nombre_original).stem
            nombre_archivo = f"{nombre_sin_ext}_{timestamp}{extension}"
            
            # Ruta completa del archivo
            ruta_completa = self.base_path / nombre_archivo
            
            # Guardar archivo
            with open(ruta_completa, 'wb') as f:
                f.write(imagen_bytes)
            
            return {
                'nombre_archivo': nombre_archivo,
                'ruta_relativa': f"Uploads/{nombre_archivo}",
                'tamano_bytes': tamano_bytes,
                'tipo_mime': tipo_mime
            }
            
        except Exception as e:
            print(f"Error guardando archivo: {e}")
            raise
    
    def eliminar_archivo(self, nombre_archivo: str) -> bool:
        """
        Elimina un archivo físico
        
        Args:
            nombre_archivo: Nombre del archivo a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        try:
            ruta_completa = self.base_path / nombre_archivo
            if ruta_completa.exists():
                ruta_completa.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error eliminando archivo {nombre_archivo}: {e}")
            return False
    
    def obtener_ruta_completa(self, nombre_archivo: str) -> Path:
        """
        Obtiene la ruta completa de un archivo
        
        Args:
            nombre_archivo: Nombre del archivo
            
        Returns:
            Path con la ruta completa
        """
        return self.base_path / nombre_archivo
