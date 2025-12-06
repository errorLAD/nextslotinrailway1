from django.db import models


class DatabaseFile(models.Model):
    """
    Model to store file data in the database.
    """
    name = models.CharField(max_length=255, unique=True)
    data = models.BinaryField()
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'utils_databasefile'
