#!/usr/bin/env python

import argparse
import os
import glob
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone

parser = argparse.ArgumentParser()
parser.add_argument(
    "-b",
    "--backupfolder",
    default="/var/lib/unifi/backup/autobackup",
    help='the folder containing backups to manage (default "/var/lib/unifi/backup/autobackup")',
)
parser.add_argument(
    "-m",
    "--monthstokeep",
    type=int,
    default=1,
    help="the number of months to keep of weekly backups (default 1, set to 0 for infinite)",
)
parser.add_argument(
    "-w",
    "--weekstokeep",
    type=int,
    default=1,
    help="the number of weeks to keep of daily backups (default 1, set to 0 for infinite)",
)
parser.add_argument(
    "-y",
    "--yearstokeep",
    type=int,
    default=0,
    help="the number of years to keep of monthly backups (default 0, which is infinite)",
)
parser.add_argument(
    "-t",
    "--timezone",
    default="Europe/London",
    help='the timezone to use when processing backups (default "Europe/London")',
)
args = parser.parse_args()

timezone_to_use = timezone(args.timezone)

unf_files_in_path = glob.glob(os.path.join(args.backupfolder, "*.unf"))
meta_json_files_in_path = glob.glob(os.path.join(args.backupfolder, "*meta.json"))
meta_json_files_in_path.sort(key=os.path.getmtime)
meta_json_file = meta_json_files_in_path[-1]

with open(meta_json_file) as meta_json:
    meta = json.load(meta_json)

meta = {
    backup_file_name: backup_file_data
    for backup_file_name, backup_file_data in meta.items()
    if os.path.isfile(os.path.join(args.backupfolder, backup_file_name))
}

files_to_delete = [
    backup_file_name for backup_file_name in unf_files_in_path if os.path.basename(backup_file_name) not in meta
]

for backup_file in files_to_delete:
    os.remove(backup_file)

unf_files_in_path = glob.glob(os.path.join(args.backupfolder, "*.unf"))

unf_files_in_path.sort(key=os.path.getmtime)
earliest_backup_datetime = datetime.fromtimestamp(os.path.getmtime(unf_files_in_path[0]), tz=timezone_to_use)
now_datetime = datetime.now(tz=timezone_to_use)
now_lastmidnight = datetime.combine(now_datetime.date(), datetime.min.time(), now_datetime.tzinfo)
dates_to_keep = []

current_date = now_lastmidnight

while current_date >= earliest_backup_datetime - relativedelta(days=1) and (
    current_date >= now_lastmidnight - relativedelta(weeks=args.weekstokeep) or args.weekstokeep == 0
):
    dates_to_keep.append(current_date)
    current_date = current_date - relativedelta(days=1)

current_date = now_lastmidnight

while current_date >= earliest_backup_datetime - relativedelta(weeks=1) and (
    current_date >= now_lastmidnight - relativedelta(months=args.monthstokeep) or args.monthstokeep == 0
):
    if current_date.day >= 1 and current_date.day <= 7:
        current_date = current_date.replace(day=1)
    if current_date.day >= 8 and current_date.day <= 14:
        current_date = current_date.replace(day=8)
    if current_date.day >= 15 and current_date.day <= 21:
        current_date = current_date.replace(day=15)
    if current_date.day >= 22 and current_date.day <= 28:
        current_date = current_date.replace(day=22)
    if current_date.day >= 29:
        current_date = current_date.replace(day=29)
    dates_to_keep.append(current_date)
    current_date = current_date - relativedelta(weeks=1)

current_date = now_lastmidnight

while current_date >= earliest_backup_datetime - relativedelta(months=1) and (
    current_date >= now_lastmidnight - relativedelta(years=args.yearstokeep) or args.yearstokeep == 0
):
    dates_to_keep.append(current_date.replace(day=1))
    current_date = current_date - relativedelta(months=1)

dates_to_keep = list(set(dates_to_keep))

new_meta = {}

dates_to_keep.sort()

for date_to_keep in dates_to_keep:
    for days_to_check in range(1, 31):
        files_on_date = {
            backup_file_name: backup_file_data
            for backup_file_name, backup_file_data in meta.items()
            if datetime.fromtimestamp(backup_file_data["time"] / 1000, tz=timezone_to_use) > date_to_keep
            and datetime.fromtimestamp(backup_file_data["time"] / 1000, tz=timezone_to_use)
            < date_to_keep + relativedelta(days=days_to_check)
        }
        if len(files_on_date) > 0:
            break
    if len(files_on_date) > 1:
        earliest_file_name = [os.path.join(args.backupfolder, file_name) for file_name in files_on_date].sort(
            key=os.path.getmtime
        )[0]
        files_on_date = {
            backup_file_name: backup_file_data
            for backup_file_name, backup_file_data in files_on_date.items()
            if backup_file_name == earliest_file_name
        }
    new_meta.update(files_on_date)

files_to_delete = [
    backup_file_name for backup_file_name in unf_files_in_path if os.path.basename(backup_file_name) not in new_meta
]

for backup_file in files_to_delete:
    print("Deleting file: " + backup_file)
    os.remove(backup_file)

print("Writing new meta.json")
print(json.dumps(new_meta, ensure_ascii=False, indent=4))

with open(meta_json_file, "w", encoding="utf-8") as meta_json:
    json.dump(new_meta, meta_json, ensure_ascii=False, indent=4)
