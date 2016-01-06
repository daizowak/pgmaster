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
    BranchList,
    CommitTable,
    )


# カスタム例外クラスの定義
class CustomExceptionContext(Exception):
    def __init__(self,msg):
        self.msg = msg

# カスタム例外ビューメソッドの定義
"""
CustomExceptionContext(message)がraiseされたらこのビューが
自動的に表示される。このビューは、messageを表示するだけ。
"""
@view_config(context=CustomExceptionContext, renderer='templates/error.pt')
def error(exception, request):
    request.response.status_code = 500
    return dict(exception=exception.msg)

@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return HTTPFound(location = request.route_url('front',pagename='front'))

# トップページ
"""
frontページにアクセスするとこの処理が実行される。
トップページはデータベースからデフォルトの50件を取得して表示する。
もしパラメータに日付が指定されていたらその日付以前の50件のコミットを表示する。
コミット情報はバージョン毎に以下のテーブルを用意している↓
rel8_4_stable
rel9_0_stable
rel9_1_stable
rel9_2_stable
rel9_3_stable
rel9_4_stable
rel9_5_stable
master
上記テーブルは全て_versionテーブルを親とした
パーティションテーブル構成になっている。
そのため、_versionテーブルに対してINSERT/UPDATE/DELETE/SELECTを
行うことで、各テーブルに対して処理が透過的に実施される。

**********************************************
以前までの実装ではボタンを押したときに動的にそのテーブルが検索されるよう、
押下したボタン(バージョン)に併せて対応するテーブルの
カスタムタイプインスタンスを都度作成することでこの処理を実現していた。
もうこの実現方法は必要ないのだが、メモとしてormtypeインスタンスの作成方法を
ここに残しておくことにする。

#ormtype=type("作成したいテーブル名",(Base,),{'__tablename__':"作成したいテーブル名",'__table_args__':{'autoload':True}})

こうすることによって、動的に作成したいテーブルのSQLAlchemyインスタンスタイプを作成できる。
**********************************************

"""
@view_config(route_name='front',renderer='templates/front.pt')
def front(request):

    #データベースに定義されたブランチテーブル一覧(view:branchlist)を取得し、
    #そのブランチリストをfrontページのタブとして表示させる
    branchlist=DBSession.query(BranchList).all()

    majorver = "9.4" #default branch
    if 'majorver' in request.params:
        majorver = request.params['majorver']

    #コミットIDフィルタ
    commitid=""
    if 'commitid' in request.params:
        commitid = request.params['commitid']

    #all検索チェックがついていたら全バージョンからコミットを検索
    isall="false"
    if 'all' in request.params:
        isall = request.params['all']

    #defalt offset is 0
    offset_num=0
    if 'offset' in request.params:
        offset_num = request.params['offset']

    # Select commit database limit 50
    if 'date' in request.params:
        records=DBSession.query(CommitTable).filter(CommitTable.majorver==majorver).filter(CommitTable.commitdate<=request.params['date']).order_by(CommitTable.commitdate.desc(),CommitTable.logid).limit(50).offset(offset_num).all()
    
    elif isall == "true":
        records= DBSession.query(CommitTable).order_by(CommitTable.commitdate.desc(),CommitTable.logid).filter(CommitTable.commitid.like(commitid + "%")).limit(50).offset(offset_num).all()
    else:
        records= DBSession.query(CommitTable).order_by(CommitTable.commitdate.desc(),CommitTable.logid).filter(CommitTable.majorver==majorver).filter(CommitTable.commitid.like(commitid + "%")).limit(50).offset(offset_num).all()

    
    return dict(myself=request.route_url('front'),branchlist=branchlist,majorver=majorver,records=records,detail=request.route_url('detail'))

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
    majorver = "9.4"
    if 'majorver' in request.params:
        majorver = request.params['majorver']

    # gitコマンド発行用
    if majorver == "master":
        check = majorver
    else:
        check = "REL" + majorver.replace('.','_') + "_STABLE" 

    commitid=request.params['commitid']
    # open a lock file.
    try:
        fd = open("../lockfile","w")
        fcntl.flock(fd,fcntl.LOCK_EX)  #LOCK!
        commands.getoutput("git checkout " + check)
        description=commands.getoutput("git log --stat -1 " + commitid )
        diff=commands.getoutput("git log -p -1 --pretty=format: " + commitid )
    finally:
        fcntl.flock(fd,fcntl.LOCK_UN)  #UNLOCK!
        fd.close()

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
        DBSession.query(CommitTable).filter(CommitTable.commitid == commitid).filter(CommitTable.majorver == majorver).update(
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
        # 同様の情報を更新する。ただし、同じバージョンのコミットIDレコードは更新対象外とする。
        # (この機能はあくまでバックパッチ目的)
        if 'conupload' in request.params:
            # Search related information
            relatedids=DBSession.query(RelatedCommit).filter(RelatedCommit.src_commitid == commitid).filter(RelatedCommit.dst_relname != majorver).all()
            for id in relatedids:
                # UPDATE
                DBSession.query(CommitTable).filter(CommitTable.commitid == id.dst_commitid).filter(CommitTable.majorver == id.dst_relname).update(
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
        # まずは入力されたバージョンテーブルに関連コミットがあるか検索
        # なければ登録しない
        targetver=str(request.params['relatedrel'])
        # 該当するコミットレコードが本当にあるかチェック
        try:
            nrows = DBSession.query(CommitTable).filter(CommitTable.majorver == targetver).filter(CommitTable.commitid == request.params['relatedid']).count()
            if nrows == 0:
                raise CustomExceptionContext('Your input commitid does not exist in specified PG-version.')
        except DBAPIError:
            raise CustomExceptionContext('Internal Error...')
        
        # 今回追加する関連コミット情報と、既に存在する関連コミットとの関連付けを行う。
        # ただし、追加する関連コミットのバージョンがこのページと同じバージョンであるか、
        # すでに登録されている関連コミットとこのページのバージョンが同じである場合は、
        # 当該関連コミットとの関連付けを行わない
        for  subrelated in DBSession.query(RelatedCommit).filter(RelatedCommit.src_commitid == commitid).all():
            if majorver == request.params['relatedrel'] or majorver == subrelated.dst_relname:
                continue
            #重複する可能性があるので、INSERT INTO ... CONFLICT IGNORE をAP側で実行する
            nrows = DBSession.query(RelatedCommit).filter(RelatedCommit.src_commitid == subrelated.dst_commitid).filter(RelatedCommit.dst_commitid == request.params['relatedid']).count()
            if nrows > 0: #すでに登録済みなので、登録はスキップ
                continue
            DBSession.add(RelatedCommit(subrelated.dst_commitid,request.params['relatedid'],request.params['relatedrel']))
            DBSession.add(RelatedCommit(request.params['relatedid'],subrelated.dst_commitid,subrelated.dst_relname))
        # 今回登録する関連コミットと当該ページのコミット情報の関連付けを行う。
        DBSession.add(RelatedCommit(commitid,request.params['relatedid'],request.params['relatedrel']))
        DBSession.add(RelatedCommit(request.params['relatedid'],commitid,majorver))
        DBSession.flush()

    # 引数として渡されたコミット情報を検索する。
    # コミット情報はutf-8で表示するが、decode関数を使うと、一部UnicodeDecodeErrorが
    # 発生していたので、現在はunicode関数に'ignore'オプションを使用してデコードすることで
    # この問題を回避している。
    try:
        # Search commit information.
        record = DBSession.query(CommitTable).filter(CommitTable.majorver == majorver).filter(CommitTable.commitid == commitid).one()
        # Search related information.
        relatedids=DBSession.query(RelatedCommit).filter(RelatedCommit.src_commitid == commitid).all()
    except DBAPIError:
        raise CustomExceptionContext('Internal Error...(Failed search of specified commitid information)')
    return dict(myself=request.route_url('detail'),top=request.route_url('front'),detail=unicode(description,'utf-8','ignore'),diff=unicode(diff,'utf-8','ignore'),record=record,commitid=commitid,majorver=majorver,relatedids=relatedids)

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
    # ファイルディスクリプタのクローズはfinallyブロックで行う。
    try:
        fd = open("../lockfile","w")
        fcntl.flock(fd,fcntl.LOCK_EX)  #LOCK!
        commands.getoutput("git checkout " + check)
        result=commands.getoutput("git log --grep=\"" + word.encode('utf-8')  + "\"")
    finally:
        fcntl.flock(fd,fcntl.LOCK_UN)  #UNLOCK!
        fd.close()

    return dict(test=unicode(result,'utf-8','ignore'),myself=request.route_url('log'),check=check)
