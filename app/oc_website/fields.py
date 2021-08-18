from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.fields import URLField as FormURLField


class MagnetURLValidator(validators.URLValidator):
    def __call__(self, value: str) -> None:
        try:
            super().__call__(value)
        except ValidationError:
            if isinstance(value, str) and value.startswith("magnet:"):
                return
            raise


class MagnetURLFormField(FormURLField):
    default_validators = [MagnetURLValidator()]


class MagnetURLField(models.URLField):
    """URL field that accepts URLs that start with magnet:// or https:// only."""

    default_validators = [MagnetURLValidator()]

    def formfield(self, **kwargs):
        return super().formfield(
            **{**kwargs, "form_class": MagnetURLFormField}
        )
