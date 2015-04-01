# -*- coding:utf-8 -*-

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

Base = declarative_base()
DBSession = scoped_session(sessionmaker(autocommit=True))

#[TODO] ORM is not using yet...because I don't know how to use.
class PatchRecord:
    __tablename__ = '_rel9_0_stable'

    commitid=sa.Column(sa.Unicode(255),unique=True)
    scommitid=sa.Column(sa.Unicode(255),unique=True)

    def __init__(self,commitid):
        self.commitid=commitid


