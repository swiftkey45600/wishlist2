from typing import Annotated

from pydantic import Field


SQLITE_MAX_INTEGER = 9223372036854775807
DatabaseId = Annotated[int, Field(gt=0, le=SQLITE_MAX_INTEGER)]
