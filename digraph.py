from collections import ChainMap
from xml.dom.minidom import parse

gene_ids = ['MSU_ID', 'RAP_ID', 'funricegene_ID', 'Gramene_ID']
id_mapping = {}


class DiGraph:

    def __init__(self):
        self._nodes = {}
        self._edges = {}

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges

    def check_node_from_id(self, nid):
        if nid in self.nodes:
            return nid
        return -1

    def check_node_from_data(self, check_data: dict):
        if check_data['_type'] == 'Gene':
            for nid, data in self.nodes.items():
                if data['_type'] == 'Gene':
                    for gene_id in gene_ids:
                        if gene_id in check_data.keys() and gene_id in data.keys() and \
                                check_data[gene_id] == data[gene_id]:
                            return nid
        for nid, data in self.nodes.items():
            if check_data == data:
                return nid
        return -1

    def add_node(self, add_id, add_data: dict = None, method: str = 'id'):
        if add_data is None:
            add_data = {}
        if method == 'id':
            nid = self.check_node_from_id(add_id)
        elif method == 'data':
            nid = self.check_node_from_data(add_data)
        else:
            raise ValueError('Invalid method name {}'.format(method))
        if nid == -1:
            self.nodes[add_id] = add_data
            nid = add_id
        else:
            self.nodes[nid].update(add_data)
        return nid

    def add_edge(self, node1_id, node2_id, **edge_data):
        node1_id = self.add_node(node1_id)
        node2_id = self.add_node(node2_id)
        try:
            if node2_id in self.edges[node1_id]:
                self.edges[node1_id].update({node2_id: edge_data})
            else:
                self.edges[node1_id][node2_id] = edge_data
        except KeyError:
            self.edges[node1_id] = {node2_id: edge_data}

    def read_ttl(self, ttl_file: str):
        with open(ttl_file, 'r') as ttl:
            for line in ttl.readlines():
                line = line.strip()
                if line:
                    line = line.split(' ', 2)
                    line[2] = line[2][:-2]

                    if line[2][0] == '_':
                        # read edges
                        source = line[0]
                        target = line[2]
                        relationship = line[1].split('#')[1][:-1]
                        self.add_edge(source, target, relationship=relationship)

                    else:
                        # read nodes
                        rdf_id = line[0]
                        if line[2][0] == '<':
                            entity_type = line[2].split('#')[1][:-1]
                            self.add_node(rdf_id)
                            self.nodes[rdf_id]['_type'] = entity_type
                        else:
                            data_type = line[1].split('#')[1][:-1]
                            data = line[2][1:-1]
                            self.add_node(rdf_id)
                            self.nodes[rdf_id][data_type] = data

    def read_path(self, path_file: str):
        with open(path_file, 'r') as path:
            for line in path.readlines():
                line = line.strip()
                if line[0] == '#':
                    continue
                else:
                    self.read_ttl(line)

    def read_owl(self, path: str):
        xml = parse(path)
        root = xml.documentElement

        for i in root.getElementsByTagName('owl:Class'):
            try:
                go_accession = i.getAttribute('rdf:about').split('/')[4]
                go_name = None
                obo_namespace = None

                for child in i.childNodes:
                    if child.nodeName == 'rdfs:label':
                        go_name = child.firstChild.data
                    elif child.nodeName == 'oboInOwl:hasOBONamespace':
                        obo_namespace = child.firstChild.data
                self.add_node(go_accession, {'go_name': go_name, 'obo_namespace': obo_namespace})

                subclass_nodes = i.getElementsByTagName('rdfs:subClassOf')
                if subclass_nodes:
                    for node in subclass_nodes:
                        to_go_accession = node.getAttribute('rdf:resource').split('/')[4]
                        if to_go_accession:
                            self.add_edge(go_accession, to_go_accession, relationship='SubclassOf')
            except IndexError:
                pass

    def merge_ttl(self, ttl):
        mapping = {}
        node_id = 0

        for oid, data in ttl.nodes.items():
            nid = self.add_node(node_id, data, 'data')
            mapping[oid] = nid
            if nid == node_id:
                node_id += 1

        for source, target_and_data in ttl.edges.items():
            for target, data in target_and_data.items():
                self.add_edge(mapping[source], mapping[target], **data)

    def annotate_on_instances(self, public_onto):
        node_id = len(self.nodes)
        associated_data_list = ['go_accession']
        associated_data = ''
        mapping = {}  # onto_accession: id_in_graph

        # for i in associated_data_list:
        #     if i in list(public_onto.nodes.values()):
        #         print(i)
        #         associated_data = i
        associated_data = 'go_accession'
        if not associated_data:
            return

        for accession, data in public_onto.nodes.items():
            self.add_node(node_id, dict(ChainMap({associated_data: accession, '_type': 'PublicOnto'},
                                                 public_onto.nodes[accession])))
            mapping[accession] = node_id
            node_id += 1

        for nid, data in self.nodes.items():
            if associated_data in data.keys():
                try:
                    self.add_edge(nid, mapping[data[associated_data]], relationship='PublicOntoMapping')
                except KeyError:
                    pass

    def print_graph(self):
        print('Nodes:')
        for i, nid in enumerate(self.nodes):
            print('Node', i, ':', nid, self.nodes[nid])
        print('Edges:')
        for i, source in enumerate(self.edges):
            print('Edge', i, ':', source, '->', self.edges[source])

    def output_to_csv(self,
                      node_path: str = 'output\\output_all_csv_node.csv',
                      edge_path: str = 'output\\output_all_csv_edge.csv',
                      contains_data: bool = True):
        node_csv = open(node_path, 'w')
        edge_csv = open(edge_path, 'w')

        node_csv.write('Id,Label,Polygon\n')
        edge_csv.write('Source,Target,Type,Label,Weight\n')

        for nid, data in self.nodes.items():
            node_csv.write('{},"{}",{}\n'.format(nid, data['_type'], 0))
        for source, target_and_data in self.edges.items():
            for target, data in target_and_data.items():
                edge_csv.write('{},{},{},{},{}\n'.format(source, target, 'Directed', data['relationship'], 1))

        if contains_data:
            node_num = len(self.nodes)
            for nid, data in self.nodes.items():
                for k, v in data.items():
                    if k == '_type':
                        continue
                    node_csv.write('{},"{}",{}\n'.format(node_num, v, 3))
                    edge_csv.write('{},{},{},{},{}\n'.format(nid, node_num, 'Undirected', k, 1))
                    node_num += 1

        node_csv.close()
        edge_csv.close()


if __name__ == '__main__':
    o = DiGraph()
    o.read_path('example\\path.txt')
    g = DiGraph()
    g.merge_ttl(o)

    # onto = DiGraph()
    # onto.read_owl('D:\\Downloads\\lab\\rdf_merge\\data\\go.owl')
    # g.annotate_on_instances(onto)

    # g.output_to_csv('output\\output_all_csv_node_go.csv', 'output\\output_all_csv_edge_go.csv')
    g.print_graph()
