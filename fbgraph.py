import urllib, json, pygame
from treeclasses import *
from fdl import *
import cPickle

def update_graph_bh(bh_root, allnodes, edges, dt):
    update_forces_bh(bh_root, allnodes, edges)
    update_velocs(allnodes, dt)
    update_posns(allnodes, dt)

# draws the screen to reflect the current state of the graph
def update_screen_bh(screen, bh_root, allnodes, edges, width, height, dt):
    update_graph_bh(bh_root, allnodes, edges, dt)
    auto_scale(allnodes, width, height)
    draw_edges(screen, edges)
    for node in allnodes:
        pygame.draw.circle(screen, (255, 255, 255), (int(node.screen_pos.x), int(node.screen_pos.y)), 3)

# get all of the posts at the given open graph url
def scrape_posts(url, num_pages, acc=[]):
    if num_pages == 0:
        return acc
    else:
        page_dict = json.load(urllib.urlopen(url))
        posts     = page_dict['data']
        next_page = page_dict['paging']['next']
        acc.extend(posts)
        return scrape_posts(next_page, num_pages - 1, acc)

# generate a histogram of poster frequency
def freq_by_poster(posts):
    res = {}
    for post in posts:
        res[post['from']['name']] = res.get(post['from']['name'], 0) + 1
    return res

# scrape the id numbers of events at the given url, for the given number of pages
# for use in generating a graph
def scrape_event_ids(url, num_pages, acc):
    if num_pages == 0:
        return acc
    else:
        page_dict = json.load(urllib.urlopen(url))
        event_ids = [event['id'] for event in page_dict['data'] if event['rsvp_status'] == 'attending']
        next_page = page_dict['paging']['next']
        acc.extend(event_ids)
        return scrape_event_ids(next_page, num_pages - 1, acc)

# scrape the list of attendees for a given event url
def get_attendees(url, acc):
    page_dict = json.load(urllib.urlopen(url))
    attendees = page_dict['data']
    if attendees == []:
        return acc
    else:
        next_page = page_dict['paging']['next']
        acc.extend(attendees)
        return get_attendees(next_page, acc)

# scrape multiple events
def get_guestlists(event_ids, accesstok):
    res = []
    for event_id in event_ids:
        event_url = 'https://graph.facebook.com/{0}/attending?access_token={1}'.format(event_id, accesstok)
        res.append(get_attendees(event_url, []))
    return res

# for a list of event ids, create a dict of how often people go to the same events
def mutual_attendees(event_ids, accesstok):
    res = {}
    for guestlist in get_guestlists(event_ids, accesstok):
        for attendee in guestlist:
            res[attendee['name']] = res.get(attendee['name'], 0) + 1
    return res

# scrape the friends-list of the user with the given id number
def get_friends(id_num, access_token):
    url = 'https://graph.facebook.com/{0}/friends?access_token={1}'.format(id_num, access_token)
    return json.load(urllib.urlopen(url))['data']

# build a dictionary of Node objects from a list of friends for use in a graph
def friends_to_node_dict(friends):
    res = {}
    for friend in friends:
        friend_node = Node()
        id_num      = friend['id']
        friend_node.name = friend['name']
        friend_node.id   = id_num
        res[id_num] = friend_node
    return res

# returns a list of mutual friends for the given two id numbers
def mutual_friend_ids(my_id, friend_id, access_token):
    url     = 'https://graph.facebook.com/{0}/mutualfriends/{1}?access_token={2}'.format(my_id, friend_id, access_token)
    try:
        friends = json.load(urllib.urlopen(url))['data']
    except KeyError:
        print "Mutual friend scraping failed for IDs {0} and {1}. Try again.".format(my_id, friend_id)
    res = []
    for friend in friends:
        res.append(friend['id'])
    return res

