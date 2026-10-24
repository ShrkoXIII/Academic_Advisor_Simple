"""Shared validation for optional model selection; omitted means legacy A/B/C."""


def normalize_models(models=None):
    if models is None:
        return ('A', 'B', 'C')
    if (not isinstance(models, (list, tuple)) or not models or
            any(not isinstance(name, str) or name not in ('A', 'B', 'C') for name in models) or
            len(set(models)) != len(models)):
        raise ValueError('Select one or more distinct Pilot models: A, B, C.')
    return tuple(name for name in ('A', 'B', 'C') if name in models)
