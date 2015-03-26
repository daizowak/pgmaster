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
    result=commands.getoutput("git checkout REL9_2_STABLE")
    return dict(test=result)
