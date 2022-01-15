from datetime import datetime
from pydantic import BaseModel, validator
from dateutil.parser import isoparse

first_format = {
    "time": "2018-01-05 16:59:33+00:00",
}
# second_format = {'time': '2021-03-05T08:21:00.000Z',}
second_format = {
    "time": "2022-01-16T06:07:00.000Z",
}


class TimeModel(BaseModel):
    time: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @validator("time", pre=True)
    def time_validate(cls, v):
        # return datetime.fromisoformat(v)
        return isoparse(v)


print(TimeModel.parse_obj(first_format).json())
print("first_format successfull")
print(TimeModel.parse_obj(second_format))
print("second_format successfull")
x = TimeModel(time=first_format["time"])
print(x.time)
