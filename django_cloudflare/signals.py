"""
Django signals for automatic cache purging.

This module sets up signal handlers to automatically purge cache
when models are saved or deleted.
"""

import logging
from typing import Optional, Type, Set, List, Callable

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from django_cloudflare.purge import purge_model

logger = logging.getLogger(__name__)

# Registry of models to watch for cache purging
_registered_models: Set[Type] = set()
_model_url_funcs: dict = {}


def register_model(
    model: Type, get_url_func: Optional[Callable] = None, include_dependencies: bool = True
) -> None:
    """
    Register a model for automatic cache purging.

    When instances of this model are saved or deleted, the cache
    will be automatically purged for the instance's URL.

    Args:
        model: The Django model class to register.
        get_url_func: Optional function to get URL(s) for instances.
        include_dependencies: Whether to include dependent URLs in purge.

    Example:
        from django_cloudflare.signals import register_model
        from myapp.models import BlogPost

        register_model(BlogPost)
    """
    _registered_models.add(model)
    if get_url_func:
        _model_url_funcs[model] = {
            "get_url_func": get_url_func,
            "include_dependencies": include_dependencies,
        }
    else:
        _model_url_funcs[model] = {
            "get_url_func": None,
            "include_dependencies": include_dependencies,
        }

    # Connect signals
    post_save.connect(_on_model_save, sender=model)
    post_delete.connect(_on_model_delete, sender=model)

    logger.debug("Registered model %s for cache purging", model.__name__)


def unregister_model(model: Type) -> None:
    """
    Unregister a model from automatic cache purging.

    Args:
        model: The Django model class to unregister.
    """
    _registered_models.discard(model)
    _model_url_funcs.pop(model, None)

    post_save.disconnect(_on_model_save, sender=model)
    post_delete.disconnect(_on_model_delete, sender=model)

    logger.debug("Unregistered model %s from cache purging", model.__name__)


def _on_model_save(sender, instance, created: bool, **kwargs) -> None:
    """
    Signal handler for model save.

    Args:
        sender: The model class.
        instance: The model instance.
        created: Whether this is a new instance.
    """
    _purge_instance(instance, sender)


def _on_model_delete(sender, instance, **kwargs) -> None:
    """
    Signal handler for model delete.

    Args:
        sender: The model class.
        instance: The model instance being deleted.
    """
    _purge_instance(instance, sender)


def _purge_instance(instance, sender: Type) -> None:
    """
    Purge cache for a model instance.

    Args:
        instance: The model instance.
        sender: The model class.
    """
    config = _model_url_funcs.get(sender, {})
    get_url_func = config.get("get_url_func")
    include_dependencies = config.get("include_dependencies", True)

    try:
        purge_model(
            instance,
            include_dependencies=include_dependencies,
            get_url_func=get_url_func,
        )
        logger.info("Triggered cache purge for %s instance", sender.__name__)
    except Exception as e:
        logger.error("Failed to purge cache for %s: %s", instance, e)


def is_model_registered(model: Type) -> bool:
    """
    Check if a model is registered for cache purging.

    Args:
        model: The Django model class to check.

    Returns:
        True if the model is registered.
    """
    return model in _registered_models


def get_registered_models() -> List[Type]:
    """
    Get all registered models.

    Returns:
        List of registered model classes.
    """
    return list(_registered_models)
