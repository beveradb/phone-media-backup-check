# Purpose of this script:
# Check through list of files in Android phone DCIM folder and cross-reference them all with files in my Dropbox
# "Camera Uploads" folder, matching up by date and exact filesize, to ensure all of data from my phone is backed up.
# The reason this is even a doubt is because the Dropbox "Camera Uploads" feature renames every file on upload...
#
# Files to check were generated like so:
# (plug in phone, enable USB debugging in settings -> developer tools)
# adb shell ls -An /sdcard/DCIM/Camera > phone-sdcard-dcim-camera-ls-$(date +%Y-%m-%d).txt
# ssh homelaptopremote ls -ltn --time-style=long-iso -Sr '/mnt/FAST8TB/Dropbox/Camera\ Uploads/' > backup-camera-uploads-ls-$(date +%Y-%m-%d).txt
#
# These commands output a simple list of files using 'ls', both in the same format. Here's an example line:
# -rw-rw---- 1 0 9997    7673692 2020-12-17 13:01 IMG_20201217_140101.jpg

import json
import re
from datetime import datetime, timedelta

import humanize

def parse_file_to_dict(filename):
    files = {}
    list_file = open(filename)
    for line in list_file:
        groups = pattern.match(line)
        if groups is None:
            if line[0:5] == "total":
                continue
            else:
                print("No match found: " + line)
                exit(1)
        file_dict = groups.groupdict()
        files[file_dict['date'] + '.' + file_dict['filesize']] = file_dict

    return files

today_date_str = datetime.now().strftime("%Y-%m-%d")
phone_files_list_filename = "phone-sdcard-dcim-camera-ls-" + today_date_str + ".txt"
backup_files_list_filename = "backup-camera-uploads-ls-" + today_date_str + ".txt"
backup_filename_map_filename = "phone-media-orig-to-backup-filenames-map-" + today_date_str + ".json"

pattern = re.compile(
    "(?P<permissions>[^ ]+) (?P<ownership>[0-9]+ [0-9]+ [0-9]+) +"
    "(?P<filesize>[0-9]+) (?P<date>[0-9]+-[0-9]+-[0-9]+) (?P<time>[0-9]+:[0-9]+) (?P<filename>.+)")

backup_files = parse_file_to_dict(backup_files_list_filename)
phone_files = parse_file_to_dict(phone_files_list_filename)

files_counts = {
    "backed_up": 0,
    "backed_up_total_size": 0,
    "fuzzy_date_match": 0,
    "missing": 0,
}

backup_keys = backup_files.keys()
orig_to_backup_filenames_map = []
missing_filenames = []

for phone_key in phone_files:
    phone_file = phone_files[phone_key]
    file_found = False
    matching_key = phone_key

    if phone_key in backup_keys:
        file_found = True
    else:
        # Check the same filesize but with a date up to 2 days before or after the expected date
        # This is because the Dropbox Camera Uploads feature mangles the filename when it uploads the file,
        # e.g. setting the date to the uploaded date rather than trusting the original filename.
        phone_file_date_str = phone_file['date']
        phone_file_date_ojb = datetime.strptime(phone_file_date_str, "%Y-%m-%d").date()

        fuzzy_keys = (
            str(phone_file_date_ojb - timedelta(days=1)) + '.' + phone_file['filesize'],
            str(phone_file_date_ojb - timedelta(days=2)) + '.' + phone_file['filesize'],
            str(phone_file_date_ojb + timedelta(days=1)) + '.' + phone_file['filesize'],
            str(phone_file_date_ojb + timedelta(days=2)) + '.' + phone_file['filesize']
        )

        for fuzzy_key in fuzzy_keys:
            if fuzzy_key in backup_keys:
                file_found = True
                files_counts["fuzzy_date_match"] += 1
                matching_key = fuzzy_key

    if file_found:
        files_counts["backed_up"] += 1
        files_counts["backed_up_total_size"] += int(phone_file['filesize'])
        orig_to_backup_filenames_map.append({
            "original_filename": phone_file['filename'],
            "backup_filename": backup_files[matching_key]['filename'],
            "filesize": phone_file['filesize'],
        })
    else:
        files_counts["missing"] += 1
        missing_filenames.append(phone_file['filename'])
        print("Phone file not found in backup: " + str(phone_file))

# Write map or original filenames to backup filenames (along with filesize),
# so we can store this map file forever for later lookup in case we're struggling to find a specific file,
# or in case we want to try and rename the files back to their original filenames rather than keeping Dropbox's renames
orig_to_backup_filenames_map_file = open(backup_filename_map_filename, "w")
json.dump(orig_to_backup_filenames_map, orig_to_backup_filenames_map_file, indent=4)
orig_to_backup_filenames_map_file.close()

print(files_counts)

if files_counts["missing"] > 0:
    print("Missing files found. Make sure you've run the Dropbox app with wifi+power first!")
    print("Then, to move all missing files to backup dir for manual review, run: ")
    print("adb shell")
    print("mkdir -p /sdcard/DCIMCameraBackupReview")
    print("cd /sdcard/DCIM/Camera")
    print("mv " + " ".join(missing_filenames) + " /sdcard/DCIMCameraBackupReview/")
else:
    print("All " + str(files_counts["backed_up"]) + " files backed up. Original to backup filenames map JSON written!")
    print("To permanently delete " + humanize.naturalsize(
        files_counts["backed_up_total_size"]
    ) + " from phone, run: adb shell rm /sdcard/DCIM/Camera/*")
