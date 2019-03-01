#!/usr/bin/env python3

try:
    import sys
    import json
    import re
    import logging
    import argparse
except Exception as e:
    print(str(type(e).__name__) + ": " + str(e), file=sys.stderr)
    sys.exit(1)


def delete_temp_data_in_dict(dict):
    """
    Delete temporary key, value for all items in dictionary

    :param dict: input user dictionary, must be having 'temp_store' key
    :return: None
    """
    for key, value in dict.items():
        del value['temp_store']


def parse_passwd_add_uid_name(dict_users, set_users, passwd_filepath):
    """
    Parse passwd file, for each user_name as key, add uid, full_name, and also
    temp_store data
    :param dict_users: main dictionary storing user data
    :param set_users: set of all unique users
    :param passwd_filepath: file path of passwd file
    :return: None
    """
    with open(passwd_filepath) as f:

        for line in f:
            # foe each user entry, perform a weak validation by checking
            # against regex, and testing for duplicate user name.

            # from useradd man page at
            # https://linuxconfig.org/useradd-8-manual-page:
            # the only constraints are that usernames must neither start with a
            # dash (’-’) nor contain a colon (’:’) or a whitespace (space:’ ’,
            # end of line: ’\n’, tabulation: ’\t’, etc.).
            pattern = r'^([^-:\s].*:[^:]*:[0-9]*:[0-9]*:[^:]*:/[^:]*:/[^:]*)$'
            if re.match(pattern, line, flags=0) is None:
                raise AssertionError('passwd file malformed')

            passwd_line = line.split(':')

            user_name = passwd_line[0]

            # test for duplicate users
            if user_name in set_users:
                raise AssertionError("Duplicate user name '" + user_name +
                                     "' present")

            set_users.add(user_name)

            dict_users[user_name] = {}
            dict_users[user_name]['uid'] = passwd_line[2]
            dict_users[user_name]['full_name'] = passwd_line[4]

            # add 'temp_store' index to store temporary data;
            dict_users[user_name]['temp_store'] = {}
            dict_users[user_name]['temp_store']['primary_gid'] = passwd_line[3]
            dict_users[user_name]['temp_store']['is_primary_group_added'] = 0

            dict_users[user_name]['groups'] = []


def parse_group_add_groups(dict_users, dict_groups, set_users, group_filepath):
    """
    Add all supplementary groups for every user to dictionary 'dict_users',
    from examining members field in each group entry

    :param dict_users: main dictionary storing user data
    :param dict_groups: an empty dictionary to build group info; to be used
     later
    :param set_users: set of all unique users
    :param group_filepath: file path of group file
    :return: None
    """
    #raise AssertionError("parse group")

    set_gid = set()
    set_groupnames = set()

    with open(group_filepath) as f:

        for line in f:
            # foe each group entry, perform a weak validation by checking
            # against regex, and testing for duplicate group name

            # use same pattern for group name, as used for user name
            pattern = r'^([^-:\s].*:[^:]*:[0-9]*:([^-:\s].*,)*([^-:\s].*)*)$'

            if re.match(pattern, line, flags=0) is None:
                raise AssertionError('group file malformed.')

            group_line = line.split(':')

            group_name = group_line[0]
            gid = group_line[2]

            if group_name in set_groupnames:
                raise AssertionError("Duplicate group name '" + group_name +
                                     "' present")

            set_groupnames.add(group_name)

            if gid not in set_gid:
                dict_groups[gid] = dict()
                dict_groups[gid]['group_names'] = []
                set_gid.add(gid)

            dict_groups[gid]['group_names'].append(group_name)

            members_string = group_line[3].strip()

            # in case this group entry has no members listed, process
            # next group
            if not members_string:
                continue

            members_list = members_string.split(',')

            for member in members_list:
                # check if member exists in set
                if member not in set_users:
                    raise AssertionError("group member '" + member +
                                         "' not an existing user. "
                                         "Malformed passwd/group file")

                dict_users[member]['groups'].append(group_name)

                # record if this member user also has the same primary group,
                # so that, duplicate group entry is avoided when explicitly
                # adding primary group for each user
                if gid == dict_users[member]['temp_store']['primary_gid']:
                    dict_users[member]['temp_store']['is_primary_group_added']\
                        = 1


