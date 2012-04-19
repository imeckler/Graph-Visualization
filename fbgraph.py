from treeclasses import *
from fdl import *
import cPickle
import threading
import Queue
import urllib2
import json
import pygame

# based on an implementation from 
# http://www.artfulcode.net/articles/multi-threading-python/
# A class to facilitate multithreaded downloading of web pages
class URLThread(threading.Thread):
    """A class to download web pages in parallel threads"""
    def __init__(self, url, label):
        self.url = url
        self.label = label
        self.result = None
        threading.Thread.__init__(self)
    def run(self):
        try:
            page = urllib2.urlopen(self.url)
            contents = page.read()
            page.close()
            self.result = contents
        except IOError:
            print "Could not open url: {0}".format(self.url)


# A function to download a dictionary of labels to urls in 
# multiple threads, returning a dictionary that maps from the
# same labels to the contents of those urls
def download_urls(url_dict, max_threads):
    def producer(q, url_dict):
        for label, url in url_dict.iteritems():
            thread = URLThread(url, label)
            thread.start()
            q.put(thread, True)

    finished = {}

    def consumer(q, total_files):
        while len(finished) < total_files:
            thread = q.get(True)
            thread.join()
            # Having results equal to None will cause a lot of trouble
            # when we use this for the purpose of scraping mutual friend
            # relationships
            if thread.result:
                finished[thread.label] = thread.result

    q = Queue.Queue(max_threads)

    prod_thread = threading.Thread(target=producer, args=(q, url_dict))
    cons_thread = threading.Thread(target=consumer, args=(q, len(url_dict)))
    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()
    return finished

# An interface for the Open-Graph of the user with the given id_number
class Facebook(object):
    def __init__(self, id_number, access_token):
        self.id = id_number
        self.access_token = access_token

    # return the friends list of the user as a list of dictionaries
    def get_friends(self):
        url  = ('https://graph.facebook.com/{0}/friends?access_token={1}'
                .format(self.id, self.access_token))
        page = urllib2.urlopen(url)
        friends = json.load(page)['data']
        # memoize the result as an attribute
        self.friends = friends
        return friends

    # returns a list of the user's mutual friends with the user with
    # the given id number, friend_id
    def mutual_friends(self, friend_id):
        url = ('https://graph.facebook.com/{0}/'
               'mutualfriends/{1}?access_token={2}'
               .format(self.id, friend_id, self.access_token))
        try:
            mut_friends = json.load(urllib2.urlopen(url))['data']
        except IOError:
            print ("Mutual friend scraping failed for IDs {0} and {1}."
                   .format(self.id, friend_id))
            return None

        return mut_friends

    def all_mutual_friend_lists(self):
        try:
            friends = self.friends
        except AttributeError:
            friends = self.get_friends()

        # build a dictionary that maps from a friend's id number to
        # the url of the list of the user's mutual friends with them
        url_dict = {}
        for friend in friends:
            url_dict[friend['id']] = ('https://graph.facebook.com/{0}/'
                                      'mutualfriends/{1}?access_token={2}'
                                      .format(self.id, friend['id'], 
                                              self.access_token))

        mut_friend_dict = download_urls(url_dict, 3)

        for k, v in mut_friend_dict.iteritems():
            try:
                mut_friend_dict[k] = json.loads(v)['data']
            except TypeError:
                pass

        # memoize the dictionary as an attribute
        self.mutual_friend_dict = mut_friend_dict
        return mut_friend_dict


    # generate a list of edges, where each node is a friend of the user,
    # and each edge represents a friendship between two users
    def friends_graph(self):
        # build a dictionary of Node objects from a list of friends for
        # use in the graph
        def friends_to_node_dict(friends):
            res = {}
            for friend in friends:
                friend_node = Node()
                id_num = friend['id']
                friend_node.name = friend['name']
                friend_node.id = id_num
                res[id_num] = friend_node
            return res

        try:
            friends = self.friends
        except AttributeError:
            friends = self.get_friends()

        friend_nodes = friends_to_node_dict(friends)
        edges = set()

        try:
            mutual_friend_dict = self.mutual_friend_dict
        except AttributeError:
            mutual_friend_dict = self.all_mutual_friend_lists()

        for id_num, friend_node in friend_nodes.iteritems():
            mut_friend_id_list = [f['id'] for f in mutual_friend_dict[id_num]]

            for mut_friend_id in mut_friend_id_list:
                edge = (a, b) = (friend_node, friend_nodes[mut_friend_id])
                if (b, a) not in edges:
                    edges.add(edge)

        graph = friend_nodes, edges
        # memoize
        self.graph = graph
        return graph

    # saves the graph structure of your social network to a file
    # to prevent having to re-scrape Facebook
    def pickle_friend_graph(self, out_file_path):
        try:
            graph = self.graph
        except AttributeError:
            graph = self.friends_graph()
        with open(out_file_path, 'w') as out_file:
            cPickle.dump(graph, out_file)

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


def run_fb_simulation(facebook, mode, width, height, dt, out_directory):
    try:
        nodes, edges = facebook.graph
    except AttributeError:
        nodes, edges = facebook.friends_graph()

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
        id_num, access_token, width, height, dt, mode = sys.argv[1:7]
        try:
            outpath = sys.argv[7]
        except ValueError:
            outpath = None

        facebook = Facebook(id_num, access_token)
        run_fb_simulation(facebook, mode, width, height, dt, outpath)
    except:
        print "Usage: [ID number] [access token] [width] [height] [time step] ['save'|'live'] [output path for save mode]"
