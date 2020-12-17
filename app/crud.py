# Reusable functions for our data model

from datetime import datetime  # time, date, timedelta

from sqlalchemy.orm import Session
from databases import Database

from . import models, schemas


async def create_useinfo_entry(db: Database, log_entry: schemas.LogItemIncoming):
    new_log = dict(
        sid="current_user",
        event=log_entry.event,
        act=log_entry.act,
        div_id=log_entry.div_id,
        timestamp=datetime.utcnow(),
    )
    query = models.logitem.insert()
    await db.execute(query=query, values=new_log)
    return new_log
