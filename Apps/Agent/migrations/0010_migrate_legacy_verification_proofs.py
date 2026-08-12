# Generated manually — migrate legacy AgentProfile proof files into VerificationDocument

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def forwards_migrate_legacy_proofs(apps, schema_editor):
    AgentProfile = apps.get_model('Agent', 'AgentProfile')
    VerificationDocument = apps.get_model('Agent', 'VerificationDocument')

    status_map = {
        'approved': 'verified',
        'pending': 'pending_review',
        'rejected': 'reupload_required',
        'not_started': 'pending_review',
    }

    for profile in AgentProfile.objects.all():
        agent = profile.user
        mapped_status = status_map.get(profile.verification_status, 'pending_review')
        remarks = profile.verification_remarks or ''

        if profile.id_proof_document:
            exists = VerificationDocument.objects.filter(
                agent=agent,
                document_type='aadhaar',
                is_current=True,
            ).exists()
            if not exists:
                VerificationDocument.objects.create(
                    agent=agent,
                    document_type='aadhaar',
                    document_name='',
                    front_file=profile.id_proof_document,
                    back_file='',
                    has_back_side=False,
                    status=mapped_status if profile.verification_status != 'not_started' else 'pending_review',
                    rejection_reason=remarks if mapped_status == 'reupload_required' else '',
                    is_current=True,
                )

        if profile.address_proof_document:
            exists = VerificationDocument.objects.filter(
                agent=agent,
                document_type='address_proof',
                is_current=True,
            ).exists()
            if not exists:
                VerificationDocument.objects.create(
                    agent=agent,
                    document_type='address_proof',
                    document_name='',
                    front_file=profile.address_proof_document,
                    back_file='',
                    has_back_side=False,
                    status=mapped_status if profile.verification_status != 'not_started' else 'pending_review',
                    rejection_reason=remarks if mapped_status == 'reupload_required' else '',
                    is_current=True,
                )


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Agent', '0009_verificationdocument'),
    ]

    operations = [
        migrations.RunPython(forwards_migrate_legacy_proofs, backwards_noop),
    ]
