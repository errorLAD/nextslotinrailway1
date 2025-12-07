from storages.backends.s3boto3 import S3Boto3Storage

class StaticRootS3Boto3Storage(S3Boto3Storage):
    """
    Storage for static files.
    The folder is defined in settings.AWS_STATIC_LOCATION
    """
    location = 'static'
    default_acl = 'public-read'
    file_overwrite = False  # Don't overwrite files with the same name

class MediaRootS3Boto3Storage(S3Boto3Storage):
    """
    Storage for media files.
    The folder is defined in settings.AWS_MEDIA_LOCATION
    """
    location = 'media'
    file_overwrite = False  # Don't overwrite files with the same name
