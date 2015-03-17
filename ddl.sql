drop table _version cascade;
create table _version
(
logid bigserial primary key,  -- テーブル毎にユニークなプライマリキー
commitid text unique,         -- commitid (from git log)
scommitid text unique,          -- (short)commitid ( from git log)
commitdate date,              -- commitdate (from git log)
updatetime timestamp default now(), -- 情報を更新した日付
seclevel text,  -- セキュリティレベル
reporturl text, -- バグ報告URL
buglevel text,  -- バグのレベル
revision text,  -- 当該コミットのリビジョン
relememo text,  -- 該当リリースノートのメモ
releurl text,   -- 該当リリースノートのURL
genre   text,   -- 当該コミットのジャンル
snote    text,   -- 当該コミットの日本語簡易メモ
note   text,     -- 当該コミットの日本語メモ
analysys    text,     -- 当該コミットの分析情報メモ
keyword   text      -- 検索タグ
);

create table REL8_4_STABLE(like _version including all) inherits(_version);
create table REL9_0_STABLE(like _version including all) inherits(_version);
create table REL9_1_STABLE(like _version including all) inherits(_version);
create table REL9_2_STABLE(like _version including all) inherits(_version);
create table REL9_3_STABLE(like _version including all) inherits(_version);
create table REL9_4_STABLE(like _version including all) inherits(_version);