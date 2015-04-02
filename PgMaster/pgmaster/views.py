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

from sqlalchemy.exc import DBAPIError
from .models import (
    Base,
    DBSession,
    )

@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return HTTPFound(location = request.route_url('front',pagename='front'))

@view_config(route_name='front',renderer='templates/front.pt')
def front(request):
    os.chdir("../master")
    check = "REL9_2_STABLE" #default branch
    if 'branch' in request.params:
        check = request.params['branch']
    commands.getoutput("git checkout " + check)

    # Select commit database limit 50
    tblname=str(check).lower()
    ormtype=type(tblname,(Base,),{'__tablename__':tblname,'__table_args__':{'autoload':True}})
    records= DBSession.query(ormtype).order_by(ormtype.commitdate.desc(),ormtype.logid).limit(50).all()

    return dict(myself=request.route_url('front'),check=check,records=records,detail=request.route_url('detail'))


@view_config(route_name='detail',renderer='templates/detail.pt')
def detail(request):
    os.chdir("../master")
    check = "REL9_2_STABLE"
    if 'branch' in request.params:
        check = request.params['branch']
    commands.getoutput("git checkout " + check)

    commitid=request.params['commitid']
    result=commands.getoutput("git log -c -n 1 " + commitid )
    tblname=str(check).lower()
    ormtype=type(tblname,(Base,),{'__tablename__':tblname,'__table_args__':{'autoload':True}})

    if 'upload' in request.params:

        buglevel=request.params['buglevel']
        seclevel=request.params['seclevel']
        snote=request.params['snote']
        note=request.params['note']
        revision=request.params['revision']
        releurl=request.params['releurl']
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
             "genre":genre,
             "analysys":analysys,
             })
        DBSession.flush()

    try:
        # Search commit information.
        record= DBSession.query(ormtype).filter(ormtype.commitid == commitid).one()
    except DBAPIError:
        return Response(conn_err_msg,content_type='text/plain',status_init=500)
    
    return dict(myself=request.route_url('detail'),detail=result.decode('utf-8'),record=record,commitid=commitid,branch=check)


@view_config(route_name='log',renderer='templates/log.pt')
def log(request):
    os.chdir("../master")
    check = "REL9_2_STABLE"
    if 'branch' in request.params:
        check = request.params['branch']
    commands.getoutput("git checkout " + check)

    # Keyword Search
    word="Stamp"
    if 'keyword' in request.params:
        word = request.params['keyword']

    result=commands.getoutput("git log --grep=\"" + word  + "\"")
    return dict(test=result.decode('utf-8'),myself=request.route_url('log'),check=check)


conn_err_msg="SQLAlchemy error occured..."
