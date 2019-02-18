#!/usr/bin/env python3

import pprint, json

class PasswordParser():
    def parsePasswdGroups(self):

        passwd_filepath = '/etc/passwd'
        group_filepath = '/etc/group'

        pp = pprint.PrettyPrinter(indent=4)

        # validation



        dict1 = dict()

        with open(passwd_filepath) as f:
            for line in f:
                user_line = line.split(':')
                # print(user_line)
                dict1[user_line[0]]={}
                dict1[user_line[0]]['uid'] = user_line[2]
                dict1[user_line[0]]['user_desc'] = user_line[4]
    
                dict1[user_line[0]]['temp_store'] = {}
                dict1[user_line[0]]['temp_store']['primary_gid'] = user_line[3]
                dict1[user_line[0]]['temp_store']['is_primary_group_added'] = 0

                dict1[user_line[0]]['groups'] = []

        # pp.pprint(dict1)


        dict2 = dict()

        with open(group_filepath) as f:
            for line in f:
                group_line = line.split(':')
                print(type(group_line[2]))

                dict2[group_line[2]] = {}
                dict2[group_line[2]]['name'] = group_line[0]

                members_string = group_line[3]
                members_string_stripped = members_string.strip()

                if not members_string_stripped:
                    continue

                members_list = members_string_stripped.split(',')
                print(members_list)
                # print(len(members_list[0]))

                for member in members_list:
                    # print("member: "+member)
                    dict1[member]['groups'].append(group_line[0])

                    if group_line[2] == dict1[member]['temp_store']['primary_gid']:
                        dict1[member]['temp_store']['is_primary_group_added'] = 1

        # pp.pprint(dict1)
        print(json.dumps(dict1, indent=2, sort_keys=True))

        if True:
            for key, value in dict1.items():
                if value['temp_store']['is_primary_group_added'] == 0:
                    value['groups'].append(dict2[value['temp_store']['primary_gid']]['name'])


        # print(json.dumps(dict1, indent=2, sort_keys=True))

        for key,value in dict1.items():
            del value['temp_store']

        print(json.dumps(dict1, indent=2, sort_keys=True))

p = PasswordParser()
p.parsePasswdGroups()