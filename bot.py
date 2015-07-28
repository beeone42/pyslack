import time, json, os, requests, urllib
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
        post_msg("\n".join(k))
    else:
        if (len(config['cams']) > 0) and (msg[1] in config['cams'].keys()):
            for c in config['cams'][msg[1]]:
                msg_cam_do(c)
        else:
            msg_cam_do(msg[1])
        
msg_fct = {
    'help':  msg_help,
    'load':  msg_load,
    'snap':  msg_snap,
    'usage': msg_usage,
    'cam':   msg_cam
}

msg_help = {
    'cam': "cam [cam_name]"
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
        if (len(rtm) > 0):
            for r in rtm:
                if "type" in r:
                    if r["type"] in funcdict.keys():
                        funcdict[r["type"]](sc, r)
        time.sleep(1)
else:
    print "Connection Failed, invalid token?"
