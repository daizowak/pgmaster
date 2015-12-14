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

class RelatedCommit(Base):
    __tablename__='relatedcommit'
    src_commitid=Column('src_commitid',Text,primary_key=True)
    dst_commitid=Column('dst_commitid',Text,primary_key=True)
    dst_relname=Column('dst_relname',Text)

    def __init__(self,src,dst,relname):
        self.src_commitid=src
        self.dst_commitid=dst
        self.dst_relname=relname

class BranchList(Base):
    __tablename__='branchlist'
    branch=Column('branch',Text,primary_key=True)

    def __init__(self,branch):
        self.branch=branch
