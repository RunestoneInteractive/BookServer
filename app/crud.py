# Reusable functions for our data model

from datetime import datetime  # time, date, timedelta

from sqlalchemy.orm import Session

from . import models, schemas


def create_useinfo_entry(db: Session, log_entry: schemas.LogItemIncoming):
    new_log = models.LogItem(
        sid="current_user",
        event=log_entry.event,
        act=log_entry.act,
        div_id=log_entry.div_id,
        timestamp=datetime.utcnow(),
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log
