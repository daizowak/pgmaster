# -*- coding:utf-8 -*-

from sqlalchemy import (
    Column,
    Integer,
    Text,
    )
from sqlalchemy.dialects.postgresql import DATE,TIMESTAMP,VARCHAR,BIGINT
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

class CommitTable(Base):
    __tablename__='_version'
    logid=Column('logid',Integer,primary_key=True)
    commitid=Column('commitid',Text)
    scommitid=Column('scommitid',Text)
    commitdate=Column('commitdate',TIMESTAMP)
    updatetime=Column('updatetime',TIMESTAMP)
    seclevel=Column('seclevel',Text)
    reporturl=Column('reporturl',Text)
    buglevel=Column('buglevel',Text)
    revision=Column('revision',Text)
    relememo=Column('relememo',Text)
    releurl=Column('releurl',Text)
    genre=Column('genre',Text)
    snote=Column('snote',Text)
    note=Column('note',Text)
    analysys=Column('analysys',Text)
    keyword=Column('keyword',Text)
    majorver=Column('majorver',Text)
