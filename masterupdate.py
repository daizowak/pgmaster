#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import commands
import psycopg2
import datetime

connstr = "dbname=pgmaster host=localhost user=postgres port=9999"

# mv postgres git repository.
os.chdir('master')
versions=commands.getoutput("git branch|cut -c3-|grep ^REL").split('\n') 
for version in versions:
    commands.getoutput("git checkout " + version)
    commands.getoutput("git pull")
    print "git pull done. branch :" + version 

# connect
conn = psycopg2.connect(connstr)
print "connect"

# main process
for version in versions:
    print "processing...." + version
    commands.getoutput("git checkout " + version)
    cur = conn.cursor()
    cur.execute("select max(commitdate) from " + version + " limit 1")
    since=cur.fetchone()
    conn.commit()
    cur.close()

    command="git log --date=short --no-merges --pretty=format:\"%H,%h,%ad\""
    if since is not None:
        command += " --since " + since[0].strftime('%Y-%m-%d')
        records=commands.getoutput(command).split('\n')
        for record in records:
            commitid= record.split(',')[0]
            scommitid= record.split(',')[1]
            commitdate= record.split(',')[2]
            cur = conn.cursor()
            try:
                cur.execute("insert into " + version + " (commitid,scommitid,commitdate) values ( %s,%s,%s) ",(commitid,scommitid,commitdate))
                print commitid + " has inserted."
            except psycopg2.Error as e:
                print "ERRCODE:" + e.pgcode + " MESSAGE:" + e.pgerror
                print "info: we will skip the record because it exists already. let's go next one."
                pass
            conn.commit()
            cur.close() 
    print "done."


print "all have done."