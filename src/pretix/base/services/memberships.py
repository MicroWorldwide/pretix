from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from pretix.base.models import Item, OrderPosition, Customer, SubEvent, Event


def membership_validity(item: Item, subevent: SubEvent, event: Event):
    tz = event.timezone
    if item.grant_membership_duration_like_event:
        ev = subevent or event
        date_start = ev.date_from
        date_end = ev.date_to

        if not date_end:
            # Use end of day, if event end date is not set
            date_end = date_start.astimezone(tz).replace(hour=23, minute=59, second=59, microsecond=999999)

    else:
        # Always end at start of day
        date_start = now().astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start

        if item.grant_membership_duration_months:
            date_end -= timedelta(days=1)  # start on 25th gives end on 26th
            date_end += relativedelta(months=item.grant_membership_duration_months)  # start on 31th may give end on 28th

        if item.grant_membership_duration_days:
            date_end += timedelta(days=item.grant_membership_duration_days)

        # Always end at end of day
        date_end = date_end.astimezone(tz).replace(hour=23, minute=59, second=59, microsecond=999999)

    return date_start, date_end


def create_membership(customer: Customer, position: OrderPosition):
    item = position.item

    date_start, date_end = membership_validity(item, position.subevent, position.order.event)

    customer.memberships.create(
        membership_type=position.item.grant_membership_type,
        granted_in=position,
        date_start=date_start,
        date_end=date_end,
        attendee_name_parts=position.attendee_name_parts
    )