def setup_logging():
    """
    Using logging module, setup logging to file /var/log/passwdparser.log

    :return: None
    """
    try:

        logging.basicConfig(format="%(asctime)s [%(levelname)s] : %(message)s",
                            filename='/var/log/passwdparser.log',
                            level=logging.DEBUG)

    except PermissionError:

        print("Error: log file absent or not writable. To fix, execute these "
              "commands:\n"
              ">> sudo mkdir -p /var/log\n"
              ">> sudo touch /var/log/passwdparser.log\n"
              ">> sudo chown $USER /var/log/passwdparser.log"
              "  # OR, change ownernship appropriately to "
              " some other USER:GROUP",
              file=sys.stderr)

        # don't re-raise exception; terminate script with error status 1
        sys.exit(1)


def parse_cmdargs_get_passwd_group_filepath():
    """
    Using argparse module, get commandline arguments

    :return: set of three values - passwd filepath, group filepath, boolean
    flag to control adding primary group for each user
    """
    parser = argparse.ArgumentParser(description='Parse passwd, group file '
                                                 'and dump json object to '
                                                 'stdout.')
    parser.add_argument('-p', '--pwd_file', help='passwd filepath',
                        required=False)
    parser.add_argument('-g', '--grp_file', help='group filepath',
                        required=False)
    parser.add_argument('--include_primary_group', help='include primary'
                                                        ' group for each user',
                                                        action='store_true',
                                                        default=False,
                                                        required=False)
    args = parser.parse_args()

    # default to system path
    args.pwd_file = args.pwd_file or '/etc/passwd'
    args.grp_file = args.grp_file or '/etc/group'

    return args.pwd_file, args.grp_file, args.include_primary_group


def check_flag_add_primary_group(flag_include_primary_group, dict_users,
                                 dict_groups):
    """
    Check flag to add primary group

    :param flag_include_primary_group: boolean value to decide
    :param dict_users:
    :param dict_groups:
    :return:
    """
    if flag_include_primary_group is False:
        logging.info("Excluding primary group for each user")
        return

    logging.info("Adding primary group for each user")

    for key, value in dict_users.items():
        if value['temp_store']['is_primary_group_added'] == 1:
            for i, name in enumerate(value['groups']):
                if name in dict_groups[value['temp_store']['primary_gid']]['group_names']:
                    del (value['groups'][i])

        primary_gid = value['temp_store']['primary_gid']
        for group_name in dict_groups[primary_gid]['group_names']:
            value['groups'].append(group_name)


def is_linux_check():
    """
    Raise exception if non-Linux OS detected

    :return: None
    """
    if sys.platform == "linux" or sys.platform == "linux2":
        return
    else:
        raise AssertionError("Linux OS not detected.")


def parse_passwd_group_dump_json():
    """
    MAIN function: parse passwd, group file to create a dictionary object
    with the same structure as the desired json output, and dump it to
    stdout in json format.

    IMPORTANT: By default, for every user, only supplementary groups are
    added. To add primary group too, add argument --include_primary_group.
    To view usage, execute using '-h' option.

    :exception: All exceptions are caught using the general Exception class
    in this outermost function. The program doesn't try to recover when an
    exception occurs, they just bubble up to this function, where they are
    caught and the exception message and stack trace are logged to
    /vat/log/passwdparser.log

    :return: None
    """

    try:
        setup_logging()

        passwd_filepath, group_filepath, flag_include_primary_group = \
            parse_cmdargs_get_passwd_group_filepath()

        is_linux_check()

        # this dictionary will be converted to json, and should have the exact
        # same structure as needed for the json output
        dict_users = dict()

        # to store all unique usernames; will be used for validation
        set_users = set()

        # this dictionary is needed for accessing group names with gid as
        # key; to add primary group to user using the primary gid field
        dict_groups = dict()

        parse_passwd_add_uid_name(dict_users, set_users, passwd_filepath)

        parse_group_add_groups(dict_users, dict_groups, set_users,
                               group_filepath)

        check_flag_add_primary_group(flag_include_primary_group, dict_users,
                                     dict_groups)

        delete_temp_data_in_dict(dict_users)

        print(json.dumps(dict_users, indent=2, sort_keys=False))

    except Exception as e:
        logging.exception(str(type(e).__name__) + ": " + str(e), exc_info=True)
        sys.exit(1)  # return error status 1


if __name__ == '__main__':
    parse_passwd_group_dump_json()
