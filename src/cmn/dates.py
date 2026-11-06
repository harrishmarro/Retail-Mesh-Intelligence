"""Explicit business-calendar and UTC conversion helpers for prepared sample data."""
from datetime import datetime,timezone
from math import ceil
from zoneinfo import ZoneInfo
BUSINESS_ZONE = ZoneInfo('America/Vancouver')
def parse_utc(value):
    stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
    if stamp.tzinfo is None:raise ValueError('Timestamp requires an explicit timezone')
    return stamp.astimezone(timezone.utc)
def utc_text(value):return value.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def business_date(value):return parse_utc(value).astimezone(BUSINESS_ZONE).date().isoformat()
def intended_local_to_utc(value):
    """Fixture correction assumption: old clock readings represent local business hours."""
    wall=datetime.fromisoformat(value.replace('Z','')).replace(tzinfo=BUSINESS_ZONE)
    return utc_text(wall)
def billable_days(start,end):
    seconds=(parse_utc(end)-parse_utc(start)).total_seconds()
    if seconds<=0:raise ValueError('Rental return must be after collection')
    return max(1,ceil(seconds/86400))
