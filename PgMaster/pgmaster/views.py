# -*- coding: utf-8 -*-
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    )
import os
import commands
import datetime
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

# トップページ
"""
frontページにアクセスするとこの処理が実行される。
トップページはデータベースからデフォルトの50件を取得して表示する。
もしパラメータに日付が指定されていたらその日付以前の50件のコミットを表示する。
コミット情報はバージョン毎にテーブルを用意している↓
rel8_4_stable
rel9_0_stable
rel9_1_stable
rel9_2_stable
rel9_3_stable
rel9_4_stable
ボタンを押したときに動的にそのテーブルが検索されるよう、
SQLAlchemyのormtypeインスタンスは、押下したボタン(バージョン)に
併せて対応するテーブルのインスタンスを都度作成することでこの処理を実現している。
"""
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

# コミット情報詳細ページ
"""
frontページから各コミット情報のリンクをクリックすると、
そのコミットIDを使用してこのページに飛ぶ。
ここでは、データベースに格納されたコミット情報に加えて、
コミットIDをキーにしてgit logした結果も併せて表示する。
そのために当該ブランチに都度checkoutを行っている。
しかしgitリポジトリは共有で使用しているために、
複数のユーザがこの操作を同時に行う可能性があるため、
git checkout->git logは、ロックファイルを用いて
排他処理を行うようにする。

"""
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

    # 更新ボタンが押された場合はこの処理が実行される
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


        # 関連コミットにも反映ボタンが押された場合は、関連コミットとして登録されているコミットIDにも
        # 同様の情報を更新する。
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

    # 関連コミットを登録ボタンが押されたら、登録するコミットIDとバージョンを登録する
    if 'relatedid' in request.params:
        for  subrelated in DBSession.query(RelatedCommit).filter(RelatedCommit.src_commitid == commitid).all():
            DBSession.add(RelatedCommit(subrelated.dst_commitid,request.params['relatedid'],request.params['relatedrel']))
            DBSession.add(RelatedCommit(request.params['relatedid'],subrelated.dst_commitid,subrelated.dst_relname))
        DBSession.add(RelatedCommit(commitid,request.params['relatedid'],request.params['relatedrel']))
        DBSession.add(RelatedCommit(request.params['relatedid'],commitid,check))
        DBSession.flush()

    # 引数として渡されたコミット情報を検索する。
    # コミット情報はutf-8で表示するが、decode関数を使うと、一部UnicodeDecodeErrorが
    # 発生していたので、現在はunicode関数に'ignore'オプションを使用してデコードすることで
    # この問題を回避している。
    try:
        # Search commit information.
        record = DBSession.query(ormtype).filter(ormtype.commitid == commitid).one()
        # Search related information.
        relatedids=DBSession.query(RelatedCommit).filter(RelatedCommit.src_commitid == commitid).all()
    except DBAPIError:
        return Response(conn_err_msg,content_type='text/plain',status_init=500)    
    return dict(myself=request.route_url('detail'),top=request.route_url('front'),detail=unicode(description,'utf-8','ignore'),diff=unicode(diff,'utf-8','ignore'),record=record,commitid=commitid,branch=check,relatedids=relatedids)

# git検索用ページ(コミットリポジトリとは独立して存在)
"""
デフォルトはStampをキーワードに抽出。
指定されたキーワードを入力した状態で検索したいバージョンのボタンを
クリックすることで、検索したいバージョンにチェックアウトし、
git logの検索を行っている。
"""
@view_config(route_name='log',renderer='templates/log.pt')
def log(request):
    os.chdir("../master")
    check = "REL9_4_STABLE"
    if 'branch' in request.params:
        check = request.params['branch']

    # Keyword Search
    word="Stamp"
    if 'keyword' in request.params:
        word = request.params['keyword']

    # open a lock file.
    # こちらも同じgitリポジトリを使用するので、
    # ロックファイルを使用した排他制御が必要。
    fd = open("../lockfile","w")
    fcntl.flock(fd,fcntl.LOCK_EX)  #LOCK!
    commands.getoutput("git checkout " + check)
    result=commands.getoutput("git log --grep=\"" + word  + "\"")
    fcntl.flock(fd,fcntl.LOCK_UN)  #UNLOCK!
    fd.close()

    return dict(test=result.decode('utf-8'),myself=request.route_url('log'),check=check)


conn_err_msg="SQLAlchemy error occured..."
