#!/usr/bin/python

import time, json, os, requests, urllib, subprocess
from slackclient import SlackClient

#urllib3.disable_warnings()

def read_config(confname):
    with open(confname) as json_data_file:
        data = json.load(json_data_file)
    return (data)

def find_group_id(sc, name):
    groups = json.loads(sc.api_call("groups.list"))
    for grp in groups['groups']:
        if (grp['name'] == name):
            return (grp['id'])

def post_msg(msg):
    global config
    sc.server.channels.find(config['group']).send_message(str(msg))

def post_file(fname):
    global config
    r = requests.post('https://slack.com/api/files.upload', files={'file': open(fname, 'rb')}, params={'token': config['token2'], 'channels': config['gid'], 'filename': fname})
        
def msg_help(sc, msg):
    global msg_fct, msg_help
    c = msg_fct.keys()
    c.sort()
    res = "Commands:"
    for i in c:
        res = res + "\n"
        if (i in msg_help.keys()):
            res = res + msg_help[i]
        else:
            res = res + i
    post_msg(res)

def msg_load(sc, msg):
    print(os.getloadavg())
    post_msg(os.getloadavg())

def msg_snap(sc, msg):
    os.system("./imagesnap")
    post_file("snapshot.jpg")

def msg_free(sc, msg):
    proc = subprocess.Popen(["./free.sh"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    post_msg(out)

def msg_usage(sc, msg):
    r = requests.get("http://enroll.42.fr/usage.php")
    post_msg(r.content)

def msg_cam_do(cam):
    global config
    cam_name = cam + ".jpg"
    print("grab cam " + cam_name)
    urllib.urlretrieve(config['cam_base'] + cam_name, cam_name)
    print("post cam " + cam_name)
    post_file(cam_name)
    
def msg_cam(sc, msg):
    global config
    if (len(msg) == 1):
        k = config['cams'].keys()
        k.sort()
        res = "Cameras:"
        for i in k:
            res = res + "\n"
            res = res + "*" + i + "* : "
            cams = config['cams'][i]
            res = res + "_" + ",".join(cams) + "_"
        post_msg(res)
    else:
        if (len(config['cams']) > 0) and (msg[1] in config['cams'].keys()):
            for c in config['cams'][msg[1]]:
                msg_cam_do(c)
        else:
            msg_cam_do(msg[1])

def msg_balance(sc, msg):
    global config
    r = requests.get(config['bank_base'] + "balance.php?login=" + msg[1] + "&key=" + config['bank_key'])
    post_msg(r.content)

def msg_credit(sc, msg):
    global config
    r = requests.get(config['bank_base'] + "credit.php?login=" + msg[1] + "&amount=" + msg[2] + "&key=" + config['bank_key'])
    post_msg(r.content)

def msg_pay(sc, msg):
    global config
    r = requests.get(config['bank_base'] + "pay.php?login=" + msg[1] + "&amount=" + msg[2] + "&key=" + config['bank_key'])
    post_msg(r.content)

            
msg_fct = {
    'help':     msg_help,
    'load':     msg_load,
    'snap':     msg_snap,
    'free':     msg_free,
    'usage':    msg_usage,
    'cam':      msg_cam,
    'balance':  msg_balance,
    'credit':   msg_credit,
    'pay':      msg_pay
}

msg_help = {
    'cam': "*cam* [cam_name] _# without arg show cam list, with arg upload cam pic_",
    'load': "*load* _# show load of bot host_",
    'snap': "*snap* _# upload a snapshot from host cam_",
    'usage': "*usage* _# return number of people in the building_",
    'balance': "*balance* <login> _# show user foodtruck balance_",
    'credit': "*credit* <login> <amount> _# add amount to user foodtruck balance_",
    'pay': "*pay* <login> <amount> _# remove amount from user foodtruck balance_",
    'help': "*help* _# show this help_"
}

# {u'text': u'salut', u'ts': u'1437998018.000013', u'user': u'U03BC35LH', u'team': u'T03BDS0E2', u'type': u'message', u'channel': u'D086XDSTF'}
def rtm_message(sc, rtm):
    msg = rtm["text"].split(" ")
    if msg[0].lower() in msg_fct.keys():
        msg_fct[msg[0].lower()](sc, msg)
    
funcdict = {
    'message': rtm_message
}

config = read_config("config.json")
sc = SlackClient(config['token'])
config['gid'] = find_group_id(sc, config['group'])
print(config['gid'])

if sc.rtm_connect():
    while True:
        rtm = sc.rtm_read()
        try:
            if (len(rtm) > 0):
                for r in rtm:
                    if "type" in r:
                        if r["type"] in funcdict.keys():
                            funcdict[r["type"]](sc, r)
        except Exception:
            print("parse error: ")
            print(rtm)
            pass
        time.sleep(1)
else:
    print "Connection Failed, invalid token?"
