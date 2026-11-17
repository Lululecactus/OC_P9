"""Validation et réencodage des couvertures envoyées par les lecteurs."""

from io import BytesIO
from uuid import uuid4
import warnings

from PIL import Image, UnidentifiedImageError
from django import forms
from django.core.files.base import ContentFile


class CoverImageField(forms.ImageField):
    """Ne conserve que les pixels d’une image PNG, JPEG ou WebP bornée."""

    max_bytes = 5 * 1024 * 1024
    max_pixels = 12_000_000

    def to_python(self, data):
        # Vérifier la taille avant tout décodage Pillow.
        upload = forms.FileField.to_python(self, data)
        if upload is None:
            return None
        if upload.size > self.max_bytes:
            raise forms.ValidationError('L’image ne doit pas dépasser 5 Mo.')
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                upload.seek(0)
                with Image.open(upload, formats=['PNG', 'JPEG', 'WEBP']) as source:
                    if source.width * source.height > self.max_pixels:
                        raise forms.ValidationError('L’image ne doit pas dépasser 12 millions de pixels.')
                    source.load()
                    # Une image neuve retire métadonnées et contenu ajouté au fichier.
                    pixels = source.convert('RGBA')
                    clean = Image.new('RGBA', source.size)
                    clean.paste(pixels)
                    output = BytesIO()
                    clean.save(output, format='PNG')
        except (UnidentifiedImageError, OSError, ValueError,
                Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise forms.ValidationError('Envoyez une image PNG, JPEG ou WebP valide.')
        if output.tell() > self.max_bytes:
            raise forms.ValidationError('L’image réencodée dépasse 5 Mo. Réduisez ses dimensions.')
        return ContentFile(output.getvalue(), name=f'{uuid4().hex}.png')
