from unicodedata import normalize

# A minimal Node class used in constructing graphs
class Node(object):
    def __init__(self, name="", kind="", children=None, parent=None):
        self.name   = name
        self.kind   = kind
        self.parent = parent
        if children:
            self.children = children
        else:
            self.children = []

    def __repr__(self):
        return 'Node("{0}", "{1}")'.format(to_ascii(self.name), self.kind)

# vector class used for force, position, and velocity. Pretty self explanatory
class Vector(object):
    def __init__(self, x, y):
        self.x, self.y = x, y
    def length(self):
        return ((self.x ** 2) + (self.y ** 2)) ** (.5)
    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)
    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)
    def __div__(self, scalar):
        return Vector(self.x / scalar, self.y / scalar)
    def __iter__(self):
        yield self.x
        yield self.y
    def __eq__(self, other):
        return (self.x == other.x) and (self.y == other.y)
    def dot(self, other):
        return Vector(self.x * other.x, self.y * other.y)
    def norm(self):
        return self.dot(self) ** .5
    def normed(self):
        l = self.length()
        try:
            return Vector(self.x / l, self.y / l)
        except ZeroDivisionError:
            return Vector(0,0)
    def __repr__(self):
        return "({0}, {1})".format(self.x, self.y)
    __rmul__ = __mul__

# Barnes-Hutt tree class for approximating the n-body problem
class BHTree:
    def __init__(self, body=None, mid_x=None, mid_y=None, halfwidth=None):
        self.nodes = {}
        self.body  = body
        self.mid_x, self.mid_y = mid_x, mid_y
        self.halfwidth = halfwidth
        if body:
            self.com    = Vector(body.pos.x, body.pos.y)
            self.charge = body.charge
    # updates a node's center of mass and total charge
    def update_charge(self, new_charge, new_x, new_y):
        tot_charge = self.charge + new_charge
        self.com.x = (self.charge * self.com.x + new_charge * new_x)/float(tot_charge)
        self.com.y = (self.charge * self.com.y + new_charge * new_y)/float(tot_charge)
        self.charge = tot_charge

    # insert a body into the tree
    def insert(self, body):
        def new_midpt(currpt, new_hwidth, dir_ness):
            if dir_ness:
                return currpt + new_hwidth
            else:
                return currpt - new_hwidth

        northness = body.pos.y > self.mid_y
        eastness  = body.pos.x > self.mid_x
        quadrant  = (eastness, northness)

        # if the current node of the tree does not have a body, insert it here
        if self.body:
            old_body  = self.body
            self.body = None
            self.charge = 0
            self.insert(old_body)
            self.insert(body)

        # if there is no node at the quadrant where this body should go,
        # create a new tree there and place the body in it
        elif quadrant not in self.nodes: 
            new_hwidth = self.halfwidth/2.0
            new_mid_x  = new_midpt(self.mid_x, new_hwidth, eastness)
            new_mid_y  = new_midpt(self.mid_y, new_hwidth, northness)
            self.nodes[quadrant] = BHTree(body, new_mid_x, new_mid_y, new_hwidth)
            self.update_charge(body.charge, body.pos.x, body.pos.y)

        # otherwise recursively insert the body into the proper quadrant's
        # tree
        else:
            self.nodes[quadrant].insert(body)
            self.update_charge(body.charge, body.pos.x, body.pos.y)


# simply inserts all the nodes in a nodelist into a BHTree
def nodes_to_bh_tree(nodes):
    root = BHTree(nodes[0], 500, 500, 500)
    for node in nodes[1:]:
        root.insert(node)
    return root

# return a tree, trimmed after a certain level
def pruned(root, level):
    new_root = Node()
    new_root.name = root.name
    new_root.kind = root.kind
    new_root.children = []

    if level == 0:
        return new_root
    else:
        for child in root.children:
            new_root.children.append(pruned(child, level - 1))
        return new_root

# return the leaves of a root
def leaves(root):
    res = []
    for child in root.children:
        if child.children == []:
            res.append(child)
        else:
            res.extend(leaves(child))
    return res

# return all the nodes in a tree
def all_nodes(root):
    res = [root]
    for child in root.children:
        res.extend(all_nodes(child))
    return res


# converts a unicode string to an ascii approximation
def to_ascii(u):
    try:
        return normalize('NFKD',u).encode('ascii','ignore')
    except TypeError:
        return u

def get_edges(root):
    edges = []
    for child in root.children:
        edges.append((root, child))
        edges.extend(get_edges(child))
    return edges

def binary_tree(level):
    if level == 0:
        res = Node()
        res.children = []
        return res
    else:
        res = Node()
        res.children = [binary_tree(level - 1), binary_tree(level - 1)]
        return res

# generate a complete graph of degree n (i.e., a graph in which each
# node has an edge with each other node)
def complete_graph(n):
    nodes = [Node() for x in xrange(0, n)]
    edges = [(nodes[i], nodes[j]) for i in xrange(0,n) for j in xrange(i + 1, n)]
    return nodes, edges
