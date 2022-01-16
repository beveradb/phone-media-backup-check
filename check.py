# Purpose of this script:
# Check through list of files in Android phone DCIM folder and cross-reference them all with files in my Dropbox
# "Camera Uploads" folder, matching up by date and exact filesize, to ensure all of data from my phone is backed up.
# The reason this is even a doubt is because the Dropbox "Camera Uploads" feature renames every file on upload...
#
# Files to check were generated like so:
# (plug in phone, enable USB debugging in settings -> developer tools)
# adb shell ls -An /sdcard/DCIM/Camera > phone-sdcard-dcim-camera-ls-$(date +%Y-%m-%d).txt
# ssh homelaptopremote ls -ltn --time-style=long-iso -Sr '/mnt/FAST8TB/Dropbox/Camera\ Uploads/' > dropbox-camera-uploads-ls-$(date +%Y-%m-%d).txt
#

dropbox_files = []
phone_files = []

