"""
Service for handling user health metrics (KPI) persistence and retrieval.
"""
from typing import Any, Dict, List

from lib.models.metrics import Metric, MetricSet

# In-memory store for demonstration (replace with DB integration as needed)
_user_metrics_store: Dict[str, List[MetricSet]] = {}

def save_user_metric_set(user_id: str, date: str, metrics: List[Dict[str, Any]]) -> None:
    """
    Save a metric set for a user for a given date.
    :param user_id: The user's ID
    :param date: The date for the metric set (ISO string)
    :param metrics: List of metric dicts
    """
    metric_objs = [Metric(**m) for m in metrics]
    metric_set = MetricSet(user_id=user_id, date=date, metrics=metric_objs)
    if user_id not in _user_metrics_store:
        _user_metrics_store[user_id] = []
    _user_metrics_store[user_id].append(metric_set)


def get_user_metric_sets(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all metric sets for a user.
    :param user_id: The user's ID
    :return: List of metric set dicts
    """
    sets = _user_metrics_store.get(user_id, [])
    return [ms.to_dict() for ms in sets] 