from collections import ChainMap
from xml.dom.minidom import parse
import re

property_path = "PathProperty.properties"
gene_seq_check = False  # 未完成的功能，勿设置为True


class Properties:
    def __init__(self, file_name):
        self.properties = dict()
        self.read_properties(file_name)

    def read_properties(self, file_name):
        try:
            pro_file = open(file_name, 'r', encoding='utf-8')
            for line in pro_file:
                line = line.strip()
                if line:
                    strs = re.split(r"\s=\s", line)
                    self.properties[strs[0]] = strs[1]
        except Exception as e:
            raise e
        else:
            pro_file.close()

    def get_property(self, param):
        return self.properties[param]

    def read_list(self, param):
        res = list()
        with open(self.properties[param], "r") as file:
            for line in file.readlines():
                line = line.strip()
                if line:
                    res.append(line)
        return res

    def read_dict(self, param):
        res = dict()
        with open(self.properties[param], "r") as file:
            for line in file.readlines():
                line = line.strip()
                if line:
                    strs = line.split("\t")
                    res[strs[0]] = strs[1]
        return res


class DiGraph:
    def __init__(self):
        self._nodes = {}
        self._edges = {}
        self._data_properties = []
        self._gene_seq = []
        self._not_gene_seq = []

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges

    @property
    def data_properties(self):
        return self._data_properties

    @property
    def gene_seq(self):
        return self._gene_seq

    @property
    def not_gene_seq(self):
        return self._not_gene_seq

    def check_node_from_id(self, nid):
        """
        通过结点的ID判断是否存在该点
        :param nid: 结点ID
        :return: 若找到结点，则返回结点ID，否则返回-1
        """
        if nid in self.nodes:
            return nid
        return -1

    def check_node_from_data(self, check_data: dict):
        """
        通过结点的数据属性判断是否存在该点（有ID对应关系的会合并，数据属性完全一致的会合并）
        :param check_data: 欲检查的数据属性
        :return: 若找到结点，则返回结点ID，否则返回-1
        """
        if check_data['_type'] == 'Gene':
            for nid, data in self.nodes.items():
                if data['_type'] == 'Gene':
                    for gene_id in identifiers:
                        if gene_id in check_data.keys() and gene_id in data.keys() and \
                                check_data[gene_id] == data[gene_id]:
                            return nid
        for nid, data in self.nodes.items():
            if gene_seq_check:
                for k, v in data.items():
                    if self.is_sequence(k, v):
                        nid = self.check_sequence(v)
                        if nid != -1:
                            return nid
            if check_data == data:
                return nid
        return -1

    def is_sequence(self, data_type, data):
        """
        检查字符串是否是基因序列
        :param data_type: 待检查数据属性
        :param data: 待检查字符串
        :return: 若是，返回True，否则返回False
        """
        if data_type not in self.gene_seq and data_type not in self.not_gene_seq:
            if type(data) == str and len(data) >= 5:
                is_seq = True
                for i in data:
                    if i not in ['A', 'T', 'C', 'G', 'U', 'a', 't', 'c', 'g', 'u']:
                        self.not_gene_seq.append(data_type)
                        is_seq = False
                if is_seq:
                    self.gene_seq.append(data_type)
            else:
                self.not_gene_seq.append(data_type)
        return data_type in self.gene_seq

    def check_sequence(self, seq):
        """
        通过基因序列判断是否存在该结点
        :param seq: 待检查基因序列
        :return: 若找到结点，则返回结点ID，否则返回-1
        """
        for nid, data in self.nodes.items():
            for i in self.gene_seq:
                if i in data.keys() and data[i].upper() == seq.upper():
                    return nid
        return -1

    def add_node(self, add_id, add_data: dict = None, method: str = 'id'):
        """
        向有向图中加入结点
        :param add_id: 结点ID
        :param add_data: 结点数据属性
        :param method: 加入时检查结点是否存在的方法，“id”表示按ID检查，“data”表示按数据属性检查
        :return: 返回结点的实际ID（若存在该结点，则返回原结点ID；若不存在该结点，返回用户定义的add_id）
        """
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
        """
        向有向图中加入边
        :param node1_id: 边的起点
        :param node2_id: 边的终点
        :param edge_data: 边的数据属性
        """
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
        """
        读取Karma生成的TTL文件，读取的结点ID为TTL文件中结点的ID
        :param ttl_file: ttl文件路径
        """
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
                        relationship = line[1]
                        self.add_edge(source, target, relationship=relationship)

                    else:
                        # read nodes
                        rdf_id = line[0]
                        if line[2][0] == '<':
                            entity_type = line[2]
                            self.add_node(rdf_id)
                            self.nodes[rdf_id]['_type'] = entity_type
                        else:
                            data_type = line[1]
                            data = line[2][1:-1]
                            self.add_node(rdf_id)
                            self.nodes[rdf_id][data_type] = data
                            if data_type not in self.data_properties:
                                self.data_properties.append(data_type)

    def read_path(self, path_file: str):
        """
        读取多个TTL文件组成的文本文件，每行一个TTL文件的路径
        :param path_file: 文件路径
        """
        with open(path_file, 'r') as path:
            for line in path.readlines():
                line = line.strip()
                if line[0] == '#':
                    continue
                else:
                    self.read_ttl(line)

    def read_owl(self, path: str):
        """
        读取OWL文件
        :param path: OWL文件路径
        """
        xml = parse(path)
        root = xml.documentElement

        for i in root.getElementsByTagName('owl:Class'):
            try:
                accession = i.getAttribute('rdf:about').split('/')[4]
                name = None
                obo_namespace = None

                for child in i.childNodes:
                    if child.nodeName == 'rdfs:label':
                        name = child.firstChild.data
                    elif child.nodeName == 'oboInOwl:hasOBONamespace':
                        obo_namespace = child.firstChild.data
                accession = accession.replace('_', ':')
                self.add_node(accession, {'name': name, 'obo_namespace': obo_namespace})

                subclass_nodes = i.getElementsByTagName('rdfs:subClassOf')
                if subclass_nodes:
                    for node in subclass_nodes:
                        to_accession = node.getAttribute('rdf:resource').split('/')[4]
                        if to_accession:
                            self.add_edge(accession, to_accession, relationship='SubclassOf')
            except IndexError:
                pass

    def merge_ttl(self, ttl):
        """
        合并多个TTL文件对应的网络，结点ID转换为结点编号
        :param ttl: 读取多个TTL文件得到的有向图
        """
        for prop in ttl.data_properties:
            self.data_properties.append(prop)
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

    def relation_to_public_onto(self):
        """
        判断网络是否含有GO、TO等公共本体的信息，是否需要进行实例级标注
        :return: GO、TO等字符串组成的列表
        """
        public_id = {'GO': '', 'TO': ''}
        data_properties = self.data_properties.copy()
        for data in self.nodes.values():
            for k, v in data.items():
                if k in data_properties and v[:2].upper() not in public_id.keys():
                    data_properties.remove(k)

        for data_prop in data_properties:
            cid = 0
            for nid, data in self.nodes.items():
                if data_prop in data.keys():
                    cid = nid
                    break
            public_id[self.nodes[cid][data_prop][:2].upper()] = data_prop
        return public_id

    def annotate_on_instances(self):
        """
        对网络的GO、TO等进行实例级标注
        """
        relation = self.relation_to_public_onto()

        for pid, associated_data in relation.items():
            if associated_data:

                node_id = len(self.nodes)
                mapping = {}  # onto_accession: id_in_graph

                onto = DiGraph()
                onto.read_owl(public_onto[pid])

                for accession, data in onto.nodes.items():
                    self.add_node(node_id, dict(ChainMap({associated_data: accession, '_type': 'PublicOnto'},
                                                         onto.nodes[accession])))
                    mapping[accession] = node_id
                    node_id += 1

                for nid, data in self.nodes.items():
                    if 'PublicOnto' != data['_type'] and associated_data in data.keys():
                        try:
                            self.add_edge(nid, mapping[data[associated_data]], relationship='PublicOntoMapping')
                        except KeyError:
                            pass

    def print_graph(self):
        """
        以易读格式，输出有向图
        """
        print('Nodes:')
        for i, nid in enumerate(self.nodes):
            print('Node {}: {} {}'.format(i, nid, self.nodes[nid]))
        print('Edges:')
        for i, source in enumerate(self.edges):
            print('Edge {}: {} -> {}'.format(i, source, self.edges[source]))

    def output_to_csv(self,
                      node_path: str = 'output\\output_all_csv_node.csv',
                      edge_path: str = 'output\\output_all_csv_edge.csv',
                      contains_data: bool = True):
        """
        输出Gephi可用的可视化文件
        :param node_path: 结点的目标路径
        :param edge_path: 边的目标路径
        :param contains_data: 是否可视化结点的数据属性
        """
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

    def output_to_json(self,
                       path1: str = 'output\\output_all_json.json',
                       path2: str = 'output\\output_all_json.txt'):
        """
        输出JSON格式的网络
        :param path1: JSON文件目标路径
        :param path2: 实体和关系的对应关系文件的目标路径
        """
        entity_type = {}
        relationship_type = {}
        nodes_list = list(self.nodes.items())
        edges_list = list(self.edges.items())

        json = open(path1, 'w')
        json.write("{\"Vertices\":[\n")
        entity_num = 0

        # Print nodes except the last one
        for index, node in nodes_list[:-1]:
            if node['_type'] not in entity_type:
                entity_type[node['_type']] = entity_num
                entity_num = entity_num + 1
            json.write("\t{\"id\":%d,\"entity_type\":%d,\"properties\":\"{" % (index, entity_type[node['_type']]))
            del node['_type']
            node = list(node.items())
            for k, v in node[:-1]:
                json.write("\\\"%r\\\":\\\"%r\\\"," % (k, v))
            if len(node) > 0:
                json.write("\\\"%r\\\":\\\"%r\\\"" % (node[-1][0], node[-1][1]))
            json.write("}\"},\n")

        # Print last node
        index, node = nodes_list[-1]
        if node['_type'] not in entity_type:
            entity_type[node['_type']] = entity_num
        json.write("\t{\"id\":%d,\"entity_type\":%d,\"properties\":\"{" % (index, entity_type[node['_type']]))
        del node['_type']
        node = list(node.items())
        for k, v in node[:-1]:
            json.write("\\\"%r\\\":\\\"%r\\\"," % (k, v))
        if len(node) > 0:
            json.write("\\\"%r\\\":\\\"%r\\\"" % (node[-1][0], node[-1][1]))
        json.write("}\"},\n")

        json.write("]},\n")

        json.write("{\"Edges\":[\n")
        relationship_num = 0

        # Print edges except the last one
        for edge in edges_list[:-1]:
            for target, value in edge[1].items():
                relationship = value['relationship']
                if relationship not in relationship_type:
                    relationship_type[relationship] = relationship_num
                    relationship_num = relationship_num + 1
                json.write("\t{\"source_id\":%r,\"target_id\":%r,\"relationship\":%r},\n" % (
                    edge[0], target, relationship_type[relationship]))

        # Print last edge
        edge = edges_list[-1]
        for target, value in edge[1].items():
            relationship = value['relationship']
            if relationship not in relationship_type:
                relationship_type[relationship] = relationship_num
                relationship_num = relationship_num + 1
            json.write("\t{\"source_id\":%r,\"target_id\":%r,\"relationship\":%r},\n" % (
                edge[0], target, relationship_type[relationship]))

        json.write("]}\n")
        json.close()

        txt = open(path2, 'w')
        for key, value in entity_type.items():
            txt.write("%s\t%s\n" % (key, value))
        txt.write("\n")
        for key, value in relationship_type.items():
            txt.write("%s\t%s\n" % (key, value))
        txt.close()


if __name__ == '__main__':
    properties = Properties(property_path)
    identifiers = properties.read_list("mt2n.identifiersPath")
    public_onto = properties.read_dict("mt2n.publicOntoPath")
    ttl_path = properties.get_property("mt2n.ttlPath")

    o = DiGraph()
    o.read_path(ttl_path)
    g = DiGraph()
    g.merge_ttl(o)

    # g.annotate_on_instances()
    g.output_to_csv()
