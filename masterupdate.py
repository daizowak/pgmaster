#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import commands
import psycopg2
import datetime
import fcntl

connstr = "dbname=pgmaster host=localhost user=postgres port=9999"

# mv postgres git repository.
os.chdir('master')

# open a lock file.
fd = open("../lockfile","w")
fcntl.flock(fd,fcntl.LOCK_EX)  #LOCK!

versions=commands.getoutput("git branch|cut -c3-|grep ^REL").split('\n') 
for version in versions:
    commands.getoutput("git checkout " + version)
    commands.getoutput("git pull")
    print "LOG: git pull done. branch :" + version 

# connect
conn = psycopg2.connect(connstr)
print "LOG: connect"

# main process
for version in versions:
    print "LOG: processing...." + version
    commands.getoutput("git checkout " + version)
    cur = conn.cursor()
    cur.execute("select (max(commitdate) - interval '1 days')::date from " + version + " limit 1")
    since=cur.fetchone()
    conn.commit()
    cur.close()

    command="git log --date=short --no-merges --pretty=format:\"%H,%h,%ci\""
    if since is not None:
        majorver=version[3:].replace('_STABLE','').replace('_','.')  #メジャーバージョンの取得
        command += " --since " + since[0].strftime('%Y-%m-%d')
        records=commands.getoutput(command).split('\n')
        for record in records:
            commitid= record.split(',')[0]
            scommitid= record.split(',')[1]
            commitdate= record.split(',')[2]
            cur = conn.cursor()
            try:
                cur.execute("insert into " + version + " (commitid,scommitid,commitdate,majorver) values ( %s,%s,%s,%s) ",(commitid,scommitid,commitdate,majorver))
                print commitid + " has inserted."
            except psycopg2.Error as e:
                print "LOG:" + e.pgerror + "errorcode:"
                print "INFO: we will skip the record because it exists already. let's read next one."
                pass
            conn.commit()
            cur.close() 
    print "INFO: done."

fcntl.flock(fd,fcntl.LOCK_UN)  #UNLOCK!
fd.close()
print "LOG: all have done."
