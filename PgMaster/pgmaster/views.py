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
    DBSession,
    PatchRecord
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

    Object1=PatchRecord

    try:
        # Select commit database limit 50
        records=DBSession.execute("select commitid,scommitid,seclevel,snote,commitdate from " + check + " order by logid desc limit 50").fetchall()
    except DBAPIError:
        return Response(conn_err_msg,content_type='text/plain', status_int=500)

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

    if 'upload' in request.params:
        # UPDATE 
        seclevel=request.params['seclevel']
        snote=request.params['snote']
        note=request.params['note']
        DBSession.execute("update " + check + " set " + 
                          " seclevel = '" + seclevel + "'," +
                          " snote = '"    + snote    + "'," +
                          " note = '"     + note     + "'"  +
                          " where commitid='" + commitid +"';")

    try:
        # Search commit information.
        records=DBSession.execute("select seclevel,snote,note from " + check + " where commitid='" + commitid + "'").fetchall()
    except DBAPIError:
        return Response(conn_err_msg,content_type='text/plain',status_init=500)
    
    global record
    for row in records:
        record=row

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
