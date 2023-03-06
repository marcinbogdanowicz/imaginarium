from celery import shared_task
from api.models import TempLink, TempLinkTokenBlacklist
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)

@shared_task
def remove_expired_templink_tokens():
    """
    Periodically scans the db and removes expired temporary link tokens.
    """
    removed = 0
    for templink in TempLink.objects.all():
        if templink.has_expired():
            token = templink.token
            TempLinkTokenBlacklist.objects.create(token=token)
            templink.delete()
            removed += 1

    logger.info(f'Removed {removed} expired temp links.')
