"""
Custom storage backend for storing files in PostgreSQL database.
"""
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import models
from django.urls import reverse
from .models import DatabaseFile
import os


class DatabaseStorage(Storage):
    """
    A storage implementation that stores files in the database.
    """
    def _open(self, name, mode='rb'):
        # Convert absolute paths to relative
        name = os.path.basename(name)
        try:
            db_file = DatabaseFile.objects.get(name=name)
            return ContentFile(bytes(db_file.data), name=name)
        except DatabaseFile.DoesNotExist:
            raise FileNotFoundError(f"File {name} does not exist in database")

    def _save(self, name, content):
        # Convert absolute paths to relative
        name = os.path.basename(name)
        
        # If the file already exists, delete it first
        DatabaseFile.objects.filter(name=name).delete()
        
        # Read the file content
        content.seek(0)
        file_data = content.read()
        
        # Create a new database record
        db_file = DatabaseFile(
            name=name,
            data=file_data,
            content_type=getattr(content, 'content_type', 'application/octet-stream'),
            size=len(file_data)
        )
        db_file.save()
        
        return name

    def delete(self, name):
        # Convert absolute paths to relative
        name = os.path.basename(name)
        DatabaseFile.objects.filter(name=name).delete()

    def exists(self, name):
        # Convert absolute paths to relative
        name = os.path.basename(name)
        return DatabaseFile.objects.filter(name=name).exists()

    def size(self, name):
        # Convert absolute paths to relative
        name = os.path.basename(name)
        try:
            return DatabaseFile.objects.get(name=name).size
        except DatabaseFile.DoesNotExist:
            return 0

    def url(self, name):
        # Always work with just the basename
        name = os.path.basename(name)

        # Try to use the dedicated DB media serving view
        try:
            return reverse("utils:serve_db_file", kwargs={"name": name})
        except Exception:
            # Fallback to MEDIA_URL pattern if reverse fails for any reason
            base = getattr(settings, "MEDIA_URL", "/media/")
            return f"{base.rstrip('/')}/{name}"

    def get_available_name(self, name, max_length=None):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        # Convert to basename to handle absolute paths
        name = os.path.basename(name)
        
        # If the file doesn't exist, return the name as is
        if not self.exists(name):
            return name
            
        # If it exists, generate a new name with a number
        file_root, file_ext = os.path.splitext(name)
        count = 1
        
        while True:
            # Generate new name with number
            new_name = f"{file_root}_{count}{file_ext}"
            
            # Check if new name is too long
            if max_length and len(new_name) > max_length:
                # Truncate the filename root if needed
                truncate_length = max_length - len(file_ext) - len(str(count)) - 1
                if truncate_length > 0:
                    file_root = file_root[:truncate_length]
                    new_name = f"{file_root}_{count}{file_ext}"
            
            # If the new name doesn't exist, return it
            if not self.exists(new_name):
                return new_name
                
            count += 1
