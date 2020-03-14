#!/bin/sh

# setting cron for server

# 登録したいジョブ
cron_job_line="23 3 * * * python3 /home/sdkn104/AppEngine/yahooMailClean.py"

# crontabファイル
cron_file="/var/spool/cron/crontabs/root"

## crontabファイル準備

# 無ければ作る
[ -f ${cron_file} ] && touch ${cron_file}

## タスク登録

# 既に登録されているかどうかを判定
cron_job_line_for_grep="${cron_job_line}"
if [ `grep "${cron_job_line_for_grep}" "${cron_file}" | wc -l` -eq 0 ] ; then
  echo "not registered yet. begin registering..."
  echo "${cron_job_line}" >> "${cron_file}"
else
  echo "already registered."
fi

# cron再起動
service cron restart

echo "registering finished."

