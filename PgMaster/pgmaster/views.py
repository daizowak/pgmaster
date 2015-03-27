# -*- coding: utf-8 -*-
from pyramid.view import view_config
import os
import commands
# import psycopg2
import datetime


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'PgMaster'}


@view_config(route_name='test',renderer='templates/test.pt')
def test(request):
    os.chdir("../master")
    check = "REL9_2_STABLE"
    if '9.4' in request.params:
        check = request.params['9.4']
    if '9.3' in request.params:
        check = request.params['9.3']
    if '9.2' in request.params:
	check = request.params['9.2']
    if '9.1' in request.params:
        check = request.params['9.1']
    if '9.0' in request.params:
        check = request.params['9.0']
    if '8.4' in request.params:
        check = request.params['8.4']
    commands.getoutput("git checkout " + check)


    # Keyword Search
    if 'keyword' in request.params:
        keyword = request.params['keyword']
        if keyword is None:
            keyword="Stamp"

    result=commands.getoutput("git log --grep=\"" + keyword  + "\"")
    return dict(test=result.decode('utf-8'),myself=request.route_url('test'),check=check)
