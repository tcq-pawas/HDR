"""
API Views for Contact Inquiry API
Handles contact form submissions from multiple websites
"""

import logging
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.db import transaction
from django.shortcuts import render
from django.conf import settings
from .constants import WEBSITE_CONFIG, SUCCESS_MESSAGE, UNEXPECTED_ERROR_MESSAGE
from .contact_serializers import ContactInquirySerializer, ContactInquiryResponseSerializer
from .emails import send_contact_inquiry_email


logger = logging.getLogger('contact_inquiry_api')


class ContactInquiryAPIView(APIView):
    """
    API endpoint for handling contact form submissions from multiple websites
    
    POST /api/contact/
    
    Accepts JSON requests with dynamic validation based on website configuration.
    
    Authentication: API key via X-API-Key header
    """
    authentication_classes = []
    permission_classes = []
    
    @extend_schema(
        tags=['Contact Inquiry'],
        summary='Submit contact inquiry',
        description='Submit a contact inquiry from any configured website (HeyDay Realty or TheCodiQ Global). The API dynamically validates fields based on the website configuration. Requires X-API-Key header for authentication.',
        parameters=[
            OpenApiParameter(
                name='X-API-Key',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description='API key for authentication (HeyDay or CodiQ key)',
                required=True
            )
        ],
        request=ContactInquirySerializer,
        responses={
            200: ContactInquiryResponseSerializer,
            400: ContactInquiryResponseSerializer,
            401: ContactInquiryResponseSerializer,
            500: ContactInquiryResponseSerializer,
        },
        examples=[
            OpenApiExample(
                'HeyDay Realty Inquiry',
                summary='Submit a property inquiry for HeyDay Realty',
                value={
                    'website': 'heyday',
                    'full_name': 'John Doe',
                    'phone_number': '+1234567890',
                    'email': 'john@example.com',
                    'subject': 'Property Inquiry',
                    'preferred_contact_method': 'email',
                    'property_type': 'apartment',
                    'preferred_location': 'Downtown',
                    'budget_range': '10m_20m',
                    'area_size': '1000_2000',
                    'message': 'I am interested in this property.'
                }
            ),
            OpenApiExample(
                'TheCodiQ Global Inquiry',
                summary='Submit a website inquiry for TheCodiQ Global',
                value={
                    'website': 'thecodiq',
                    'full_name': 'Jane Smith',
                    'phone_number': '+9876543210',
                    'email': 'jane@example.com',
                    'message': 'I would like to discuss a project.'
                }
            )
        ]
    )
    
    def post(self, request):
        """
        Handle contact inquiry submission
        
        Request headers must include:
        - X-API-Key: Valid API key for the website
        
        Request body must include:
        - website: 'heyday' or 'thecodiq'
        - Other required fields based on website configuration
        
        Returns:
            - 200: Success response
            - 401: Invalid API key
            - 400: Validation error
            - 500: Unexpected error
        """
        # Validate API key
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            response_serializer = ContactInquiryResponseSerializer({
                'success': False,
                'message': 'API key is required. Please provide X-API-Key header.'
            })
            return Response(
                response_serializer.data,
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        valid_keys = [
            getattr(settings, 'CONTACT_API_KEY_HEYDAY', ''),
            getattr(settings, 'CONTACT_API_KEY_CODIQ', '')
        ]
        
        if api_key not in valid_keys:
            response_serializer = ContactInquiryResponseSerializer({
                'success': False,
                'message': 'Invalid API key. Access denied.'
            })
            return Response(
                response_serializer.data,
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Validate and deserialize request
            serializer = ContactInquirySerializer(
                data=request.data,
                context={'request': request}
            )
            
            if not serializer.is_valid():
                logger.warning(
                    f"Contact inquiry validation failed: {serializer.errors}"
                )
                
                response_serializer = ContactInquiryResponseSerializer({
                    'success': False,
                    'message': 'Validation failed. Please check the errors below.',
                    'errors': serializer.errors
                })
                
                return Response(
                    response_serializer.data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save inquiry within a transaction
            with transaction.atomic():
                inquiry = serializer.save()
            
            # Get website configuration
            website = inquiry.website
            website_config = WEBSITE_CONFIG.get(website)
            
            if not website_config:
                logger.error(f"No configuration found for website: {website}")
            else:
                # Send email notification (non-blocking failure)
                try:
                    email_success, email_message = send_contact_inquiry_email(
                        inquiry,
                        website_config
                    )
                    
                    if not email_success:
                        logger.warning(
                            f"Email sending failed for inquiry {inquiry.id}: {email_message}"
                        )
                    # Note: We don't fail the API if email fails
                
                except Exception as email_error:
                    logger.error(
                        f"Unexpected error during email sending for inquiry {inquiry.id}: {str(email_error)}",
                        exc_info=True
                    )
                    # Note: We don't fail the API if email fails
            
            # Return success response
            response_serializer = ContactInquiryResponseSerializer({
                'success': True,
                'message': SUCCESS_MESSAGE
            })
            
            logger.info(
                f"Contact inquiry processed successfully for website {website} "
                f"from {inquiry.email}"
            )
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(
                f"Unexpected error in ContactInquiryAPIView: {str(e)}",
                exc_info=True
            )
            
            response_serializer = ContactInquiryResponseSerializer({
                'success': False,
                'message': UNEXPECTED_ERROR_MESSAGE
            })
            
            return Response(
                response_serializer.data,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContactAPIDocumentationView:
    """
    View to serve the Contact API documentation
    """
    
    def __init__(self):
        self.doc_path = os.path.join(
            os.path.dirname(__file__),
            'CONTACT_API_DOCUMENTATION.md'
        )
    
    def __call__(self, request):
        """
        Render the documentation as HTML
        """
        try:
            with open(self.doc_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Simple markdown to HTML conversion
            html_content = self._markdown_to_html(markdown_content)
            
            return render(request, 'administration/api_documentation.html', {
                'title': 'Contact Inquiry API Documentation',
                'content': html_content
            })
        
        except FileNotFoundError:
            return render(request, 'administration/api_documentation.html', {
                'title': 'Contact Inquiry API Documentation',
                'content': '<p>Documentation file not found.</p>'
            })
    
    def _markdown_to_html(self, markdown):
        """
        Simple markdown to HTML converter
        """
        html = markdown
        
        # Headers
        html = html.replace('### ', '<h3>').replace('\n', '</h3>\n', 1)
        html = html.replace('## ', '<h2>').replace('\n', '</h2>\n', 1)
        html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
        
        # Code blocks
        html = html.replace('```json', '<pre><code class="language-json">')
        html = html.replace('```python', '<pre><code class="language-python">')
        html = html.replace('```', '</code></pre>')
        
        # Inline code
        html = html.replace('`', '<code>')
        
        # Bold
        html = html.replace('**', '<strong>')
        
        # Lists
        lines = html.split('\n')
        in_list = False
        for i, line in enumerate(lines):
            if line.startswith('- '):
                if not in_list:
                    lines[i] = '<ul>' + line.replace('- ', '<li>')
                    in_list = True
                else:
                    lines[i] = line.replace('- ', '<li>')
            elif in_list and not line.startswith(' '):
                lines[i] = '</li></ul>' + line
                in_list = False
        
        html = '\n'.join(lines)
        
        # Paragraphs
        paragraphs = html.split('\n\n')
        html = '\n\n'.join(
            f'<p>{p}</p>' if not p.startswith('<') else p 
            for p in paragraphs
        )
        
        return html
