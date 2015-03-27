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
    check = None
    if '9.2' in request.params:
	check = request.params['9.2']
    if '9.1' in request.params:
        check = request.params['9.1']
    result=commands.getoutput("git checkout REL9_2_STABLE")
    return dict(test=result,myself=request.route_url('test'),check=check)
