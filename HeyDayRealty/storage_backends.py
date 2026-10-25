from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

# Check if AWS credentials are provided
USE_S3 = bool(getattr(settings, 'AWS_ACCESS_KEY_ID', None) and getattr(settings, 'AWS_SECRET_ACCESS_KEY', None))

if USE_S3:
    class BaseRoleMediaStorage(S3Boto3Storage):
        """
        Base storage class that sets common S3 properties for Storj/S3.
        """
        access_key = settings.AWS_ACCESS_KEY_ID
        secret_key = settings.AWS_SECRET_ACCESS_KEY
        endpoint_url = settings.AWS_S3_ENDPOINT_URL
        region_name = settings.AWS_S3_REGION_NAME
        default_acl = settings.AWS_DEFAULT_ACL
        querystring_auth = False

    class AgentMediaStorage(BaseRoleMediaStorage):
        bucket_name = settings.AWS_AGENT_BUCKET_NAME

    class CustomerMediaStorage(BaseRoleMediaStorage):
        bucket_name = settings.AWS_CUSTOMER_BUCKET_NAME

    class AdminMediaStorage(BaseRoleMediaStorage):
        bucket_name = settings.AWS_ADMIN_BUCKET_NAME

    class PropertyMediaStorage(BaseRoleMediaStorage):
        bucket_name = settings.AWS_PROPERTY_BUCKET_NAME

        def _save(self, name, content):
            """Override to catch SSL/network errors and fall back to local storage."""
            try:
                return super()._save(name, content)
            except Exception as exc:
                # botocore/urllib3 SSL errors surface as various exception types;
                # catching broadly here so a transient Storj issue doesn't break
                # the entire property submission in development.
                logger.error(
                    "PropertyMediaStorage: failed to upload '%s' to Storj (%s: %s). "
                    "Falling back to local FileSystemStorage.",
                    name, type(exc).__name__, exc,
                )
                local = FileSystemStorage()
                return local._save(name, content)

    class GeneralMediaStorage(BaseRoleMediaStorage):
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
else:
    # Fallback to local storage when AWS credentials are not provided in development
    class BaseRoleMediaStorage(FileSystemStorage):
        pass

    class AgentMediaStorage(FileSystemStorage):
        pass

    class CustomerMediaStorage(FileSystemStorage):
        pass

    class AdminMediaStorage(FileSystemStorage):
        pass

    class PropertyMediaStorage(FileSystemStorage):
        pass

    class GeneralMediaStorage(FileSystemStorage):
        pass



def generate_unique_upload_path(instance, filename, folder_name="general"):
    """
    Utility function to generate unique upload paths.
    Format: {user_id}_{username}/{folder_name}/{filename}
    """
    user_id = 'unknown_id'
    username = 'unknown_user'

    # Try to extract user info depending on the instance type
    if hasattr(instance, 'user') and instance.user:
        user_id = instance.user.id
        username = instance.user.username
    elif hasattr(instance, 'id') and hasattr(instance, 'username'):
        # In case the instance IS the user model
        user_id = instance.id
        username = instance.username

    # Sanitize username for path
    safe_username = str(username).replace(' ', '_').lower()
    
    # Example: 12_ajaysingh/kyc_docs/passport.jpg
    return f"{user_id}_{safe_username}/{folder_name}/{filename}"

# Specific path generators for models to use in upload_to
def get_agent_profile_path(instance, filename):
    return generate_unique_upload_path(instance, filename, "profile_images")

def get_agent_kyc_path(instance, filename):
    return generate_unique_upload_path(instance, filename, "kyc_documents")

def get_agent_id_proof_path(instance, filename):
    return generate_unique_upload_path(instance, filename, "agent_verification/id_proof")

def get_agent_address_proof_path(instance, filename):
    return generate_unique_upload_path(instance, filename, "agent_verification/address_proof")

def get_agent_verification_front_path(instance, filename):
    return generate_unique_upload_path(instance.agent, filename, "agent_verification/front")

def get_agent_verification_back_path(instance, filename):
    return generate_unique_upload_path(instance.agent, filename, "agent_verification/back")

def get_customer_profile_path(instance, filename):
    return generate_unique_upload_path(instance, filename, "customer_profiles")

def get_admin_profile_path(instance, filename):
    return generate_unique_upload_path(instance, filename, "admin_profiles")

def get_agent_document_path(instance, filename):
    # Depending on model structure, instance.agent usually exists
    user_obj = instance.agent if hasattr(instance, 'agent') else instance
    return generate_unique_upload_path(user_obj, filename, "documents")

def get_property_image_path(instance, filename):
    """
    Build the storage path for property-related media.

    The Property model uses a `seller` FK (not `agent`), so we read that.
    PropertyImage rows link back to the property via `instance.property`.
    We also guard against the object not yet having a PK (pre-save) by using
    'new' as the folder name in that edge-case.
    """
    # --- resolve the owning user ---
    # Direct seller FK on Property
    if hasattr(instance, 'seller') and instance.seller_id:
        user_identifier = f"seller_{instance.seller_id}"
    # PropertyImage has a FK called `property` which has a `seller`
    elif hasattr(instance, 'property') and instance.property and instance.property.seller_id:
        user_identifier = f"seller_{instance.property.seller_id}"
    # Fallback: agent FK (other models that reuse this helper)
    elif hasattr(instance, 'agent') and instance.agent:
        user_identifier = f"agent_{instance.agent.id}"
    else:
        user_identifier = "system"

    # Use PK if already saved, else 'new' to avoid 'None' in the path
    obj_id = instance.pk if instance.pk else "new"
    return f"properties/{user_identifier}/{obj_id}/{filename}"
