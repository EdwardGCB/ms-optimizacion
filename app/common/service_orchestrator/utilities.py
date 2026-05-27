from importlib import import_module
from app.worker.core.utilitites import get_attr


def absolute_component_factory_module(module_path: str):
    return import_module(f"{module_path}.service")


def enqueue_task(task_name, **kwargs):
    task = get_attr('config.celery', task_name)
    task.delay(**kwargs)
