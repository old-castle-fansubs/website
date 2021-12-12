from datetime import datetime, timezone

import factory
from factory.fuzzy import FuzzyDateTime

from oc_website.models import Project, ProjectRelease


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project


class ProjectReleaseFactory(factory.django.DjangoModelFactory):
    project = factory.SubFactory(ProjectFactory)
    release_date = FuzzyDateTime(datetime(2008, 1, 1, tzinfo=timezone.utc))

    class Meta:
        model = ProjectRelease
