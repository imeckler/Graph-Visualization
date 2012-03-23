import os.path, urllib2
from treeclasses import *
from BeautifulSoup import BeautifulSoup as BS

def clean_name_file(namefile, outpath):
    f = open(outpath, 'w')
    f.close()

    with open(outpath, 'a') as outfile:
        for line in namefile:
            spline = line.split('|')
            if 'scientific name' in spline[3]:
                outfile.write(' | '.join([s.strip() for s in spline[:2]]) + '\n')
    outfile.closed

def read_names(namefile):
    nodelist = [None for i in xrange(0,1158206)]

    for line in namefile:
        spline = line.split(' | ')
        id_num = int(spline[0])
        name   = spline[1].strip()
        try:
            nodelist[id_num] = Node(name)
        except IndexError:
            print id_num
    return nodelist

def read_nodes(nodefile, nodelist):
    for line in nodefile:
        spline = line.split('|')
        id_num = int(spline[0].strip())
        parnum = int(spline[1].strip())
        kind   = spline[2].strip()
        try:
            nodelist[parnum].children.append(nodelist[id_num])
        except IndexError:
            pass
        try:
            nodelist[id_num].parent = nodelist[parnum]
            nodelist[id_num].kind   = kind
        except IndexError:
            pass
    return nodelist

def lineage(node, acc=[]):
    if node.name == 'root':
        return acc
    else:
        return lineage(node.parent, acc + [node])

def node_by_name(name):
    global nodelist
    for node in nodelist:
        if node:
            if node.name == name:
                return node

def last_shared_group(name1, name2):
    lineage1 = lineage_by_name(name1)
    lineage2 = lineage_by_name(name2)
    if lineage1 and lineage2:
        for a1, a2 in zip(lineage1[::-1], lineage2[::-1]):
            if a1 == a2:
                mostrecent = a1
            else:
                break
    else:
        return None
    return mostrecent

def images_and_times(nodes):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    imgs  = []
    times = []
    for node in nodes:
        page_url = 'http://en.wikipedia.org/wiki/{0}'.format(capitalize(node.name.replace(' ','_')))
        soup     = BS(opener.open(page_url).read())

        img_tag  = soup.find('table', {'class':'infobox biota'}).find('img')
        img_tag['src']  = 'http:' + img_tag['src']

        time_rng = soup.find('table', {'class':'infobox biota'}).small.text
        time_rng = normalize('NFKD',time_rng).encode('ascii','ignore')

        imgs.append(img_tag)
        times.append(time_rng)
    return imgs, times

def nodes_to_html(nodes):
    imgs, times = images_and_times(nodes)
    img_cells   = ['<td>{0}</td>'.format(str(tag)) for tag in imgs]
    name_cells  = ['<td>{0}: {1}</td>'.format(capitalize(node.name), time) for node,time in zip(nodes,times)]
    return '<table border="1">\n<tr>' + '\n'.join(img_cells) + '</tr>\n<tr>' + '\n'.join(name_cells) + '</tr>\n</table>'

# the arguments are the paths (or in the case of clean_name_file_path,
# possibly the desired path) to names.dmp, nodes.dmp, and the clean 
# names file respectively
def generate_nodelist(name_file_path, node_file_path, clean_name_file_path)
    with open(node_file_path) as nodefile:
        if not os.path.exists(clean_name_file_path):
            with open(name_file_path) as dirty_file:
                clean_name_file(dirty_file, clean_name_file_path)

        with open (clean_name_file_path) as clean_file:
            nodelist = read_nodes(nodefile, read_names(clean_file))

if __name__ == "__main__":
    print "This module is not intended to be called directly."
