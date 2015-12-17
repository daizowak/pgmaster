-- #-- uninstall each tables.
-- drop table _version cascade;
-- drop table relatedcommit;
create table if not exists _version
(
logid bigserial primary key  -- テーブル毎にユニークなプライマリキー
,commitid text unique         -- commitid (from git log)
,scommitid text unique          -- (short)commitid ( from git log)
,commitdate timestamptz              -- commitdate (from git log)
,updatetime timestamp default now() -- 情報を更新した日付
,seclevel text  -- セキュリティレベル
,reporturl text -- バグ報告URL
,buglevel text  -- バグのレベル
,revision text  -- 当該コミットのリビジョン
,relememo text  -- 該当リリースノートのメモ
,releurl text   -- 該当リリースノートのURL
,genre   text   -- 当該コミットのジャンル
,snote    text   -- 当該コミットの日本語簡易メモ
,note   text     -- 当該コミットの日本語メモ
,analysys    text     -- 当該コミットの分析情報メモ
,keyword   text      -- 検索タグ
,majorver   text   -- 当該コミットの対象メジャーバージョン 
);

create table if not exists REL8_4_STABLE(like _version including all) inherits(_version);
create table if not exists REL9_0_STABLE(like _version including all) inherits(_version);
create table if not exists REL9_1_STABLE(like _version including all) inherits(_version);
create table if not exists REL9_2_STABLE(like _version including all) inherits(_version);
create table if not exists REL9_3_STABLE(like _version including all) inherits(_version);
create table if not exists REL9_4_STABLE(like _version including all) inherits(_version);
create table if not exists REL9_5_STABLE(like _version including all) inherits(_version);

create table if not exists RELATEDCOMMIT
(
src_commitid text
,dst_commitid text
,dst_relname text
,primary key(src_commitid, dst_commitid)
);

CREATE OR REPLACE VIEW branchlist AS 
    SELECT upper(relname) AS branch 
    FROM pg_class 
    WHERE oid 
    IN (
        SELECT inhrelid FROM pg_inherits WHERE inhparent=(SELECT oid FROM pg_class WHERE relname='_version' limit 1)
        ) 
    ORDER BY relname DESC;

