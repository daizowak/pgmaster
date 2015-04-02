# -*- coding:utf-8 -*-

from sqlalchemy import (
    Column,
    Integer,
    Text,
    )
from sqlalchemy.ext.declarative import declarative_base
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

Base = declarative_base()
DBSession = scoped_session(sessionmaker(autocommit=True))
