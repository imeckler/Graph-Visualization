import pygame, sys
from treeclasses import *
from random import random, randint
from copy import deepcopy
from physics import hooke, coulomb

def net_bh_force(body, bh_root):
    force = Vector(0, 0)
    other_body = bh_root.body
    dist_vect  = body.pos - bh_root.com
    if other_body is body or dist_vect == Vector(0, 0):
        pass
    # if the other node is a leaf, calculate the force between the two bodies
    elif other_body:
        force += coulomb(dist_vect, 100, body.charge, other_body.charge)
    # otherwise we'll decide whether or not to approximate
    else:
        ratio = bh_root.halfwidth / dist_vect.length()
        if ratio < .25:
            force += coulomb(dist_vect, 100, body.charge, bh_root.charge)
        else:
            for child in bh_root.nodes.itervalues():
                force += net_bh_force(body, child)
    return force

def update_forces_bh(bh_root, allnodes, edges):
    for node in allnodes:
        node.force += net_bh_force(node, bh_root)
    update_hooke_forces(edges)


# update the hooke forces between each connected node in a graph
def update_hooke_forces(edges):
    for edge in edges:
        dist_vect = edge[0].pos - edge[1].pos
        f = hooke(dist_vect, 10, 60)
        edge[0].force += f
        edge[1].force -= f

# update the hooke forces between each connected node in a tree,
# increasing the force by level
def update_hooke_forces_tree(root, level):
    for child in root.children:
        dist_vect = child.pos - root.pos
        f = hooke(dist_vect, 10 * (level ** 2), 60.0/(2 *level))
        child.force += f
        root.force  -= f
        update_hooke_forces_tree(child, level + 1)


# calculate the net electrical force on a node
def net_coulomb(base, nodes):
    force = Vector(0,0)
    for node in nodes:
        dist_vect = base.pos - node.pos
        if dist_vect.length() == 0:
            force += Vector(100, 100)
        else:
            force += coulomb(dist_vect, 100, base.charge, node.charge)
    return force

# update the electrical forces for each node in a nodelist
def update_coulomb_forces(allnodes):
    for node in allnodes:
        if not node.fixed:
            node.force += net_coulomb(node, allnodes)

# update all the forces for each node in a graph
def update_forces(allnodes, edges, is_tree=False, root=None):
    update_coulomb_forces(allnodes)
    if is_tree:
        update_hooke_forces_tree(root, 1)
    else:
        update_hooke_forces(edges)

# update all the positions of each node in a graph
def update_posns(allnodes, dt):
    for node in allnodes:
        if not node.fixed:
            new_pos    = node.pos + (dt * node.velocity)
            node.pos   = Vector(int(round(new_pos.x)), int(round(new_pos.y)))
            node.force = Vector(0,0)

# update all the velocities of each node in a graph
def update_velocs(allnodes, dt):
    for node in allnodes:
        if not node.fixed:
            node.velocity += node.force * dt
            node.velocity *= .97

# evolve the state of a graph with time-step dt
def update_graph(allnodes, edges, dt, is_tree=False, root=None):
    update_forces(allnodes, edges, is_tree, root)
    update_velocs(allnodes, dt)
    update_posns(allnodes, dt)

# add force, velocity, charges, and random positions to nodes
def initialize(allnodes, width, charge):
    for node in allnodes:
        node.force    = Vector(0, 0)
        node.velocity = Vector(0, 0)
        node.pos      = Vector(randint(0, width), randint(0, width))
        node.charge   = charge
        node.fixed    = False


# sets the screen_pos attribute for each node, mapped by a 
# linear transformation selected to allow the whole graph
# to fit on the pygame surface

def map_graph(nodes, x_scale, y_scale, x_shift, y_shift):
    for node in nodes:
        if not node.fixed:
            node.screen_pos = Vector(node.pos.x * x_scale + x_shift, node.pos.y * y_scale + y_shift)
        else:
            node.pos = Vector((node.screen_pos.x - x_shift) / x_scale, (node.screen_pos.y - y_shift) / y_scale, )

# returns a copy of the input graph, with screen_pos attributes
# set to fit on the pygame surface
def auto_scale(allnodes, width, height):
    sorted_by_x = sorted([node.pos.x for node in allnodes])
    sorted_by_y = sorted([node.pos.y for node in allnodes])
    
    min_x = sorted_by_x[0]
    max_x = sorted_by_x[-1]
    min_y = sorted_by_y[0]
    max_y = sorted_by_y[-1]

    curr_width  = max_x - min_x
    curr_height = max_y - min_y

    x_scale = width / float(curr_width)
    y_scale = height / float(curr_height)

    min_x *= x_scale
    min_y *= y_scale

    x_shift = -min_x + 100
    y_shift = -min_y + 100

    map_graph(allnodes, x_scale, y_scale, x_shift, y_shift)

def draw_edges(screen, edges):
    for edge in edges:
        pygame.draw.line(screen, (0, 0, 255), tuple(edge[0].screen_pos), tuple(edge[1].screen_pos))

def draw_nodes(nodes, screen, radius):
    for node in nodes:
        pygame.draw.circle(screen, 
                           (255, 255, 255), 
                           (int(node.screen_pos.x), int(node.screen_pos.y)), 
                           radius)

# updates the screen for a  graph
def update_screen(screen, allnodes, edges, width, height, dt, is_tree=False, root=None):
    update_graph(allnodes, edges, dt, is_tree, root)
    auto_scale(allnodes, width, height)
    draw_edges(screen, edges)
    draw_nodes(allnodes, screen, 10)

# get the edges of a tree from its root
def get_clicked_node(nodes, mouse_pos):
    for node in nodes:
        point_rect = pygame.Rect(int(node.screen_pos.x - 5), int(node.screen_pos.y - 5), 20, 20)
        if point_rect.collidepoint(mouse_pos):
            return node

def run_simulation(nodes, edges, width, height, dt, is_tree=False, root=None):
    pygame.init()
    screen = pygame.display.set_mode((int(width * 1.4), int(height * 1.4)))
    clicked_node = None

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not clicked_node:
                    clicked_node = get_clicked_node(nodes, mouse_pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                if clicked_node:
                    clicked_node.fixed = False
                    clicked_node = None

        if clicked_node:
            clicked_node.fixed = True
            clicked_node.velocity = Vector(0, 0)
            clicked_node.force = Vector(0, 0)
            clicked_node.screen_pos = Vector(mouse_pos[0], mouse_pos[1])
       
        screen.fill((0,0,0))
        update_screen(screen, nodes, edges, width, height, dt, is_tree, root)
        pygame.display.update()
