#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import commands
import psycopg2
import datetime
import fcntl

# 指定した日付にコミットされたコミットログのみをデータベースに格納する
since = sys.argv[1]

print since

connstr = "dbname=pgmaster host=localhost user=postgres password=postgres port=9999"

# mv postgres git repository.
os.chdir('master')

# open a lock file.
fd = open("../lockfile","w")
fcntl.flock(fd,fcntl.LOCK_EX)  #LOCK!

versions=commands.getoutput("git branch|cut -c3-|grep -e ^REL -e ^master").split('\n') 
#for version in versions:
#    commands.getoutput("git checkout " + version)
#    commands.getoutput("git pull")
#    print "LOG: git pull done. branch :" + version 

# connect
conn = psycopg2.connect(connstr)
print "LOG: connect"

# main process
for version in versions:
    print "LOG: processing...." + version
    res = commands.getstatusoutput("git checkout " + version)
    print res[1]
    if res[0] != 0:
        print "ERROR: command failed => git checkout" + version
        continue
    command="git log --date=short --no-merges --pretty=format:\"%H,%h,%ci\""
    if since is not None:
        if version == "master":
            majorver=version
        else:
            majorver=version[3:].replace('_STABLE','').replace('_','.')  #メジャーバージョンの取得
        command += " --since=\"" + since + "\" --until=`date -d \"" + since + " 1 day\" +%Y-%m-%d`"
        records=commands.getoutput(command).split('\n')
        if records[0] == '':
            print 'LOG: no record.'
            continue
        for record in records:
            commitid= record.split(',')[0]
            scommitid= record.split(',')[1]
            commitdate= record.split(',')[2]
            cur = conn.cursor()
            try:
                #パーティショントリガによりそれぞれのテーブルに振り分けられる
                cur.execute("insert into _version (commitid,scommitid,commitdate,majorver) values ( %s,%s,%s,%s) ",(commitid,scommitid,commitdate,majorver))
                print commitid + " has inserted."
            except psycopg2.Error as e:
                print "LOG:" + e.pgerror + " ERRORCODE:" + e.pgcode
                print "INFO: we will skip the record because it exists already. let's read next one."
                pass
            conn.commit()
            cur.close() 
    print "INFO: done."

fcntl.flock(fd,fcntl.LOCK_UN)  #UNLOCK!
fd.close()
print "LOG: all have done."
