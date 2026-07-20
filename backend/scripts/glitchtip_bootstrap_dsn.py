"""Bootstrap a GlitchTip project DSN for E2E error-tracking proofs.

Run inside the glitchtip-web container:

    ./manage.py shell < scripts/glitchtip_bootstrap_dsn.py
"""

from __future__ import annotations

from django.contrib.auth import get_user_model


def _import_models():
    try:
        from apps.organizations_ext.models import Organization
        from apps.projects.models import Project, ProjectKey
    except ImportError:
        from organizations_ext.models import Organization  # type: ignore[no-redef]
        from projects.models import Project, ProjectKey  # type: ignore[no-redef]
    return Organization, Project, ProjectKey


def main() -> None:
    Organization, Project, ProjectKey = _import_models()
    User = get_user_model()

    user, created = User.objects.get_or_create(
        username="e2e-admin",
        defaults={
            "email": "e2e-admin@example.com",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if created:
        user.set_password("e2e-admin-pass")
        user.save()

    org, _ = Organization.objects.get_or_create(
        slug="e2e-org",
        defaults={"name": "E2E Org"},
    )
    if hasattr(org, "add_user"):
        org.add_user(user)

    project, _ = Project.objects.get_or_create(
        slug="e2e-project",
        organization=org,
        defaults={"name": "E2E Project"},
    )
    key = ProjectKey.objects.filter(project=project).first()
    if key is None:
        key = ProjectKey.objects.create(project=project, label="e2e")

    dsn = key.get_dsn(domain="glitchtip-web:8000", secure=False, public=True)
    print(f"DSN={dsn}")


main()
