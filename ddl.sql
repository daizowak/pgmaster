-- #-- uninstall each tables.
-- drop table _version cascade;
-- drop table relatedcommit;
create table if not exists _version
(
logid bigserial primary key  -- テーブル毎にユニークなプライマリキー
,commitid text unique         -- commitid (from git log)
,scommitid text unique          -- (short)commitid ( from git log)
,commitdate timestamptz              -- commitdate (from git log)
,updatetime timestamptz default now() -- 情報を更新した日付
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

CREATE OR REPLACE FUNCTION commit_insert_trigger_func() RETURNS TRIGGER AS
$$
    DECLARE
    tablename text;
    BEGIN
        -- キー値から計算
        tablename := 'REL'||replace(new.majorver,'.','_')||'_STABLE';
        -- newを渡す
        EXECUTE 'INSERT INTO ' || tablename || ' VALUES(($1).*)' USING new;
        RETURN NULL;
    END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER commit_insert_trigger
    BEFORE INSERT ON _version
    FOR EACH ROW EXECUTE PROCEDURE commit_insert_trigger_func();

create table if not exists RELATEDCOMMIT
(
src_commitid text
,dst_commitid text
,dst_relname text
,primary key(src_commitid, dst_commitid)
);

ALTER TABLE rel8_4_stable ADD CONSTRAINT vercheck CHECK (majorver='8.4');
ALTER TABLE rel9_0_stable ADD CONSTRAINT vercheck CHECK (majorver='9.0');
ALTER TABLE rel9_1_stable ADD CONSTRAINT vercheck CHECK (majorver='9.1');
ALTER TABLE rel9_2_stable ADD CONSTRAINT vercheck CHECK (majorver='9.2');
ALTER TABLE rel9_3_stable ADD CONSTRAINT vercheck CHECK (majorver='9.3');
ALTER TABLE rel9_4_stable ADD CONSTRAINT vercheck CHECK (majorver='9.4');
ALTER TABLE rel9_5_stable ADD CONSTRAINT vercheck CHECK (majorver='9.5');

CREATE OR REPLACE VIEW branchlist AS
 SELECT replace(replace(substring(upper(pg_class.relname::text) from 4),'_STABLE',''),'_','.') AS branch
   FROM pg_class
  WHERE (pg_class.oid IN ( SELECT pg_inherits.inhrelid
           FROM pg_inherits
          WHERE pg_inherits.inhparent = (( SELECT pg_class_1.oid
                   FROM pg_class pg_class_1
                  WHERE pg_class_1.relname = '_version'::name
                 LIMIT 1))))
  ORDER BY pg_class.relname DESC;

