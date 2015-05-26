# -*- coding: utf-8 -*-
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    )
import os
import commands
# import psycopg2
import datetime
# import custom model
import time
import fcntl

from sqlalchemy.exc import DBAPIError
from .models import (
    Base,
    DBSession,
    RelatedCommit,
    )


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return HTTPFound(location = request.route_url('front',pagename='front'))

@view_config(route_name='front',renderer='templates/front.pt')
def front(request):
    os.chdir("../master")
    check = "REL9_4_STABLE" #default branch
    if 'branch' in request.params:
        check = request.params['branch']

    # Select commit database limit 50
    tblname=str(check).lower()
    ormtype=type(tblname,(Base,),{'__tablename__':tblname,'__table_args__':{'autoload':True}})
    if 'date' in request.params:
        records=DBSession.query(ormtype).filter(ormtype.commitdate<=request.params['date']).order_by(ormtype.commitdate.desc(),ormtype.logid).limit(50).all()
    else:
        records= DBSession.query(ormtype).order_by(ormtype.commitdate.desc(),ormtype.logid).limit(50).all()
        
    return dict(myself=request.route_url('front'),check=check,records=records,detail=request.route_url('detail'))


@view_config(route_name='detail',renderer='templates/detail.pt')
def detail(request):
    os.chdir("../master")
    check = "REL9_2_STABLE"
    if 'branch' in request.params:
        check = request.params['branch']

    commitid=request.params['commitid']
    # open a lock file.
    fd = open("../lockfile","w")
    fcntl.flock(fd,fcntl.LOCK_EX)  #LOCK!

    commands.getoutput("git checkout " + check)
    description=commands.getoutput("git log --stat -1 " + commitid )
    diff=commands.getoutput("git log -p -1 --pretty=format: " + commitid )

    fcntl.flock(fd,fcntl.LOCK_UN)  #UNLOCK!
    fd.close()
    tblname=str(check).lower()
    ormtype=type(tblname,(Base,),{'__tablename__':tblname,'__table_args__':{'autoload':True}})

    if 'upload' in request.params or 'conupload' in request.params:

        buglevel=request.params['buglevel']
        seclevel=request.params['seclevel']
        snote=request.params['snote']
        note=request.params['note']
        revision=request.params['revision']
        releurl=request.params['releurl']
        repourl=request.params['repourl']
        genre=request.params['genre']
        analysys=request.params['analysys']
        

        # UPDATE
        DBSession.query(ormtype).filter(ormtype.commitid == commitid).update(
            {"buglevel":buglevel,
             "seclevel":seclevel,
             "snote":snote,
             "note":note,
             "revision":revision,
             "releurl":releurl,
             "reporturl":repourl,
             "genre":genre,
             "analysys":analysys,
             })
        DBSession.flush()


        if 'conupload' in request.params:
            # Search related information
            relatedids=DBSession.query(RelatedCommit).filter(RelatedCommit.src_commitid == commitid).all()
            for id in relatedids:
                dstrel=str(id.dst_relname).lower()
                dstreltype=type(dstrel,(Base,),{'__tablename__':dstrel,'__table_args__':{'autoload':True}})
                # UPDATE
                DBSession.query(dstreltype).filter(dstreltype.commitid == id.dst_commitid).update(
                    {"buglevel":buglevel,
                     "seclevel":seclevel,
                     "snote":snote,
                     "note":note,
                     "revision":revision,
                     "releurl":releurl,
                     "reporturl":repourl,
                     "genre":genre,
                     "analysys":analysys,
                 })
                DBSession.flush()                

    if 'relatedid' in request.params:
        for  subrelated in DBSession.query(RelatedCommit).filter(RelatedCommit.src_commitid == commitid).all():
            DBSession.add(RelatedCommit(subrelated.dst_commitid,request.params['relatedid'],request.params['relatedrel']))
            DBSession.add(RelatedCommit(request.params['relatedid'],subrelated.dst_commitid,subrelated.dst_relname))
        DBSession.add(RelatedCommit(commitid,request.params['relatedid'],request.params['relatedrel']))
        DBSession.add(RelatedCommit(request.params['relatedid'],commitid,check))
        DBSession.flush()

    try:
        # Search commit information.
        record = DBSession.query(ormtype).filter(ormtype.commitid == commitid).one()
        # Search related information.
        relatedids=DBSession.query(RelatedCommit).filter(RelatedCommit.src_commitid == commitid).all()
    except DBAPIError:
        return Response(conn_err_msg,content_type='text/plain',status_init=500)    
    return dict(myself=request.route_url('detail'),top=request.route_url('front'),detail=unicode(description,'utf-8','ignore'),diff=unicode(diff,'utf-8','ignore'),record=record,commitid=commitid,branch=check,relatedids=relatedids)


@view_config(route_name='log',renderer='templates/log.pt')
def log(request):
    os.chdir("../master")
    check = "REL9_2_STABLE"
    if 'branch' in request.params:
        check = request.params['branch']

    # Keyword Search
    word="Stamp"
    if 'keyword' in request.params:
        word = request.params['keyword']

    # open a lock file.
    fd = open("../lockfile","w")
    fcntl.flock(fd,fcntl.LOCK_EX)  #LOCK!
    commands.getoutput("git checkout " + check)
    result=commands.getoutput("git log --grep=\"" + word  + "\"")
    fcntl.flock(fd,fcntl.LOCK_UN)  #UNLOCK!
    fd.close()

    return dict(test=result.decode('utf-8'),myself=request.route_url('log'),check=check)


conn_err_msg="SQLAlchemy error occured..."
