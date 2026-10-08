"""Bounded Library browsing preferences, independent of Qt and gameplay policy."""
from dataclasses import asdict, dataclass


CHOICES = {
    'opening_view': ('gallery', 'details', 'compact'),
    'card_size': ('small', 'default', 'large'),
    'normal_sort': ('name', 'year'),
}


@dataclass(frozen=True)
class LibraryPreferences:
    opening_view: str = 'gallery'
    card_size: str = 'default'
    normal_sort: str = 'name'

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_values(cls, values):
        """Strict submission boundary; never silently save an invalid choice."""
        if not isinstance(values, dict):
            raise ValueError('Library display preferences must be a mapping.')
        for field, choices in CHOICES.items():
            if not isinstance(values.get(field), str) or values[field] not in choices:
                raise ValueError(f'library.display.{field} must be one of {", ".join(choices)}.')
        return cls(**{field: values[field] for field in CHOICES})

    @classmethod
    def from_config(cls, config):
        """Tolerant read boundary; defaults do not cause a persistence write."""
        library = config.get('library', {})
        values = library.get('display', {}) if isinstance(library, dict) else {}
        values = values if isinstance(values, dict) else {}
        defaults = cls().to_dict()
        return cls(**{
            field: values[field] if isinstance(values.get(field), str) and values[field] in choices
            else defaults[field]
            for field, choices in CHOICES.items()
        })


def normalize_loaded_preferences(config):
    """Normalize only an existing display section, preserving unknown fields."""
    library = config.get('library')
    if isinstance(library, dict) and 'display' in library:
        preferences = LibraryPreferences.from_config(config)
        display = library['display']
        library['display'] = {
            **(display if isinstance(display, dict) else {}),
            **preferences.to_dict(),
        }
    return config
