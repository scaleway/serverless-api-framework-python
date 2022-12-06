from .cron import CronTrigger

# Will be converted to an Union
# Note: a Union can't be created from a single type
Trigger = CronTrigger