# generate a list of edges, where each node is a friend of the user with the
# given id number, and each edge represents a friendship between two users
def friends_graph(my_id, access_token):
    friend_nodes = friends_to_node_dict(get_friends(my_id, access_token))
    edges = set()
    for id_num, friend_node in friend_nodes.iteritems():
        for mut_friend_id in mutual_friend_ids(my_id, id_num, access_token):
            edge = (a, b) = (friend_node, friend_nodes[mut_friend_id])
            if (b, a) not in edges:
                edges.add(edge)
    return friend_nodes, edges

# generates a mapping from names to the corresponding nodes
def name_to_node_dict(names):
    res = {}
    for name in names:
        if name not in res:
            res[name] = Node(name)
    return res

# generates a list of edges and a dictionary from names to nodes from 
# a list of lists of event attendees
def event_friend_graph(guestlists):
    edges = {}
    name_dict = name_to_node_dict([name for guestlist in guestlists for name in guestlist])
    for guestlist in guestlists:
        # this set of for-loops generates all unique pairs of
        # attendees for the current guestlist and updates the
        # number of events they have attended together
        for i, name1 in enumerate(guestlist):
            for name2 in guestlist[i + 1:]:
                node1 = name_dict[name1]
                node2 = name_dict[name2]
                try:
                    edges[(node1, node2)] += 1
                except KeyError:
                    try:
                        edges[(node2, node1)] += 1
                    except KeyError:
                        edges[(node1, node2)]  = 1
    return edges, name_dict

def update_guest_hookes(edges):
    for edge, k in edges.iteritems():
        dist_vect = edge[0].pos - edge[1].pos
        f = hooke(dist_vect, k, 60)
        edge[0].force += f
        edge[1].force -= f

def update_guest_forces(allnodes, edges):
    update_guest_hookes(edges)
    update_coulomb_forces(allnodes)

def update_guest_graph(allnodes, edges, dt):
    update_guest_forces(allnodes, edges)
    update_velocs(allnodes, dt)
    update_posns(allnodes, dt)

def update_guest_screen(screen, allnodes, edges, width, height):
    update_guest_graph(allnodes, edges, .01)
    auto_scale(allnodes, width, height)
    draw_edges(screen, edges)
    for node in allnodes:
        pygame.draw.circle(screen, (255, 255, 255), (int(node.screen_pos.x), int(node.screen_pos.y)), 10)

# saves the graph structure of your social network to a file
# to prevent having to re-scrape Facebook
def pickle_friend_graph(my_id, access_token, out_file_path):
    friend_nodes, edges = friends_graph(my_id, access_token)
    with open(out_file_path, 'w') as out_file:
        cPickle.dump((friend_nodes, edges), out_file)


def run_fb_simulation(width, height, dt, data_path, my_id, access_token, mode, out_directory):
    try:
        with open(data_path, 'r') as data_file:
            try:
                nodes, edges = cPickle.load(data_file)
            except:
                sys.exit("Bad data file")
    except IOError:
        print "Data file does not exist\nScraping Facebook..."
        nodes, edges = friends_graph(my_id, access_token)

    initialize(nodes, width, 100)
    screen = pygame.display.set_mode((int(width * 1.4), int(height * 1.4)))
    i = 0

    if mode == 'live':
        def update_image():
            pygame.display.update
        pygame.init()
    elif mode == 'save':
        def update_image():
            pygame.image.save(screen, '{0}/pic{1}.png'.format(out_directory, i))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.fill((0,0,0))
        bh_root = nodes_to_bh_tree(nodes)
        update_screen_bh(screen, bh_root, nodes, edges, width, height, dt)
        update_image()
        i += 1


if __name__ == "main":
    import sys
    try:
        try:
            run_fb_simulation(*sys.argv[1:9])
        except IndexError:
            run_fb_simulation(*sys.argv[1:8])
    except:
        print "Usage: [width] [height] [time step] [path to pickle file] [ID number] [access token]  ['save'|'live'] [output path for save mode]"
