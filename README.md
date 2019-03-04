# passwd / group file parser
### *Parse ```passwd``` & ```group``` files on a linux system, prepare json object and dump to stdout*

#### Script behavior:
- By default, only supplementary groups are added for each user. This behavior can be overridden by adding switch ```--include_primary_group```, in which case primary group too, will be added. ***Note, that in this case, if a group is both a primary as well as a secondary group for a user, duplication for the group entry will be avoided.*** See [link](https://ubuntuforums.org/showthread.php?t=1688174) for explanation on primary / supplementary groups
- A weak validation for each line in ```passwd``` & ```group``` files, is performed using regex matching - *doesn't check for malformed password entries*
- Other validations are performed: username & group name must be unique
#### Steps:
- Download script ```passwdgroup_parser.py``` on a linux system
- Make it executable ```chmod +x passwdgroup_parser.py```
- manual steps to enable logging:
```
  - sudo mkdir -p /var/log
  - sudo touch /var/log/passwdparser.log
  - sudo chown $USER /var/log/passwdparser.log # OR, change ownership appropriately to 
                                               # some other USER:GROUP
```
  - Execute manually: ```./passwdgroup_parser.py```, or add to crontab script; output will be dumped to *stdout*
#### CLI arguments (*All are optional*):
  - display help: ```-h, --help```
  - specify custom passwd file path: ```-p PWD_FILE, --pwd_file PWD_FILE```
  - specify custom group file path: ```-g GRP_FILE, --grp_file GRP_FILE```
  - include primary groups too, for each user: ```--include_primary_group```

#### Logging:
- Logs will be stored in ```/var/log/passwdparser.log```
