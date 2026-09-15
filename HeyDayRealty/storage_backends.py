from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
import os

class BaseRoleMediaStorage(S3Boto3Storage):
    """
    Base storage class that sets common S3 properties for Storj.
    """
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    endpoint_url = settings.AWS_S3_ENDPOINT_URL
    region_name = settings.AWS_S3_REGION_NAME
    default_acl = settings.AWS_DEFAULT_ACL

class AgentMediaStorage(BaseRoleMediaStorage):
    bucket_name = settings.AWS_AGENT_BUCKET_NAME

class CustomerMediaStorage(BaseRoleMediaStorage):
    bucket_name = settings.AWS_CUSTOMER_BUCKET_NAME

class AdminMediaStorage(BaseRoleMediaStorage):
    bucket_name = settings.AWS_ADMIN_BUCKET_NAME

class PropertyMediaStorage(BaseRoleMediaStorage):
    # Typically properties are managed by agents or admins, but we might want a central bucket
    bucket_name = settings.AWS_PROPERTY_BUCKET_NAME
    
class GeneralMediaStorage(BaseRoleMediaStorage):
    # Fallback for subscriptions, org logos, etc.
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME


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
    # Properties might be tied to an agent
    user_identifier = f"agent_{instance.agent.id}" if hasattr(instance, 'agent') and instance.agent else "system"
    return f"properties/{user_identifier}/{instance.id}/{filename}"
