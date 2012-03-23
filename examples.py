from fdl import *

usage = 'Enter desired window side-length followed by "bin" (binary tree) or "com" (complete graph) followed by a positive integer.'
advice = "Try clicking and dragging the vertices of the graph."
max_dim = 500

if len(sys.argv) == 1:
	print usage

# an example for a tree
elif sys.argv[1] == 'bin':
    n_root = binary_tree(int(sys.argv[2]))
    edges = get_edges(n_root)
    alln = all_nodes(n_root)
    initialize(alln, max_dim, 300)
    
    print advice
    run_simulation(alln, edges, 500, 500, .01, True, n_root)

# an example for a general graph
elif sys.argv[1] == 'com':
    g_nodes, g_edges = complete_graph(int(sys.argv[2]))
    initialize(g_nodes, max_dim, 300)

    print advice
    run_simulation(g_nodes, g_edges, 500, 500, .01)

else:
	print usage